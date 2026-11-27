"""Portable skill archive: root SKILL.md + complete bilingual entries."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_skill_archive_is_root_level_and_complete(tmp: Path):
    out = tmp / "skynet-prompt.skill"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_skill.py"), "--out", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["count"] == 69

    second = tmp / "skynet-prompt.second.skill"
    proc2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_skill.py"), "--out", str(second)],
        capture_output=True, text=True,
    )
    assert proc2.returncode == 0, proc2.stderr
    assert result["sha256"] == json.loads(proc2.stdout)["sha256"]

    with zipfile.ZipFile(out) as archive:
        names = set(archive.namelist())
        assert "SKILL.md" in names
        assert "README.md" in names
        assert "index.tsv" in names
        assert len([name for name in names if name.startswith("prompts/")]) == 69

        skill = archive.read("SKILL.md").decode()
        assert re.search(r"(?m)^name:\s*skynet-prompt$", skill)
        assert re.search(r"(?m)^description:\s*\S+", skill)

        index = archive.read("index.tsv").decode().splitlines()
        assert index[0].startswith("id\tscene\t")
        assert len(index) == 70

        data = json.loads((ROOT / "data" / "prompts.json").read_text())
        for item in data["items"]:
            body = archive.read(f"prompts/{item['id']}.md").decode()
            zh = re.search(r"<!-- BEGIN ZH -->\n(.*?)\n<!-- END ZH -->", body, re.S)
            en = re.search(r"<!-- BEGIN EN -->\n(.*?)\n<!-- END EN -->", body, re.S)
            assert zh and en, item["id"]
            assert zh.group(1) == item["zh"].rstrip()
            assert en.group(1) == item["en"].rstrip()
