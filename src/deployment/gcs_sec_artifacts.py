"""Versioned Google Cloud Storage distribution for SEC retrieval artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import tarfile
from tempfile import TemporaryDirectory

from .sec_artifacts import ARTIFACT_ROOT_NAME
from .sec_artifacts import MANIFEST_FILENAME
from .sec_artifacts import SecArtifactValidationError
from .sec_artifacts import validate_sec_artifact_directory


DEFAULT_ARTIFACT_PREFIX = "sec-artifacts"
CHECKSUM_FILENAME = "sha256.txt"
ARCHIVE_EXTENSION = ".tar.gz"
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class SecArtifactDistributionError(ValueError):
    """Raised when a SEC artifact release cannot safely be distributed."""


@dataclass(frozen=True)
class SecArtifactObjectPaths:
    """Deterministic private GCS object paths for one immutable release."""

    archive: str
    checksum: str
    manifest: str


def build_object_paths(
    artifact_version: str,
    prefix: str = DEFAULT_ARTIFACT_PREFIX,
) -> SecArtifactObjectPaths:
    """Return deterministic GCS object paths for a validated release version."""
    version = _validate_artifact_version(artifact_version)
    normalized_prefix = _normalize_prefix(prefix)
    release_prefix = "{}/{}".format(normalized_prefix, version)
    return SecArtifactObjectPaths(
        archive="{}/{}{}".format(release_prefix, version, ARCHIVE_EXTENSION),
        checksum="{}/{}".format(release_prefix, CHECKSUM_FILENAME),
        manifest="{}/{}".format(release_prefix, MANIFEST_FILENAME),
    )


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest for a local artifact archive."""
    digest = sha256()
    with Path(path).open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_checksum_text(archive_path: str | Path) -> str:
    """Build a portable checksum file for one archive."""
    path = Path(archive_path)
    return "{}  {}\n".format(sha256_file(path), path.name)


def verify_checksum(
    archive_path: str | Path,
    checksum_text: str,
    expected_filename: str | None = None,
) -> None:
    """Verify a checksum file against an archive without trusting object metadata."""
    if not isinstance(checksum_text, str):
        raise SecArtifactDistributionError("SEC artifact checksum must be text.")

    parts = checksum_text.strip().split()
    if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
        raise SecArtifactDistributionError("SEC artifact checksum file is invalid.")

    expected_name = expected_filename or Path(archive_path).name
    if parts[1] != expected_name:
        raise SecArtifactDistributionError(
            "SEC artifact checksum references an unexpected archive filename."
        )
    if sha256_file(archive_path) != parts[0].lower():
        raise SecArtifactDistributionError("SEC artifact archive checksum does not match.")


def read_archive_manifest(archive_path: str | Path) -> dict:
    """Read the single manifest embedded in a portable SEC artifact archive."""
    expected_member = "{}/{}".format(ARTIFACT_ROOT_NAME, MANIFEST_FILENAME)
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            member = archive.getmember(expected_member)
            file_handle = archive.extractfile(member)
            if file_handle is None:
                raise SecArtifactDistributionError("SEC artifact manifest cannot be read.")
            payload = json.loads(file_handle.read().decode("utf-8"))
    except (KeyError, OSError, tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SecArtifactDistributionError("SEC artifact archive manifest is invalid.") from error

    if not isinstance(payload, dict):
        raise SecArtifactDistributionError("SEC artifact archive manifest must be an object.")
    return payload


def validate_sec_artifact_archive(archive_path: str | Path) -> dict:
    """Safely extract and validate a portable archive using the existing contract."""
    path = Path(archive_path)
    if not path.is_file():
        raise SecArtifactDistributionError("SEC artifact archive is missing.")

    with TemporaryDirectory() as temporary_directory:
        extraction_root = Path(temporary_directory)
        artifact_dir = extract_sec_artifact_archive(path, extraction_root)
        try:
            return validate_sec_artifact_directory(artifact_dir)
        except SecArtifactValidationError as error:
            raise SecArtifactDistributionError(str(error)) from error


def extract_sec_artifact_archive(
    archive_path: str | Path,
    output_directory: str | Path,
) -> Path:
    """Extract an archive only when every member matches the expected root path."""
    destination = Path(output_directory)
    expected_prefix = "{}/".format(ARTIFACT_ROOT_NAME)
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            if not members or any(
                not member.isfile() or not member.name.startswith(expected_prefix)
                for member in members
            ):
                raise SecArtifactDistributionError(
                    "SEC artifact archive contains unsupported members."
                )
            archive.extractall(destination, members=members, filter="data")
    except (OSError, tarfile.TarError) as error:
        raise SecArtifactDistributionError("SEC artifact archive cannot be extracted.") from error
    return destination / ARTIFACT_ROOT_NAME


def upload_sec_artifact(
    archive_path: str | Path,
    bucket_name: str,
    artifact_version: str,
    prefix: str = DEFAULT_ARTIFACT_PREFIX,
    allow_overwrite: bool = False,
    storage_client=None,
) -> SecArtifactObjectPaths:
    """Upload one validated archive as an explicit, normally immutable release."""
    archive = Path(archive_path)
    manifest = validate_sec_artifact_archive(archive)
    _validate_manifest_version(manifest, artifact_version)
    object_paths = build_object_paths(artifact_version, prefix)
    client = storage_client or _create_storage_client()
    bucket = client.bucket(_validate_bucket_name(bucket_name))
    blobs = {
        "archive": bucket.blob(object_paths.archive),
        "checksum": bucket.blob(object_paths.checksum),
        "manifest": bucket.blob(object_paths.manifest),
    }

    existing = [name for name, blob in blobs.items() if _blob_exists(blob, name)]
    if existing and not allow_overwrite:
        raise SecArtifactDistributionError(
            "SEC artifact version {!r} already exists; publish a new version instead."
            .format(artifact_version)
        )

    checksum_text = build_checksum_text(archive)
    manifest_text = _manifest_text(manifest)
    upload_options = {} if allow_overwrite else {"if_generation_match": 0}
    blobs["archive"].upload_from_filename(
        str(archive),
        content_type="application/gzip",
        **upload_options,
    )
    blobs["manifest"].upload_from_string(
        manifest_text,
        content_type="application/json",
        **upload_options,
    )
    # Upload the checksum last so it acts as the completion marker for consumers.
    blobs["checksum"].upload_from_string(
        checksum_text,
        content_type="text/plain",
        **upload_options,
    )
    return object_paths


def download_sec_artifact(
    bucket_name: str,
    artifact_version: str,
    output_directory: str | Path,
    prefix: str = DEFAULT_ARTIFACT_PREFIX,
    storage_client=None,
) -> Path:
    """Download, verify, extract, and validate an explicit SEC artifact release."""
    object_paths = build_object_paths(artifact_version, prefix)
    destination = Path(output_directory)
    if destination.exists() and any(destination.iterdir()):
        raise SecArtifactDistributionError(
            "SEC artifact output directory must be empty: {}.".format(destination)
        )
    destination.mkdir(parents=True, exist_ok=True)

    client = storage_client or _create_storage_client()
    bucket = client.bucket(_validate_bucket_name(bucket_name))
    checksum_text = _download_text(bucket.blob(object_paths.checksum), "checksum")
    external_manifest = _parse_external_manifest(
        _download_text(bucket.blob(object_paths.manifest), "manifest")
    )
    archive_path = destination / "{}{}".format(artifact_version, ARCHIVE_EXTENSION)
    _download_file(bucket.blob(object_paths.archive), archive_path, "archive")
    verify_checksum(archive_path, checksum_text, expected_filename=archive_path.name)

    archive_manifest = validate_sec_artifact_archive(archive_path)
    if archive_manifest != external_manifest:
        raise SecArtifactDistributionError(
            "SEC artifact external manifest does not match the archive manifest."
        )

    artifact_dir = extract_sec_artifact_archive(archive_path, destination)
    try:
        validate_sec_artifact_directory(artifact_dir)
    except SecArtifactValidationError as error:
        raise SecArtifactDistributionError(str(error)) from error
    return artifact_dir


def _create_storage_client():
    try:
        from google.cloud import storage
    except ImportError as error:
        raise RuntimeError(
            "google-cloud-storage is required for SEC artifact upload/download tooling. "
            "Install requirements-deployment.txt."
        ) from error
    return storage.Client()


def _download_text(blob, label: str) -> str:
    _require_blob(blob, label)
    try:
        return blob.download_as_text(encoding="utf-8")
    except Exception as error:
        raise SecArtifactDistributionError(
            "SEC artifact {} could not be downloaded.".format(label)
        ) from error


def _download_file(blob, destination: Path, label: str) -> None:
    _require_blob(blob, label)
    try:
        blob.download_to_filename(str(destination))
    except Exception as error:
        raise SecArtifactDistributionError(
            "SEC artifact {} could not be downloaded.".format(label)
        ) from error


def _require_blob(blob, label: str) -> None:
    if not _blob_exists(blob, label):
        raise SecArtifactDistributionError("SEC artifact {} is missing.".format(label))


def _blob_exists(blob, label: str) -> bool:
    try:
        return blob.exists()
    except Exception as error:
        raise SecArtifactDistributionError(
            "SEC artifact {} availability could not be checked.".format(label)
        ) from error


def _parse_external_manifest(text: str) -> dict:
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as error:
        raise SecArtifactDistributionError("SEC artifact external manifest is invalid.") from error
    if not isinstance(manifest, dict):
        raise SecArtifactDistributionError("SEC artifact external manifest must be an object.")
    return manifest


def _manifest_text(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def _validate_manifest_version(manifest: dict, artifact_version: str) -> None:
    version = _validate_artifact_version(artifact_version)
    if manifest.get("artifact_version") != version:
        raise SecArtifactDistributionError(
            "SEC artifact manifest version does not match the requested release version."
        )


def _validate_artifact_version(artifact_version: str) -> str:
    if not isinstance(artifact_version, str) or not _VERSION_PATTERN.fullmatch(artifact_version):
        raise SecArtifactDistributionError(
            "SEC artifact version must contain only letters, numbers, '.', '_', or '-'."
        )
    return artifact_version


def _normalize_prefix(prefix: str) -> str:
    if not isinstance(prefix, str):
        raise SecArtifactDistributionError("SEC artifact prefix must be a string.")
    normalized = prefix.strip().strip("/")
    parts = normalized.split("/") if normalized else []
    if not parts or any(not part or part in {".", ".."} for part in parts):
        raise SecArtifactDistributionError("SEC artifact prefix is invalid.")
    return "/".join(parts)


def _validate_bucket_name(bucket_name: str) -> str:
    if not isinstance(bucket_name, str) or not bucket_name.strip():
        raise SecArtifactDistributionError("SEC artifact bucket name must be non-empty.")
    return bucket_name.strip()
