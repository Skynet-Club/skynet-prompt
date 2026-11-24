"""本地优先、出处可核的提示词补齐工具。"""

__version__ = "0.4.0"

from .catalog import CATS, DISPLAY, PromptCatalog, PromptDataError, default_catalog

__all__ = ["CATS", "DISPLAY", "PromptCatalog", "PromptDataError", "default_catalog", "__version__"]
