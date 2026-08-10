---
status: informative
last_updated: 2026-08-10
superseded_by: PRE-015
---

# Temporary documentation validation

Use only after documentation edits. Do not run these commands for a read-only
status/orientation/report task. Report checks run and not run.

```sh
git diff --check
```

```sh
python3 - <<'PY'
from pathlib import Path
import re

link = re.compile(r"\[[^]]*\]\(([^)]+)\)")
for document in Path(".").rglob("*.md"):
    if ".git" in document.parts:
        continue
    fenced = False
    for line in document.read_text().splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for match in link.finditer(line):
            raw = match.group(1)
            target = raw.split("#", 1)[0].removeprefix("<").removesuffix(">")
            if not target or re.match(r"^(?:https?|mailto):", target):
                continue
            if not (document.parent / target).exists():
                print(f"{document} -> {raw}")
PY
```

No output from either command is a pass. These are temporary entry points and
do not satisfy PRE-015.
