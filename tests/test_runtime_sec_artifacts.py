from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading

import pytest

from deployment.runtime_sec_artifacts import RuntimeSecArtifactConfig
from deployment.runtime_sec_artifacts import RuntimeSecArtifactError
from deployment.runtime_sec_artifacts import RuntimeSecArtifactLoader
from api.app import _build_live_presentation_service


def configured_loader(tmp_path, downloader):
    config = RuntimeSecArtifactConfig(
        bucket="private-artifact-bucket",
        prefix="sec-artifacts",
        version="sec-v1",
        local_directory=tmp_path / "artifacts",
    )
    return RuntimeSecArtifactLoader(config=config, downloader=downloader)


def test_disabled_runtime_artifact_mode_preserves_local_composition():
    calls = []

    def downloader(**kwargs):
        calls.append(kwargs)
        raise AssertionError("Disabled artifact mode must not download.")

    loader = RuntimeSecArtifactLoader(
        config=RuntimeSecArtifactConfig(),
        downloader=downloader,
    )

    assert loader.load() is None
    assert calls == []
    assert loader.status() == {
        "artifact_mode_enabled": False,
        "artifact_initialized": False,
        "artifact_version": None,
    }


def test_runtime_artifact_loader_downloads_once_and_caches(tmp_path):
    calls = []
    artifact_directory = tmp_path / "artifact" / "sec-retrieval-artifact"
    artifact_directory.mkdir(parents=True)

    def downloader(**kwargs):
        calls.append(kwargs)
        return artifact_directory

    loader = configured_loader(tmp_path, downloader)

    assert loader.load() == artifact_directory
    assert loader.load() == artifact_directory
    assert calls == [
        {
            "bucket_name": "private-artifact-bucket",
            "artifact_version": "sec-v1",
            "output_directory": tmp_path / "artifacts" / "sec-v1",
            "prefix": "sec-artifacts",
        }
    ]
    assert loader.status() == {
        "artifact_mode_enabled": True,
        "artifact_initialized": True,
        "artifact_version": "sec-v1",
    }


def test_runtime_artifact_loader_serializes_concurrent_initialization(tmp_path):
    calls = []
    started = threading.Event()
    allow_return = threading.Event()
    artifact_directory = tmp_path / "artifact" / "sec-retrieval-artifact"
    artifact_directory.mkdir(parents=True)

    def downloader(**kwargs):
        calls.append(kwargs)
        started.set()
        assert allow_return.wait(timeout=2)
        return artifact_directory

    loader = configured_loader(tmp_path, downloader)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(loader.load)
        assert started.wait(timeout=2)
        second = executor.submit(loader.load)
        allow_return.set()
        assert first.result(timeout=2) == artifact_directory
        assert second.result(timeout=2) == artifact_directory

    assert len(calls) == 1


def test_runtime_artifact_loader_cleans_failed_destination_and_sanitizes_error(tmp_path):
    def downloader(**kwargs):
        output_directory = kwargs["output_directory"]
        output_directory.mkdir(parents=True)
        (output_directory / "partial-download").write_text("partial", encoding="utf-8")
        raise RuntimeError("private bucket path")

    loader = configured_loader(tmp_path, downloader)

    with pytest.raises(RuntimeSecArtifactError, match="unavailable") as error:
        loader.load()

    assert "private bucket" not in str(error.value)
    assert not (tmp_path / "artifacts" / "sec-v1").exists()
    assert loader.status()["artifact_initialized"] is False


@pytest.mark.parametrize(
    ("bucket", "version"),
    [
        ("private-artifact-bucket", None),
        (None, "sec-v1"),
    ],
)
def test_runtime_artifact_loader_rejects_partial_configuration(bucket, version):
    loader = RuntimeSecArtifactLoader(
        config=RuntimeSecArtifactConfig(bucket=bucket, version=version),
    )

    with pytest.raises(RuntimeSecArtifactError, match="requires both"):
        loader.load()


def test_runtime_artifact_loader_reads_optional_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_ARTIFACT_BUCKET", "private-artifact-bucket")
    monkeypatch.setenv("SEC_ARTIFACT_PREFIX", "configured-artifacts")
    monkeypatch.setenv("SEC_ARTIFACT_VERSION", "sec-v7")
    monkeypatch.setenv("SEC_ARTIFACT_LOCAL_DIR", str(tmp_path))

    config = RuntimeSecArtifactConfig.from_environment()

    assert config == RuntimeSecArtifactConfig(
        bucket="private-artifact-bucket",
        prefix="configured-artifacts",
        version="sec-v7",
        local_directory=tmp_path,
    )


def test_live_composition_uses_downloaded_artifact_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    artifact_directory = tmp_path / "sec-retrieval-artifact"
    artifact_directory.mkdir()
    calls = []

    def downloader(**kwargs):
        return artifact_directory

    def agent_factory(**kwargs):
        calls.append(kwargs)
        return StubAgent()

    service = _build_live_presentation_service(
        sec_artifact_loader=configured_loader(tmp_path, downloader),
        agent_factory=agent_factory,
    )

    assert service is not None
    assert calls == [
        {
            "web_search_provider": None,
            "corpus_dir": artifact_directory,
        }
    ]


def test_live_composition_preserves_local_corpus_behavior_when_disabled(monkeypatch):
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "none")
    calls = []

    def agent_factory(**kwargs):
        calls.append(kwargs)
        return StubAgent()

    service = _build_live_presentation_service(
        sec_artifact_loader=RuntimeSecArtifactLoader(
            config=RuntimeSecArtifactConfig(),
        ),
        agent_factory=agent_factory,
    )

    assert service is not None
    assert calls == [
        {
            "web_search_provider": None,
            "corpus_dir": None,
        }
    ]


class StubAgent:
    def run(self, prompt):
        raise AssertionError("The composition test must not run the agent.")
