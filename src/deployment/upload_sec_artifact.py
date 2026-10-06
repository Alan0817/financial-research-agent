"""Command-line upload for immutable SEC retrieval artifact releases."""

import argparse
import os
from pathlib import Path

from .gcs_sec_artifacts import DEFAULT_ARTIFACT_PREFIX
from .gcs_sec_artifacts import upload_sec_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a validated SEC retrieval artifact using Application Default Credentials."
    )
    parser.add_argument("--archive", required=True, help="Validated .tar.gz artifact archive.")
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
        "--allow-overwrite",
        action="store_true",
        help="Explicitly permit replacing an existing artifact version. Avoid in normal releases.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.bucket or not args.version:
        raise SystemExit("--bucket and --version are required.")
    paths = upload_sec_artifact(
        archive_path=Path(args.archive),
        bucket_name=args.bucket,
        artifact_version=args.version,
        prefix=args.prefix,
        allow_overwrite=args.allow_overwrite,
    )
    if args.allow_overwrite:
        print("Warning: existing artifact objects may have been replaced.")
    print("gs://{}/{}".format(args.bucket, paths.archive))
    print("gs://{}/{}".format(args.bucket, paths.manifest))
    print("gs://{}/{}".format(args.bucket, paths.checksum))


if __name__ == "__main__":
    main()
