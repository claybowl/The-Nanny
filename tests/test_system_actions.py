import pytest
import os
from pathlib import Path
import tempfile
from src.core.system_actions import SystemActionHandler

@pytest.fixture
def handler():
    return SystemActionHandler()

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

class TestSystemActionHandler:
    def test_init(self, handler):
        assert handler.os_type in ["windows", "darwin", "linux"]

    def test_open_application_nonexistent(self, handler):
        result = handler.open_application("nonexistentapp123")
        assert result is False

    def test_search_files(self, handler, temp_dir):
        # Create some test files
        test_files = [
            "test1.txt",
            "test2.doc",
            "other.pdf",
            "test3.pdf"
        ]
        
        for fname in test_files:
            (temp_dir / fname).touch()

        # Search for test files
        results = handler.search_files("test", temp_dir)
        assert len(results) == 3  # Should find test1, test2, and test3
        assert all("test" in str(r) for r in results)

        # Search for pdf files
        results = handler.search_files("pdf", temp_dir)
        assert len(results) == 2  # Should find other.pdf and test3.pdf
        assert all(".pdf" in str(r) for r in results)

    def test_create_note(self, handler, temp_dir):
        # Temporarily override home directory for testing
        original_home = Path.home
        Path.home = lambda: temp_dir

        try:
            content = "This is a test note"
            result = handler.create_note(content)
            
            assert result is not None
            assert result.exists()
            assert result.parent.name == "CLAWD_Notes"
            assert result.read_text() == content
            
        finally:
            # Restore original home directory function
            Path.home = original_home

    def test_create_note_with_filename(self, handler, temp_dir):
        # Temporarily override home directory for testing
        original_home = Path.home
        Path.home = lambda: temp_dir

        try:
            content = "This is a test note"
            filename = "test_note.txt"
            result = handler.create_note(content, filename)
            
            assert result is not None
            assert result.exists()
            assert result.name == filename
            assert result.read_text() == content
            
        finally:
            # Restore original home directory function
            Path.home = original_home 