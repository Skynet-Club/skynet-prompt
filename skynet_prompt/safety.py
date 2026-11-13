"""提示词供应链安全扫描。

扫描结果只用于缩小人工审核范围；`passed` 表示未命中已知规则，不表示内容已被人工批准。
"""

from __future__ import annotations

import re

RULE_VERSION = 1
RULES = (
    (
        "prompt.instruction_override",
        "high",
        re.compile(
            r"(ignore|disregard|override).{0,30}(previous|prior|system|developer).{0,20}"
            r"(instruction|prompt)|忽略.{0,12}(之前|系统|开发者).{0,8}(指令|提示词)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "secret.credential_access",
        "high",
        re.compile(
            r"(api[-_ ]?key|access[-_ ]?token|password|passwd|private key|credentials?)"
            r".{0,40}(read|print|reveal|send|upload|post|exfiltrat|获取|读取|打印|发送|上传)"
            r"|(获取|读取|打印|发送|上传).{0,30}(密码|令牌|私钥|凭据|api[-_ ]?key)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "secret.exfiltration",
        "high",
        re.compile(
            r"(exfiltrat|upload|post|send).{0,40}(file|document|secret|credential|token|"
            r"\.ssh|\.env)|(上传|发送|回传|外传).{0,30}(文件|密钥|令牌|凭据|\.ssh|\.env)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "secret.credential_use",
        "medium",
        re.compile(
            r"(username|user name|password|passwd|凭据|密码).{0,40}"
            r"(log\s*in|login|ssh|登录|连接)|"
            r"(log\s*in|login|ssh|登录|连接).{0,40}(username|password|凭据|密码)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "shell.destructive",
        "high",
        re.compile(
            r"\brm\s+-rf\b|\bmkfs(?:\.|\s)|\bdd\s+if=|\bdrop\s+(?:database|table)\b|"
            r"\btruncate\s+(?:table|database)\b|\bshutdown\b",
            re.IGNORECASE,
        ),
    ),
    (
        "shell.remote_execution",
        "high",
        re.compile(
            r"(curl|wget).{0,120}\|\s*(?:ba)?sh\b|\beval\s*\(|"
            r"(下载|获取).{0,40}(执行|运行).{0,20}(脚本|命令)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "network.untrusted_egress",
        "medium",
        re.compile(
            r"(visit|open|fetch|call|request).{0,40}https?://|"
            r"(访问|打开|请求|抓取).{0,30}https?://",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)


def scan_text(text: str) -> dict:
    flags = [
        code
        for code, _severity, pattern in RULES
        if pattern.search(text)
    ]
    severities = {
        code: severity for code, severity, pattern in RULES if pattern.search(text)
    }
    high = any(severity == "high" for severity in severities.values())
    status = "needs-review" if flags else "passed"
    return {
        "status": status,
        "flags": flags,
        "severities": severities,
        "rule_version": RULE_VERSION,
        "automatic_only": True,
        "high_risk": high,
    }


def scan_item(item: dict) -> dict:
    text = "\n".join((
        str((item.get("source") or {}).get("quote", "")),
        str(item.get("en", "")),
        str(item.get("zh", "")),
    ))
    return scan_text(text)


__all__ = ["RULE_VERSION", "RULES", "scan_item", "scan_text"]
