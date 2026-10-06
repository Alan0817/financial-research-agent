import json
from pathlib import Path
import tarfile

import numpy as np
import pytest

from deployment.sec_artifacts import ARTIFACT_ROOT_NAME
from deployment.sec_artifacts import ARTIFACT_SCHEMA_VERSION
from deployment.sec_artifacts import CORE_FILE_PATHS
from deployment.sec_artifacts import INCLUDED_FILE_PATHS
from deployment.sec_artifacts import SecArtifactValidationError
from deployment.sec_artifacts import package_sec_artifacts
from deployment.sec_artifacts import validate_sec_artifact_directory
from documents.storage import CorpusStorage
from documents.types import FinancialDocument
from documents.types import FinancialDocumentChunk
from retrieval.index import build_index


class FakeEmbeddingModel:
    model_name = "test-embedding-v1"

    def embed_documents(self, texts):
        return np.asarray(
            [[float(index + 1), 1.0] for index, _ in enumerate(texts)],
            dtype=np.float64,
        )


def build_corpus(root: Path) -> Path:
    document = FinancialDocument(
        document_id="sec_test_document",
        company="Test Company",
        ticker="TEST",
        cik="0000000001",
        accession_number="0000000001-26-000001",
        primary_document="test-10k.htm",
        document_type="10-K",
        filing_date="2026-02-19",
        period_end="2025-12-31",
        source="SEC EDGAR",
        source_url="https://www.sec.gov/Archives/example/test-10k.htm",
        text="Test filing text about custody risk.",
    )
    chunk = FinancialDocumentChunk(
        chunk_id="chunk_test_document",
        document_id=document.document_id,
        company=document.company,
        ticker=document.ticker,
        cik=document.cik,
        accession_number=document.accession_number,
        document_type=document.document_type,
        filing_date=document.filing_date,
        period_end=document.period_end,
        source=document.source,
        source_url=document.source_url,
        section="PART I ITEM 1A",
        section_title="Risk Factors",
        chunk_index=0,
        text="Bitcoin custody risks could affect the company.",
    )
    storage = CorpusStorage(root)
    storage.write_documents([document])
    storage.write_chunks([chunk])
    build_index([chunk], FakeEmbeddingModel(), root / "semantic_index")
    return root


def extract_archive(archive_path: Path, destination: Path) -> Path:
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(destination, filter="data")
    return destination / ARTIFACT_ROOT_NAME


def test_package_and_validate_sec_artifact(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    archive_path = tmp_path / "output" / "sec-v1.tar.gz"

    package_sec_artifacts(
        corpus_dir,
        archive_path,
        artifact_version="sec-v1",
        created_at="2026-10-06T00:00:00+00:00",
    )
    artifact_dir = extract_archive(archive_path, tmp_path / "extracted")
    manifest = validate_sec_artifact_directory(artifact_dir)

    assert manifest["schema_version"] == ARTIFACT_SCHEMA_VERSION
    assert manifest["artifact_version"] == "sec-v1"
    assert manifest["tickers"] == ["TEST"]
    assert manifest["document_count"] == 1
    assert manifest["chunk_count"] == 1
    assert manifest["included_files"] == list(INCLUDED_FILE_PATHS)
    assert all((artifact_dir / relative_path).is_file() for relative_path in CORE_FILE_PATHS)


def test_packaging_rejects_missing_corpus_file(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    (corpus_dir / "documents.jsonl").unlink()

    with pytest.raises(SecArtifactValidationError, match="documents.jsonl"):
        package_sec_artifacts(corpus_dir, tmp_path / "artifact.tar.gz", "sec-v1")


def test_packaging_rejects_missing_index_file(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    (corpus_dir / "semantic_index" / "vectors.npy").unlink()

    with pytest.raises(SecArtifactValidationError, match="vectors.npy"):
        package_sec_artifacts(corpus_dir, tmp_path / "artifact.tar.gz", "sec-v1")


def test_packaging_rejects_corpus_index_fingerprint_mismatch(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    storage = CorpusStorage(corpus_dir)
    original = storage.load_chunks()[0]
    changed = FinancialDocumentChunk(
        **{**original.to_dict(), "text": "Changed text after index construction."}
    )
    storage.write_chunks([changed])

    with pytest.raises(SecArtifactValidationError, match="incompatible"):
        package_sec_artifacts(corpus_dir, tmp_path / "artifact.tar.gz", "sec-v1")


def test_validation_rejects_unsupported_manifest_schema(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    archive_path = tmp_path / "artifact.tar.gz"
    package_sec_artifacts(corpus_dir, archive_path, "sec-v1")
    artifact_dir = extract_archive(archive_path, tmp_path / "extracted")
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "unsupported"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SecArtifactValidationError, match="schema version"):
        validate_sec_artifact_directory(artifact_dir)


def test_validation_rejects_artifact_file_list_mismatch(tmp_path):
    corpus_dir = build_corpus(tmp_path / "corpus")
    archive_path = tmp_path / "artifact.tar.gz"
    package_sec_artifacts(corpus_dir, archive_path, "sec-v1")
    artifact_dir = extract_archive(archive_path, tmp_path / "extracted")
    (artifact_dir / "unexpected.txt").write_text("not declared", encoding="utf-8")

    with pytest.raises(SecArtifactValidationError, match="outside its declared file list"):
        validate_sec_artifact_directory(artifact_dir)
