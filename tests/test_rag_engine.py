import pytest
from unittest.mock import patch, mock_open
from tools.rag_engine import chunk_document


# ---- FIXTURES: shared test setup ----

@pytest.fixture
def sample_text():
    """Reusable sample text for multiple tests."""
    return "This is sentence one. This is sentence two. This is sentence three. This is sentence four. This is sentence five."


@pytest.fixture
def long_text():
    """Longer text for overlap and size tests."""
    return "Alpha sentence here. Beta sentence here. Gamma sentence here. Delta sentence here. Epsilon sentence here. Zeta sentence here. Eta sentence here. Theta sentence here."


# ---- TESTS ----

class TestChunkDocument:

    def test_basic_chunking(self, sample_text):
        """Test that text gets split into chunks."""
        with patch('builtins.open', mock_open(read_data=sample_text)):
            chunks = chunk_document('fake_path.txt', chunk_size=50, overlap=10)
        assert len(chunks) > 1, "Text should be split into multiple chunks"

    def test_empty_file(self):
        """Test that empty file returns empty list."""
        with patch('builtins.open', mock_open(read_data='')):
            chunks = chunk_document('fake_path.txt')
        assert chunks == [], "Empty file should return empty list"

    def test_file_not_found(self):
        """Test that missing file returns empty list."""
        chunks = chunk_document('nonexistent_file.txt')
        assert chunks == [], "Missing file should return empty list"

    def test_chunk_size_respected(self, long_text):
        """Test that no chunk exceeds the specified size significantly."""
        with patch('builtins.open', mock_open(read_data=long_text)):
            chunks = chunk_document('fake_path.txt', chunk_size=60, overlap=10)
        for chunk in chunks:
            assert len(chunk) < 120, f"Chunk too large: {len(chunk)} chars"

    def test_overlap_exists(self, long_text):
        """Test that consecutive chunks share overlapping text."""
        with patch('builtins.open', mock_open(read_data=long_text)):
            chunks = chunk_document('fake_path.txt', chunk_size=40, overlap=15)
        if len(chunks) >= 2:
            last_part_of_first = chunks[0][-15:]
            assert last_part_of_first in chunks[1], "Overlap text should appear in next chunk"

    def test_single_sentence(self):
        """Test that single sentence returns one chunk."""
        fake_text = "Just one sentence here."
        with patch('builtins.open', mock_open(read_data=fake_text)):
            chunks = chunk_document('fake_path.txt', chunk_size=500, overlap=50)
        assert len(chunks) == 1, "Single sentence should produce one chunk"


# ---- PARAMETRIZE: test multiple inputs in one test ----

class TestChunkDocumentEdgeCases:

    @pytest.mark.parametrize("chunk_size,expected_min_chunks", [
        (20, 3),
        (50, 2),
        (500, 1),
    ])
    def test_different_chunk_sizes(self, sample_text, chunk_size, expected_min_chunks):
        """Test that smaller chunk sizes produce more chunks."""
        with patch('builtins.open', mock_open(read_data=sample_text)):
            chunks = chunk_document('fake_path.txt', chunk_size=chunk_size, overlap=5)
        assert len(chunks) >= expected_min_chunks, f"chunk_size={chunk_size} should produce at least {expected_min_chunks} chunks"
