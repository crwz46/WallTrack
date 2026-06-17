#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from walltrack.cli import run

if __name__ == "__main__":
    run()
