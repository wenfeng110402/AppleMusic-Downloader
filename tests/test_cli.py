from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from amdl import cli as cli_module


PLAYLIST_URL = (
    "https://music.apple.com/us/playlist/test/"
    "pl.1234567890abcdef1234567890abcdef"
)


class CliRoutingTests(unittest.TestCase):
    def test_gamdl_arguments_are_forwarded_unchanged(self) -> None:
        invocations = [
            [PLAYLIST_URL],
            ["-c", "/tmp/cookies.txt", PLAYLIST_URL],
            ["-c", "/tmp/cookies.txt", "-o", "/tmp/music", PLAYLIST_URL],
        ]

        for args in invocations:
            with self.subTest(args=args):
                with (
                    patch.object(sys, "argv", ["amdl", *args]),
                    patch.object(cli_module, "_passthrough_to_gamdl") as passthrough,
                ):
                    cli_module.main()

                passthrough.assert_called_once_with(args)

    def test_local_commands_are_not_forwarded(self) -> None:
        for command in ("server", "desktop", "--version"):
            with self.subTest(command=command):
                with (
                    patch.object(sys, "argv", ["amdl", command]),
                    patch.object(cli_module, "cli") as local_cli,
                    patch.object(cli_module, "_passthrough_to_gamdl") as passthrough,
                ):
                    cli_module.main()

                local_cli.assert_called_once_with(
                    args=[command], standalone_mode=False
                )
                passthrough.assert_not_called()

    def test_help_is_not_forwarded(self) -> None:
        with (
            patch.object(sys, "argv", ["amdl", "--help"]),
            patch.object(cli_module.click, "echo") as echo,
            patch.object(cli_module, "_passthrough_to_gamdl") as passthrough,
        ):
            cli_module.main()

        echo.assert_called_once_with(cli_module._HELP)
        passthrough.assert_not_called()


if __name__ == "__main__":
    unittest.main()
