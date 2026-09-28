"""Run vsfsck on every generated image and check the reported errors.

A case passes when every expected ERROR line is printed; the clean image
must print no ERROR lines at all.
"""
import pathlib
import subprocess
import sys

from make_images import CASES, main as build_images

ROOT = pathlib.Path(__file__).resolve().parent.parent
BINARY = ROOT / ("vsfsck.exe" if sys.platform == "win32" else "vsfsck")


def run():
    build_images()
    failures = 0
    for name, (_, expected) in CASES.items():
        out = subprocess.run([str(BINARY), str(ROOT / "tests" / "images" / f"{name}.img")],
                             capture_output=True, text=True, check=True).stdout
        errors = [line for line in out.splitlines() if line.startswith("ERROR")]
        missing = [e for e in expected if e not in errors]
        ok = not missing and (expected or not errors)
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failures += 1
            print("   expected:", expected, "\n   got:", errors)
    print(f"{len(CASES) - failures}/{len(CASES)} cases passed")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
