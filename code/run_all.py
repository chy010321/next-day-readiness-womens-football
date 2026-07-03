#!/usr/bin/env python3
"""One-command reproduction runner for the final manuscript analysis.

Example (Windows PowerShell):
    python code/run_all.py --data-zip "C:\\path\\to\\subjective.zip"
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "code"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-zip", required=True, type=Path,
                        help="Local path to official SoccerMon subjective.zip.")
    parser.add_argument("--work-dir", type=Path, default=REPO_ROOT / "outputs",
                        help="Directory for generated non-versioned outputs (default: outputs/).")
    parser.add_argument("--bootstrap-resamples", type=int, default=2000,
                        help="Use 2000 to reproduce manuscript inference exactly.")
    parser.add_argument("--skip-verification", action="store_true",
                        help="Skip numerical comparison against bundled expected summary outputs.")
    args = parser.parse_args()

    data_zip = args.data_zip.expanduser().resolve()
    work_dir = args.work_dir.expanduser().resolve()
    phase1_dir = work_dir / "phase1"
    analysis_dir = work_dir / "analysis"

    commands = [
        [sys.executable, str(CODE_DIR / "build_soccermon_nextday_dataset.py"),
         "--zip", str(data_zip), "--output-dir", str(phase1_dir)],
        [sys.executable, str(CODE_DIR / "final_analysis.py"),
         "--input-dir", str(phase1_dir), "--output-dir", str(analysis_dir),
         "--bootstrap-resamples", str(args.bootstrap_resamples)],
    ]
    for command in commands:
        print("Running:", " ".join(command))
        subprocess.run(command, check=True)

    if not args.skip_verification:
        command = [
            sys.executable, str(CODE_DIR / "verify_outputs.py"),
            "--actual-dir", str(analysis_dir),
            "--expected-dir", str(REPO_ROOT / "reproducibility" / "expected_outputs"),
            "--bootstrap-resamples", str(args.bootstrap_resamples),
        ]
        print("Running:", " ".join(command))
        subprocess.run(command, check=True)

    print("\nReproduction completed successfully.")
    print(f"Generated analysis outputs: {analysis_dir}")


if __name__ == "__main__":
    main()
