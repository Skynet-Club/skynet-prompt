"""不依赖 pytest 的测试入口：``python3 tests/run.py``。"""

from __future__ import annotations

import importlib
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

MODULES = ["test_catalog", "test_cli", "test_drawer", "test_admin"]
failed = 0
ran = 0

for name in MODULES:
    module = importlib.import_module(name)
    print(f"-- {name}")
    for test_name in sorted(dir(module)):
        if not test_name.startswith("test_"):
            continue
        fn = getattr(module, test_name)
        ran += 1
        try:
            if inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as tmp:
                    fn(Path(tmp))
            else:
                fn()
            print(f"PASS {test_name}")
        except Exception:
            failed += 1
            print(f"FAIL {test_name}")
            traceback.print_exc()

print(f"\n{ran - failed}/{ran} 通过")
sys.exit(1 if failed else 0)
