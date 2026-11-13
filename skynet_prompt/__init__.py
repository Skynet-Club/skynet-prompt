"""提示词补充：核心目录与 ``；；`` 抽屉。"""

from .catalog import CATS, DISPLAY

__version__ = "0.3.0"

__all__ = ["CATS", "DISPLAY", "PromptMenuCompleter", "get_completer", "__version__"]


def __getattr__(name: str):
    """让核心目录不依赖 prompt_toolkit，宿主相关对象按需导入。"""
    if name in {"PromptMenuCompleter", "get_completer"}:
        from . import menu

        return getattr(menu, name)
    raise AttributeError(name)
