"""不依赖 pytest 的跑法（宿主 venv 里没有 pytest）：python3 tests/run.py"""

from __future__ import annotations

import importlib
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    "test_catalog",
    "test_advisor",
    "test_approvals",
    "test_candidates",
    "test_club_posts",
    "test_pack_schema",
    "test_service",
    "test_mcp",
    "test_http",
    "test_export",
    "test_export_commands",
    "test_install",
    "test_agent_install",
    "test_agent_release",
    "test_bootstrap",
    "test_menu",
    "test_drawer",
    "test_evaluations",
    "test_eval_packet",
    "test_evaluation_aggregate",
    "test_evaluation_results",
    "test_fabric_import",
    "test_psup",
    "test_reviews",
    "test_release",
    "test_registry",
    "test_signing",
    "test_verify",
    "test_build",
    "test_codex_picker",
    "test_safety",
    "test_source_snapshots",
    "test_sync",
    "test_team",
    "test_feedback",
    "test_trust",
]

failed = 0
ran = 0
for mod_name in MODULES:
    module = importlib.import_module(mod_name)
    print(f"-- {mod_name}")
    for name in sorted(dir(module)):
        if not name.startswith("test_"):
            continue
        ran += 1
        fn = getattr(module, name)
        try:
            if inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as tmp:
                    fn(Path(tmp))
            else:
                fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()

print(f"\n{ran - failed}/{ran} 通过")
sys.exit(1 if failed else 0)
