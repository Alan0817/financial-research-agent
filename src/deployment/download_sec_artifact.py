"""Command-line download and verification for SEC retrieval artifact releases."""

import argparse
import os
from pathlib import Path

from .gcs_sec_artifacts import DEFAULT_ARTIFACT_PREFIX
from .gcs_sec_artifacts import download_sec_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and validate a SEC retrieval artifact using Application Default Credentials."
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("SEC_ARTIFACT_BUCKET"),
        help="Private GCS bucket. Defaults to SEC_ARTIFACT_BUCKET.",
    )
    parser.add_argument(
        "--prefix",
        default=os.getenv("SEC_ARTIFACT_PREFIX", DEFAULT_ARTIFACT_PREFIX),
        help="GCS artifact prefix. Defaults to SEC_ARTIFACT_PREFIX or sec-artifacts.",
    )
    parser.add_argument(
        "--version",
        default=os.getenv("SEC_ARTIFACT_VERSION"),
        help="Immutable artifact version. Defaults to SEC_ARTIFACT_VERSION.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Empty directory for the archive and extracted validated artifact.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.bucket or not args.version:
        raise SystemExit("--bucket and --version are required.")
    artifact_dir = download_sec_artifact(
        bucket_name=args.bucket,
        artifact_version=args.version,
        output_directory=Path(args.output_dir),
        prefix=args.prefix,
    )
    print(artifact_dir)


if __name__ == "__main__":
    main()
