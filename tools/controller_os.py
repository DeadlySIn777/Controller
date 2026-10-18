"""Offline Controller OS overlay/profile/preflight CLI; never installs or flashes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controller_os.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
