import json
import time
import colorama
import requests


def color_text(text: str, color) -> str:
    return color + text + colorama.Style.RESET_ALL


def raise_response_exception(response):
    # 构建详细的错误信息
    error_details = {
        "url": response.url,
        "status_code": response.status_code,
        "response_text": response.text,
        "request_headers": dict(response.request.headers),
        "response_headers": dict(response.headers)
    }
    
    # 创建错误消息
    error_message = f"""
=== Apple Music API Response Error ===
URL: {response.url}
Status Code: {response.status_code}
Response Text: {response.text}
Request Headers: {json.dumps(dict(response.request.headers), indent=2, ensure_ascii=False)}
Response Headers: {json.dumps(dict(response.headers), indent=2, ensure_ascii=False)}
Error Type: {type(response.reason).__name__ if response.reason else 'Unknown'}
Error Message: {response.reason if response.reason else 'No reason provided'}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
=====================================
""".strip()
    
    # 抛出带有详细信息的异常
    raise Exception(error_message)