"""Make the slice helpers importable as the modules they import each other as.

`src/slice/` is a directory of flat modules, not a package: `compose.py` does
`import role_packages`, and mkosi's own composition runs them from that
directory. Tests import them the same way rather than through a package path
that only tests would use, because a test that imports the code differently
from the way it runs is testing a second arrangement of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

SLICE = Path(__file__).resolve().parents[1]

if str(SLICE) not in sys.path:
    sys.path.insert(0, str(SLICE))
