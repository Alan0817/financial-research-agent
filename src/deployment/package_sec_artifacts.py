"""Command-line packaging for portable SEC retrieval artifacts."""

import argparse
from pathlib import Path

from .sec_artifacts import package_sec_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package a validated SEC retrieval artifact bundle."
    )
    parser.add_argument(
        "--corpus-dir",
        default="data/financial_documents",
        help="Corpus directory containing documents, chunks, and semantic_index.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination .tar.gz path.",
    )
    parser.add_argument(
        "--artifact-version",
        required=True,
        help="Version identifier recorded in the artifact manifest.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = package_sec_artifacts(
        corpus_dir=Path(args.corpus_dir),
        output_path=Path(args.output),
        artifact_version=args.artifact_version,
    )
    print(output_path)


if __name__ == "__main__":
    main()
