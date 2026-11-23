from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from amdl.server import app, _is_port_available, _find_free_port, run_server
from amdl.task_manager import get_task_manager
from amdl import cli as cli_module


class ServerApiTests(unittest.TestCase):
    def test_health_check(self):
        with TestClient(app) as client:
            res = client.get("/api/health")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("version", data)

    def test_api_info(self):
        with TestClient(app) as client:
            res = client.get("/api/info")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("supported_codecs_song", data)
            self.assertIn("supported_audio_conversion_formats", data)
            self.assertIn("supported_video_conversion_formats", data)
            self.assertIn("flac", data["supported_audio_conversion_formats"])
            self.assertIn("mp3", data["supported_audio_conversion_formats"])
            self.assertIn("mp4", data["supported_video_conversion_formats"])

    def test_settings_get_and_post(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings_file = Path(tmpdir) / "settings.json"
            with patch("amdl.server.SETTINGS_FILE", test_settings_file):
                with TestClient(app) as client:
                    # Initial GET when file doesn't exist
                    res = client.get("/api/settings")
                    self.assertEqual(res.status_code, 200)
                    self.assertEqual(res.json(), {})

                    # POST new settings
                    post_res = client.post("/api/settings", json={"theme": "dark", "output_path": "./music"})
                    self.assertEqual(post_res.status_code, 200)
                    self.assertEqual(post_res.json(), {"status": "ok"})

                    # GET saved settings
                    res = client.get("/api/settings")
                    self.assertEqual(res.status_code, 200)
                    self.assertEqual(res.json().get("theme"), "dark")
                    self.assertEqual(res.json().get("output_path"), "./music")

                    # Merge POST
                    client.post("/api/settings", json={"language": "zh-CN"})
                    res = client.get("/api/settings")
                    self.assertEqual(res.json().get("theme"), "dark")
                    self.assertEqual(res.json().get("language"), "zh-CN")

    def test_check_dependencies(self):
        with TestClient(app) as client:
            res = client.get("/api/dependencies")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("all_ok", data)
            self.assertIn("dependencies", data)
            dep_names = [d["name"] for d in data["dependencies"]]
            self.assertIn("ffmpeg", dep_names)
            self.assertIn("MP4Box", dep_names)
            self.assertIn("N_m3u8DL-RE", dep_names)

    def test_clean_temp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            (temp_path / "dummy.txt").write_text("test")
            (temp_path / "dummy_dir").mkdir()
            with patch("amdl.server.TEMP_DIR", temp_path):
                with TestClient(app) as client:
                    res = client.delete("/api/temp")
                    self.assertEqual(res.status_code, 200)
                    self.assertIn("Cleaned 2 items", res.json()["message"])

    def test_submit_task_and_manage(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
            tf.write(b"cookies")
            tf.flush()
            cookies_file = tf.name

            with TestClient(app) as client:
                # 1. Submit task with valid body
                body = {
                    "urls": ["https://music.apple.com/us/album/test/123"],
                    "cookies_path": cookies_file,
                    "audio_format": "",  # should be converted to None without 422 error
                    "quality_uploaded_video": "BEST",  # alias test
                }
                res = client.post("/api/tasks", json=body)
                self.assertEqual(res.status_code, 200)
                task_id = res.json()["task_id"]

                # 2. Get task
                task_res = client.get(f"/api/tasks/{task_id}")
                self.assertEqual(task_res.status_code, 200)
                self.assertEqual(task_res.json()["id"], task_id)

                # 3. List tasks
                list_res = client.get("/api/tasks")
                self.assertEqual(list_res.status_code, 200)
                self.assertTrue(any(t["id"] == task_id for t in list_res.json()["tasks"]))

                # 4. Cancel / Delete task (it failed immediately due to dummy cookies, so it gets removed)
                del_res = client.delete(f"/api/tasks/{task_id}")
                self.assertEqual(del_res.status_code, 200)

                # 5. Non-existent task returns 404
                del_res_404 = client.delete(f"/api/tasks/{task_id}")
                self.assertEqual(del_res_404.status_code, 404)

                # 6. Clear finished tasks
                clear_res = client.delete("/api/tasks")
                self.assertEqual(clear_res.status_code, 200)

    def test_submit_task_cookies_missing(self):
        with TestClient(app) as client:
            body = {
                "urls": ["https://music.apple.com/us/album/test/123"],
                "cookies_path": "/nonexistent/cookies_12345.txt",
            }
            res = client.post("/api/tasks", json=body)
            self.assertEqual(res.status_code, 422)

    def test_websocket_ping_pong(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
            tf.write(b"cookies")
            tf.flush()
            with TestClient(app) as client:
                body = {
                    "urls": ["https://music.apple.com/us/album/test/123"],
                    "cookies_path": tf.name,
                }
                res = client.post("/api/tasks", json=body)
                task_id = res.json()["task_id"]

                with client.websocket_connect(f"/api/ws/{task_id}") as ws:
                    initial_msg = ws.receive_json()
                    self.assertEqual(initial_msg["type"], "subscribed")

                    # Send ping (with space format)
                    ws.send_text(json.dumps({"type": "ping"}))
                    pong = ws.receive_json()
                    self.assertEqual(pong["type"], "pong")


class PortAndCliTests(unittest.TestCase):
    def test_is_port_available(self):
        port = _find_free_port(8900)
        self.assertTrue(_is_port_available(port))

    def test_run_server_explicit_port(self):
        with patch("uvicorn.run") as mock_uvicorn:
            run_server(host="127.0.0.1", port=9050, explicit_port=True)
            mock_uvicorn.assert_called_once()
            _, kwargs = mock_uvicorn.call_args
            self.assertEqual(kwargs["port"], 9050)
            self.assertEqual(kwargs["host"], "127.0.0.1")

    def test_run_server_reads_env_port(self):
        with patch.dict(os.environ, {"PORT": "9088"}), patch("uvicorn.run") as mock_uvicorn:
            run_server()
            mock_uvicorn.assert_called_once()
            _, kwargs = mock_uvicorn.call_args
            self.assertEqual(kwargs["port"], 9088)

    def test_cli_server_options_flexible(self):
        # Test: amdl --server -p 8888
        with (
            patch.object(cli_module, "cli") as mock_cli,
            patch.object(sys, "argv", ["amdl", "--server", "-p", "8888"]),
        ):
            cli_module.main()
            mock_cli.assert_called_once_with(args=["server", "-p", "8888"], standalone_mode=False)

        # Test: amdl --port 8888 --server
        with (
            patch.object(cli_module, "cli") as mock_cli,
            patch.object(sys, "argv", ["amdl", "--port", "8888", "--server"]),
        ):
            cli_module.main()
            mock_cli.assert_called_once_with(args=["server", "--port", "8888"], standalone_mode=False)


if __name__ == "__main__":
    unittest.main()
