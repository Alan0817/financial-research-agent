"""Portable, validated SEC retrieval artifact packaging helpers."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tarfile
from tempfile import TemporaryDirectory

from documents.storage import CorpusStorage
from documents.storage import validate_corpus
from retrieval.index import corpus_fingerprint
from retrieval.index import load_index


ARTIFACT_SCHEMA_VERSION = "sec-retrieval-artifact-v1"
ARTIFACT_ROOT_NAME = "sec-retrieval-artifact"
MANIFEST_FILENAME = "manifest.json"
SEMANTIC_INDEX_DIRECTORY = "semantic_index"
CORE_FILE_PATHS = (
    "chunks.jsonl",
    "documents.jsonl",
    "semantic_index/metadata.json",
    "semantic_index/vectors.npy",
)
INCLUDED_FILE_PATHS = tuple(sorted((MANIFEST_FILENAME, *CORE_FILE_PATHS)))
RETRIEVAL_BACKEND_COMPATIBILITY = (
    "bm25",
    "dense",
    "hybrid",
    "hybrid_reranked",
)


class SecArtifactValidationError(ValueError):
    """Raised when a SEC retrieval artifact cannot safely be served."""


def package_sec_artifacts(
    corpus_dir: str | Path,
    output_path: str | Path,
    artifact_version: str,
    created_at: str | None = None,
) -> Path:
    """Validate and package a portable SEC retrieval artifact archive."""
    source = Path(corpus_dir)
    manifest = build_manifest(source, artifact_version, created_at=created_at)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as temporary_directory:
        staging_root = Path(temporary_directory) / ARTIFACT_ROOT_NAME
        _copy_core_files(source, staging_root)
        _write_manifest(staging_root / MANIFEST_FILENAME, manifest)
        validate_sec_artifact_directory(staging_root)
        _write_archive(staging_root, destination)

    return destination


def build_manifest(
    corpus_dir: str | Path,
    artifact_version: str,
    created_at: str | None = None,
) -> dict:
    """Create a manifest derived from a validated corpus and semantic index."""
    if not isinstance(artifact_version, str) or not artifact_version.strip():
        raise ValueError("artifact_version must be a non-empty string.")

    root = Path(corpus_dir)
    documents, chunks, index = _load_validated_retrieval_inputs(root)
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_version": artifact_version.strip(),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "tickers": sorted({document.ticker for document in documents}),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "retrieval_backend_compatibility": list(RETRIEVAL_BACKEND_COMPATIBILITY),
        "embedding_model": index.metadata["embedding_model"],
        "corpus_fingerprint": corpus_fingerprint(chunks),
        "semantic_index_fingerprint": semantic_index_fingerprint(root),
        "included_files": list(INCLUDED_FILE_PATHS),
    }


def validate_sec_artifact_directory(artifact_dir: str | Path) -> dict:
    """Validate an extracted SEC artifact directory and return its manifest."""
    root = Path(artifact_dir)
    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise SecArtifactValidationError("SEC artifact manifest.json is missing.")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SecArtifactValidationError("SEC artifact manifest.json is invalid JSON.") from error
    _validate_manifest_shape(manifest)
    _validate_included_files(root, manifest)

    documents, chunks, index = _load_validated_retrieval_inputs(root)
    expected = {
        "tickers": sorted({document.ticker for document in documents}),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "embedding_model": index.metadata["embedding_model"],
        "corpus_fingerprint": corpus_fingerprint(chunks),
        "semantic_index_fingerprint": semantic_index_fingerprint(root),
    }
    for field, value in expected.items():
        if manifest[field] != value:
            raise SecArtifactValidationError(
                "SEC artifact manifest field {!r} does not match its contents.".format(field)
            )
    return manifest


def semantic_index_fingerprint(corpus_dir: str | Path) -> str:
    """Hash the exact persisted semantic-index files included in an artifact."""
    root = Path(corpus_dir)
    digest = sha256()
    for relative_path in ("semantic_index/metadata.json", "semantic_index/vectors.npy"):
        path = root / relative_path
        if not path.exists():
            raise SecArtifactValidationError(
                "SEC artifact requires {}.".format(relative_path)
            )
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as file_handle:
            for block in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def _load_validated_retrieval_inputs(root: Path):
    _validate_core_files(root)
    storage = CorpusStorage(root)
    documents = storage.load_documents()
    chunks = storage.load_chunks()
    errors = validate_corpus(documents, chunks)
    if errors:
        raise SecArtifactValidationError(
            "SEC corpus validation failed: {}".format("; ".join(errors))
        )
    if not documents or not chunks:
        raise SecArtifactValidationError("SEC artifact corpus must contain documents and chunks.")

    try:
        index = load_index(chunks, root / SEMANTIC_INDEX_DIRECTORY)
    except (FileNotFoundError, ValueError) as error:
        raise SecArtifactValidationError(
            "SEC semantic index is incompatible with the corpus: {}".format(error)
        ) from error
    return documents, chunks, index


def _validate_core_files(root: Path) -> None:
    for relative_path in CORE_FILE_PATHS:
        if not (root / relative_path).is_file():
            raise SecArtifactValidationError(
                "SEC artifact requires {}.".format(relative_path)
            )


def _validate_manifest_shape(manifest: object) -> None:
    if not isinstance(manifest, dict):
        raise SecArtifactValidationError("SEC artifact manifest must be an object.")
    required_fields = {
        "schema_version",
        "artifact_version",
        "created_at",
        "tickers",
        "document_count",
        "chunk_count",
        "retrieval_backend_compatibility",
        "embedding_model",
        "corpus_fingerprint",
        "semantic_index_fingerprint",
        "included_files",
    }
    missing = sorted(required_fields.difference(manifest))
    if missing:
        raise SecArtifactValidationError(
            "SEC artifact manifest is missing fields: {}.".format(", ".join(missing))
        )
    if manifest["schema_version"] != ARTIFACT_SCHEMA_VERSION:
        raise SecArtifactValidationError("SEC artifact schema version is unsupported.")
    if not isinstance(manifest["artifact_version"], str) or not manifest["artifact_version"].strip():
        raise SecArtifactValidationError("SEC artifact manifest has an invalid artifact_version.")
    if not isinstance(manifest["created_at"], str) or not manifest["created_at"].strip():
        raise SecArtifactValidationError("SEC artifact manifest has an invalid created_at.")
    if not isinstance(manifest["tickers"], list) or not all(
        isinstance(ticker, str) for ticker in manifest["tickers"]
    ):
        raise SecArtifactValidationError("SEC artifact manifest has invalid tickers.")
    if not isinstance(manifest["document_count"], int) or not isinstance(
        manifest["chunk_count"], int
    ):
        raise SecArtifactValidationError("SEC artifact manifest has invalid counts.")
    if manifest["retrieval_backend_compatibility"] != list(
        RETRIEVAL_BACKEND_COMPATIBILITY
    ):
        raise SecArtifactValidationError(
            "SEC artifact manifest has unsupported retrieval compatibility."
        )
    for field in (
        "embedding_model",
        "corpus_fingerprint",
        "semantic_index_fingerprint",
    ):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise SecArtifactValidationError(
                "SEC artifact manifest has an invalid {!r}.".format(field)
            )
    if manifest["included_files"] != list(INCLUDED_FILE_PATHS):
        raise SecArtifactValidationError("SEC artifact manifest has an invalid file list.")


def _validate_included_files(root: Path, manifest: dict) -> None:
    for relative_path in manifest["included_files"]:
        path = root / relative_path
        if not path.is_file():
            raise SecArtifactValidationError(
                "SEC artifact manifest references a missing file: {}.".format(relative_path)
            )
    actual_files = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )
    if actual_files != manifest["included_files"]:
        raise SecArtifactValidationError(
            "SEC artifact contains files outside its declared file list."
        )


def _copy_core_files(source: Path, destination: Path) -> None:
    for relative_path in CORE_FILE_PATHS:
        source_path = source / relative_path
        destination_path = destination / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination_path)


def _write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_archive(staging_root: Path, destination: Path) -> None:
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with temporary_path.open("wb") as output_file:
            with gzip.GzipFile(fileobj=output_file, mode="wb", mtime=0) as gzip_file:
                with tarfile.open(fileobj=gzip_file, mode="w") as archive:
                    for relative_path in INCLUDED_FILE_PATHS:
                        source_path = staging_root / relative_path
                        archive_name = "{}/{}".format(ARTIFACT_ROOT_NAME, relative_path)
                        info = archive.gettarinfo(str(source_path), arcname=archive_name)
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        info.mtime = 0
                        with source_path.open("rb") as file_handle:
                            archive.addfile(info, file_handle)
        temporary_path.replace(destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
