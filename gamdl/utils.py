import colorama
import requests


def color_text(text: str, color) -> str:
    """使用指定颜色代码为文本添加颜色。

    该函数通过在文本前后添加ANSI颜色代码来为文本着色，
    并在文本末尾添加重置代码以确保颜色不会影响后续文本。

    Args:
        text (str): 需要着色的文本内容
        color: ANSI颜色代码，如colorama.Fore.RED等

    Returns:
        str: 添加了颜色代码的文本
    """
    return color + text + colorama.Style.RESET_ALL


def raise_response_exception(response: requests.Response):
    """抛出包含HTTP响应错误信息的异常。

    当HTTP请求失败时，使用此函数抛出一个包含状态码和响应文本的异常，
    便于调试和错误处理。

    Args:
        response (requests.Response): 包含HTTP响应信息的requests.Response对象
    """
    raise Exception(
        f"Request failed with status code {response.status_code}: {response.text}"
    )