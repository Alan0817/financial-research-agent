"""Lazy, process-local loading of validated SEC artifacts for serving."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import shutil
import threading
from typing import Callable

from .gcs_sec_artifacts import DEFAULT_ARTIFACT_PREFIX
from .gcs_sec_artifacts import download_sec_artifact


DEFAULT_LOCAL_ARTIFACT_DIRECTORY = Path(
    "/tmp/financial-research-agent/sec-artifacts"
)


class RuntimeSecArtifactError(RuntimeError):
    """Raised when a configured runtime SEC artifact cannot be prepared."""


@dataclass(frozen=True)
class RuntimeSecArtifactConfig:
    """Optional server-owned configuration for one immutable SEC artifact."""

    bucket: str | None = None
    prefix: str = DEFAULT_ARTIFACT_PREFIX
    version: str | None = None
    local_directory: Path = DEFAULT_LOCAL_ARTIFACT_DIRECTORY

    @property
    def enabled(self) -> bool:
        """Return whether GCS-backed SEC artifact loading is selected."""
        return bool(self.bucket or self.version)

    @classmethod
    def from_environment(cls) -> "RuntimeSecArtifactConfig":
        """Read optional runtime artifact configuration without contacting GCS."""
        bucket = _optional_environment_value("SEC_ARTIFACT_BUCKET")
        version = _optional_environment_value("SEC_ARTIFACT_VERSION")
        prefix = os.getenv("SEC_ARTIFACT_PREFIX", DEFAULT_ARTIFACT_PREFIX).strip()
        local_directory = Path(
            os.getenv(
                "SEC_ARTIFACT_LOCAL_DIR",
                str(DEFAULT_LOCAL_ARTIFACT_DIRECTORY),
            )
        )
        return cls(
            bucket=bucket,
            prefix=prefix,
            version=version,
            local_directory=local_directory,
        )

    def validate(self) -> None:
        """Reject incomplete configuration only when artifact mode is selected."""
        if not self.enabled:
            return
        if not self.bucket or not self.version:
            raise RuntimeSecArtifactError(
                "SEC artifact mode requires both SEC_ARTIFACT_BUCKET and "
                "SEC_ARTIFACT_VERSION."
            )
        if not self.prefix.strip():
            raise RuntimeSecArtifactError("SEC artifact prefix must be non-empty.")


class RuntimeSecArtifactLoader:
    """Load one configured artifact once per process without eager startup work."""

    def __init__(
        self,
        config: RuntimeSecArtifactConfig | None = None,
        downloader: Callable[..., Path] | None = None,
        logger: logging.Logger | None = None,
    ):
        self._config = config or RuntimeSecArtifactConfig.from_environment()
        self._downloader = downloader or download_sec_artifact
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._artifact_directory: Path | None = None

    @property
    def config(self) -> RuntimeSecArtifactConfig:
        """Return non-secret artifact configuration for internal status checks."""
        return self._config

    def load(self) -> Path | None:
        """Return a validated artifact directory, downloading only when selected."""
        self._config.validate()
        if not self._config.enabled:
            return None
        if self._artifact_directory is not None:
            return self._artifact_directory

        with self._lock:
            if self._artifact_directory is not None:
                return self._artifact_directory

            destination = self._release_directory()
            try:
                self._prepare_destination(destination)
                self._logger.info(
                    "Starting SEC artifact download for configured version %s.",
                    self._config.version,
                )
                artifact_directory = self._downloader(
                    bucket_name=self._config.bucket,
                    artifact_version=self._config.version,
                    output_directory=destination,
                    prefix=self._config.prefix,
                )
                self._artifact_directory = Path(artifact_directory)
                self._logger.info(
                    "SEC artifact validation completed for configured version %s.",
                    self._config.version,
                )
            except Exception as error:
                self._cleanup_failed_destination(destination)
                self._logger.error(
                    "SEC artifact initialization failed for configured version %s: %s.",
                    self._config.version,
                    type(error).__name__,
                )
                raise RuntimeSecArtifactError(
                    "Configured SEC retrieval artifact is unavailable."
                ) from error

        return self._artifact_directory

    def status(self) -> dict[str, bool | str | None]:
        """Return safe, non-path state for an internal readiness response."""
        return {
            "artifact_mode_enabled": self._config.enabled,
            "artifact_initialized": self._artifact_directory is not None,
            "artifact_version": self._config.version if self._config.enabled else None,
        }

    def _release_directory(self) -> Path:
        assert self._config.version is not None
        return self._config.local_directory / self._config.version

    @staticmethod
    def _prepare_destination(destination: Path) -> None:
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _cleanup_failed_destination(destination: Path) -> None:
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)


def _optional_environment_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()
