#!/usr/bin/env python3
"""Clone every pinned repository at its pinned commit into ROOT/<owner>/<repo>.

    python3 tools/fetch_upstream.py ROOT
    python3 verify.py --upstream ROOT

Needs git and network access. All pinned repositories were public on 2026-11-17. Existing clones are left alone.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1]).resolve()
    repos = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))["repos"]
    for repo, info in repos.items():
        dest = target / repo
        if (dest / ".git").exists():
            print(f"have  {repo}")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{repo}"
        for cmd in (["git", "init", "-q"], ["git", "remote", "add", "origin", url],
                    ["git", "fetch", "-q", "--depth", "1", "origin", info["commit"]],
                    ["git", "checkout", "-q", "FETCH_HEAD"]):
            subprocess.run(cmd, cwd=dest, check=True)
        print(f"fetch {repo} {info['commit'][:7]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
