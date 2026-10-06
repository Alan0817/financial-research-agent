"""Command-line validation for extracted SEC retrieval artifacts."""

import argparse
import json
from pathlib import Path

from .sec_artifacts import validate_sec_artifact_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an extracted SEC retrieval artifact directory."
    )
    parser.add_argument(
        "--artifact-dir",
        required=True,
        help="Extracted SEC artifact directory containing manifest.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = validate_sec_artifact_directory(Path(args.artifact_dir))
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
