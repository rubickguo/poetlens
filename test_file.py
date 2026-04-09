
"""Legacy local scratch script removed for the open-source release.

import os

path = r"<example-path>"
print(f"Path: {path}")
print(f"Exists: {os.path.exists(path)}")

dir_p = r"<example-directory>"
print(f"Dir {dir_p} Exists: {os.path.exists(dir_p)}")
if os.path.exists(dir_p):
    print(f"Listing {dir_p}:")
    try:
        print(os.listdir(dir_p))
    except Exception as e:
        print(f"Error listing: {e}")
"""

import os
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python test_file.py <path>")
        return 1

    path = Path(sys.argv[1]).expanduser()
    print(f"Path: {path}")
    print(f"Exists: {path.exists()}")

    dir_path = path if path.is_dir() else path.parent
    print(f"Directory: {dir_path}")
    print(f"Directory exists: {dir_path.exists()}")

    if dir_path.exists():
        print(f"Listing {dir_path}:")
        try:
            print(os.listdir(dir_path))
        except Exception as exc:
            print(f"Error listing: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
