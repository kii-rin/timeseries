"""Optional Kaggle downloader.

Setup once:
  1. Create a Kaggle API token at Account > Create New Token.
  2. Put kaggle.json in ~/.kaggle/kaggle.json.
  3. Run: pip install kaggle

Example:
  python scripts/download_kaggle.py --dataset chirag19/air-passengers --out data/kaggle
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and unzip a Kaggle dataset.")
    parser.add_argument("--dataset", default="chirag19/air-passengers")
    parser.add_argument("--out", default="data/kaggle")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", args.dataset, "-p", str(out), "--unzip"],
        check=True,
    )
    print(f"Downloaded {args.dataset} into {out}")


if __name__ == "__main__":
    main()
