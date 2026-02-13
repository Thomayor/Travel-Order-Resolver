"""
Unit tests for data_preparation module.

Tests cover:
- DataPreparator initialization
- Word-level data loading and validation
- Label alignment with subword tokens
- Split preparation (file creation, JSONL format, stats)
- prepare_all with missing files
"""

import json
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def preparator():
    """Create a DataPreparator instance, skipping if deps are missing."""
    pytest.importorskip("transformers")
    pytest.importorskip("datasets")
    from src.nlp.data_preparation import DataPreparator
    return DataPreparator()


@pytest.fixture
def sample_ner_data():
    """Sample word-level NER examples."""
    return [
        {
            "tokens": ["Je", "veux", "aller", "de", "Paris", "à", "Lyon"],
            "labels": ["O", "O", "O", "O", "B-ORIGIN", "O", "B-DEST"],
            "metadata": {"id": "s1"},
        },
        {
            "tokens": ["Billet", "Paris", "Lyon"],
            "labels": ["O", "B-ORIGIN", "B-DEST"],
            "metadata": {"id": "s2"},
        },
        {
            "tokens": ["Je", "voyage"],
            "labels": ["O", "O"],
            "metadata": {"id": "s3"},
        },
    ]


@pytest.fixture
def sample_ner_file(sample_ner_data, tmp_path):
    """Write sample NER data to a temp JSON file."""
    p = tmp_path / "train_ner.json"
    p.write_text(json.dumps(sample_ner_data), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------


class TestDataPreparatorInit:
    def test_tokenizer_loaded(self, preparator):
        assert preparator.tokenizer is not None

    def test_default_max_length(self, preparator):
        from src.nlp.data_preparation import MAX_LENGTH
        assert preparator.max_length == MAX_LENGTH

    def test_custom_max_length(self):
        pytest.importorskip("transformers")
        from src.nlp.data_preparation import DataPreparator
        dp = DataPreparator(max_length=64)
        assert dp.max_length == 64

    def test_import_error_without_transformers(self, monkeypatch):
        import sys
        monkeypatch.setitem(sys.modules, "transformers", None)
        # Re-import to trigger the ImportError path
        import importlib
        import src.nlp.data_preparation as mod
        with pytest.raises(ImportError):
            importlib.reload(mod)
            mod.DataPreparator()


class TestLoadWordLevelData:
    def test_valid_file(self, preparator, sample_ner_file, sample_ner_data):
        data = preparator.load_word_level_data(sample_ner_file)
        assert len(data) == len(sample_ner_data)

    def test_missing_file(self, preparator):
        with pytest.raises(FileNotFoundError):
            preparator.load_word_level_data("nonexistent/path.json")

    def test_length_mismatch_raises(self, preparator, tmp_path):
        bad = [{"tokens": ["A", "B"], "labels": ["O"]}]
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError, match="token count"):
            preparator.load_word_level_data(str(p))

    def test_unknown_label_raises(self, preparator, tmp_path):
        bad = [{"tokens": ["Paris"], "labels": ["B-UNKNOWN"]}]
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError, match="unknown label"):
            preparator.load_word_level_data(str(p))


class TestAlignLabelsWithTokens:
    def test_output_keys(self, preparator):
        result = preparator.align_labels_with_tokens(["Paris"], ["B-ORIGIN"])
        assert "input_ids" in result
        assert "attention_mask" in result
        assert "labels" in result

    def test_equal_lengths(self, preparator):
        result = preparator.align_labels_with_tokens(["Paris", "Lyon"], ["B-ORIGIN", "B-DEST"])
        assert len(result["input_ids"]) == len(result["attention_mask"]) == len(result["labels"])

    def test_special_tokens_get_minus100(self, preparator):
        result = preparator.align_labels_with_tokens(["Paris"], ["B-ORIGIN"])
        # CamemBERT: first token is [CLS] (id 5), last is [SEP] (id 6)
        assert result["labels"][0] == -100
        assert result["labels"][-1] == -100

    def test_first_subword_gets_label(self, preparator):
        from src.nlp.data_preparation import LABEL2ID
        result = preparator.align_labels_with_tokens(["Paris"], ["B-ORIGIN"])
        # Between [CLS] and [SEP] there should be at least one label == LABEL2ID["B-ORIGIN"]
        inner = result["labels"][1:-1]
        assert LABEL2ID["B-ORIGIN"] in inner

    def test_continuation_subword_gets_minus100(self, preparator):
        # A long word likely produces multiple subwords
        result = preparator.align_labels_with_tokens(["anticonstitutionnellement"], ["O"])
        inner = result["labels"][1:-1]
        # If more than one subword, continuations must be -100
        if len(inner) > 1:
            assert -100 in inner

    def test_truncation_respects_max_length(self, preparator):
        from src.nlp.data_preparation import DataPreparator
        dp = DataPreparator(max_length=8)
        long_tokens = ["Paris"] * 20
        long_labels = ["B-ORIGIN"] * 20
        result = dp.align_labels_with_tokens(long_tokens, long_labels)
        assert len(result["input_ids"]) <= 8

    def test_all_o_sentence(self, preparator):
        from src.nlp.data_preparation import LABEL2ID
        result = preparator.align_labels_with_tokens(["Je", "pars"], ["O", "O"])
        inner = [l for l in result["labels"] if l != -100]
        assert all(l == LABEL2ID["O"] for l in inner)


class TestPrepareSplit:
    def test_output_file_created(self, preparator, sample_ner_file, tmp_path):
        out = tmp_path / "out.json"
        preparator.prepare_split(sample_ner_file, str(out), show_progress=False)
        assert out.exists()

    def test_output_is_jsonl(self, preparator, sample_ner_file, tmp_path):
        out = tmp_path / "out.json"
        preparator.prepare_split(sample_ner_file, str(out), show_progress=False)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        # Each line must be valid JSON
        for line in lines:
            obj = json.loads(line)
            assert "input_ids" in obj

    def test_stats_returned(self, preparator, sample_ner_file, tmp_path):
        out = tmp_path / "out.json"
        stats = preparator.prepare_split(sample_ner_file, str(out), show_progress=False)
        assert "num_examples" in stats
        assert "num_truncated" in stats
        assert "avg_subword_len" in stats
        assert "max_subword_len" in stats
        assert stats["num_examples"] == 3

    def test_creates_missing_directory(self, preparator, sample_ner_file, tmp_path):
        out = tmp_path / "new_dir" / "out.json"
        preparator.prepare_split(sample_ner_file, str(out), show_progress=False)
        assert out.exists()

    def test_reloadable_with_datasets(self, preparator, sample_ner_file, tmp_path):
        pytest.importorskip("datasets")
        from datasets import Dataset
        out = tmp_path / "out.json"
        preparator.prepare_split(sample_ner_file, str(out), show_progress=False)
        ds = Dataset.from_json(str(out))
        assert "input_ids" in ds.column_names
        assert "attention_mask" in ds.column_names
        assert "labels" in ds.column_names
        assert len(ds) == 3


class TestPrepareAll:
    def test_skips_missing_split_with_warning(self, preparator, tmp_path):
        # Only create train_ner.json, not val/test
        train_data = [{"tokens": ["Paris"], "labels": ["B-ORIGIN"]}]
        (tmp_path / "train_ner.json").write_text(json.dumps(train_data), encoding="utf-8")

        with pytest.warns(UserWarning):
            results = preparator.prepare_all(data_dir=str(tmp_path), splits=["train", "val"])

        assert "train" in results
        assert "val" not in results

    def test_processes_present_splits(self, preparator, tmp_path):
        data = [{"tokens": ["Paris"], "labels": ["B-ORIGIN"]}]
        for split in ["train", "val"]:
            (tmp_path / f"{split}_ner.json").write_text(json.dumps(data), encoding="utf-8")

        results = preparator.prepare_all(data_dir=str(tmp_path), splits=["train", "val"])
        assert set(results.keys()) == {"train", "val"}
        assert (tmp_path / "train_tokens.json").exists()
        assert (tmp_path / "val_tokens.json").exists()
