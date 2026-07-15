from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "https://physionet.org/files/bidmc/1.0.0/bidmc_csv"
FILES = ["Signals.csv", "Numerics.csv", "Breaths.csv", "Fix.txt"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def download(url: str, out: Path) -> None:
    headers = {
        "User-Agent": "Mozilla/5.0 coursework downloader",
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as response:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as f:
            while True:
                chunk = response.read(1024 * 512)
                if not chunk:
                    break
                f.write(chunk)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download selected BIDMC CSV records from PhysioNet.")
    parser.add_argument("--records", nargs="+", default=["01", "02", "03"], help="Record numbers, e.g. 01 02 03.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = project_root() / "data" / "raw"
    failed: list[str] = []

    for rec in args.records:
        for suffix in FILES:
            filename = f"bidmc_{rec}_{suffix}"
            url = f"{BASE_URL}/{filename}?download="
            out = raw_dir / filename
            if out.exists() and out.stat().st_size > 0:
                print(f"Skip existing {out}")
                continue
            print(f"Downloading {filename} ...")
            try:
                download(url, out)
                print(f"Saved {out} ({out.stat().st_size} bytes)")
                time.sleep(0.5)
            except urllib.error.HTTPError as exc:
                failed.append(f"{filename}: HTTP {exc.code} {exc.reason}")
            except Exception as exc:
                failed.append(f"{filename}: {type(exc).__name__}: {exc}")

    if failed:
        print("\nSome files could not be downloaded automatically:")
        for item in failed:
            print(f"- {item}")
        print("\nManual fallback:")
        print("1. Open https://physionet.org/content/bidmc/1.0.0/bidmc_csv/")
        print("2. Download the needed bidmc_##_Signals.csv files.")
        print("3. Place them in data/raw/, then run: python code/main.py --record 01")
        return 1

    print("All requested BIDMC files downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
