"""Agent release bundle 的可重复性和校验清单。"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

from scripts.build_agent_release import build
from skynet_prompt.signing import SignatureError, verify_manifest_signature

ROOT = Path(__file__).resolve().parent.parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_bundle_is_reproducible_and_checksummed(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    report = build(tag="v0.3.0", out=first)
    build(tag="v0.3.0", out=second)

    archive = first / "skynet-prompt-v0.3.0.tar.gz"
    assert archive.exists()
    assert archive.read_bytes() == (second / archive.name).read_bytes()
    assert report["entries"] > 100

    manifest = json.loads((first / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"]["type"] == "release-archive"
    assert manifest["source"]["tag"] == "v0.3.0"
    assert manifest["source"]["sha256"] == digest(archive)
    assert manifest["contract"]["sha256"] == digest(first / "AGENT_INSTALL.md")

    sums = {}
    for line in (first / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        sha, name = line.split("  ", 1)
        sums[name] = sha
    assert sums[archive.name] == digest(archive)
    assert sums["install-manifest.json"] == digest(first / "install-manifest.json")
    assert sums["AGENT_INSTALL.md"] == digest(first / "AGENT_INSTALL.md")

    with tarfile.open(archive, "r:gz") as bundle:
        names = bundle.getnames()
    assert "skynet-prompt-v0.3.0/AGENT_INSTALL.md" in names
    assert "skynet-prompt-v0.3.0/scripts/agent_install.py" in names
    assert not any(name.startswith("skynet-prompt-v0.3.0/.git/") for name in names)


def test_release_bundle_excludes_untracked_browser_script(tmp_path: Path):
    build(tag="v0.3.0", out=tmp_path)
    with tarfile.open(tmp_path / "skynet-prompt-v0.3.0.tar.gz", "r:gz") as bundle:
        names = bundle.getnames()
    assert not any(name.endswith("/scripts/dsh_web_acceptance.mjs") for name in names)


def test_signed_release_manifest_verifies_and_detects_tampering(tmp_path: Path):
    key = tmp_path / "ed25519.pem"
    generated = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert generated.returncode == 0, generated.stderr
    report = build(
        tag="v0.3.0",
        out=tmp_path,
        private_key=key,
        key_id="test-release",
    )
    assert report["signed"] is True
    assert report["key_id"] == "test-release"
    manifest = json.loads((tmp_path / "install-manifest.json").read_text(encoding="utf-8"))
    assert verify_manifest_signature(manifest)["key_id"] == "test-release"

    manifest["version"] = "9.9.9"
    try:
        verify_manifest_signature(manifest)
    except SignatureError:
        pass
    else:
        raise AssertionError("篡改安装 manifest 应导致签名验证失败")
