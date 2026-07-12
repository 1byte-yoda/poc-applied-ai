"""Unit tests for parse_tree_file function."""

import tempfile
import os

import pytest

from app.services.tree_parser import (
    ParsedNode,
    parse_tree_file,
    detect_content_type,
    ContentType,
)


def _write_tree_file(content: str) -> str:
    """Helper to write tree content to a temp file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestParseTreeFileEmpty:
    """Test parse_tree_file with empty/whitespace-only files."""

    def test_empty_file_returns_root_with_no_children(self):
        path = _write_tree_file("")
        try:
            result = parse_tree_file(path)
            assert result.name == "root"
            assert result.path == "."
            assert result.depth == 0
            assert result.content_type is None
            assert result.children == []
        finally:
            os.unlink(path)

    def test_whitespace_only_file_returns_root_with_no_children(self):
        path = _write_tree_file("   \n\n  \n")
        try:
            result = parse_tree_file(path)
            assert result.name == "root"
            assert result.children == []
        finally:
            os.unlink(path)

    def test_root_dot_only_returns_empty_root(self):
        path = _write_tree_file(".\n")
        try:
            result = parse_tree_file(path)
            assert result.name == "root"
            assert result.children == []
        finally:
            os.unlink(path)


class TestParseTreeFileBasic:
    """Test parse_tree_file with simple tree structures."""

    def test_single_level(self):
        content = """.
├── ./folder1
├── ./file.pdf
└── ./folder2
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert len(result.children) == 3
            assert result.children[0].name == "folder1"
            assert result.children[0].path == "folder1"
            assert result.children[0].depth == 1
            assert result.children[0].content_type is None

            assert result.children[1].name == "file.pdf"
            assert result.children[1].path == "file.pdf"
            assert result.children[1].content_type == ContentType.PDF

            assert result.children[2].name == "folder2"
            assert result.children[2].path == "folder2"
            assert result.children[2].content_type is None
        finally:
            os.unlink(path)

    def test_nested_structure(self):
        content = """.
├── ./Semester - I
│   ├── ./Semester - I/Module 1
│   │   ├── ./Semester - I/Module 1/lecture1.mp4
│   │   └── ./Semester - I/Module 1/notes.pdf
│   └── ./Semester - I/Module 2
│       └── ./Semester - I/Module 2/demo.ipynb
└── ./Semester - II
    └── ./Semester - II/Module 3
        └── ./Semester - II/Module 3/video.mp4
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert len(result.children) == 2

            sem1 = result.children[0]
            assert sem1.name == "Semester - I"
            assert sem1.path == "Semester - I"
            assert sem1.depth == 1
            assert sem1.content_type is None
            assert len(sem1.children) == 2

            mod1 = sem1.children[0]
            assert mod1.name == "Module 1"
            assert mod1.path == "Semester - I/Module 1"
            assert mod1.depth == 2
            assert len(mod1.children) == 2

            lecture1 = mod1.children[0]
            assert lecture1.name == "lecture1.mp4"
            assert lecture1.path == "Semester - I/Module 1/lecture1.mp4"
            assert lecture1.content_type == ContentType.VIDEO
            assert lecture1.children == []

            notes = mod1.children[1]
            assert notes.name == "notes.pdf"
            assert notes.content_type == ContentType.PDF

            mod2 = sem1.children[1]
            assert mod2.name == "Module 2"
            assert len(mod2.children) == 1
            assert mod2.children[0].name == "demo.ipynb"
            assert mod2.children[0].content_type == ContentType.NOTEBOOK

            sem2 = result.children[1]
            assert sem2.name == "Semester - II"
            assert len(sem2.children) == 1
            assert sem2.children[0].children[0].name == "video.mp4"
        finally:
            os.unlink(path)

    def test_preserves_sibling_order(self):
        content = """.
├── ./alpha
├── ./beta
├── ./gamma
└── ./delta
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            names = [c.name for c in result.children]
            assert names == ["alpha", "beta", "gamma", "delta"]
        finally:
            os.unlink(path)


class TestParseTreeFileRealWorld:
    """Test parse_tree_file with patterns from the actual tree files."""

    def test_deeply_nested_with_full_paths(self):
        content = """.
├── ./AppliedAI Books and Running Notes
│   ├── ./AppliedAI Books and Running Notes/Books
│   │   ├── ./AppliedAI Books and Running Notes/Books/1. Python Fundamentals Book - 1 (Draft Copy).pdf
│   │   ├── ./AppliedAI Books and Running Notes/Books/2. eBook-2-Data_Analysis.pdf
│   │   └── ./AppliedAI Books and Running Notes/Books/3. eBook-3-Machine_Learning.pdf
│   └── ./AppliedAI Books and Running Notes/Diploma Notes
│       └── ./AppliedAI Books and Running Notes/Diploma Notes/10.1 - 10.9 Problems.pdf
├── ./Diploma in AI and ML Brochure.pdf
└── ./Semester - I
    └── ./Semester - I/0. Preparatory Topics
        └── ./Semester - I/0. Preparatory Topics/1. How to learn
            └── ./Semester - I/0. Preparatory Topics/1. How to learn/01. Applied Learning.mp4
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert len(result.children) == 3

            # First top-level: directory
            books_root = result.children[0]
            assert books_root.name == "AppliedAI Books and Running Notes"
            assert books_root.content_type is None
            assert len(books_root.children) == 2

            books = books_root.children[0]
            assert books.name == "Books"
            assert len(books.children) == 3
            assert books.children[0].name == "1. Python Fundamentals Book - 1 (Draft Copy).pdf"
            assert books.children[0].content_type == ContentType.PDF

            # Second top-level: file
            brochure = result.children[1]
            assert brochure.name == "Diploma in AI and ML Brochure.pdf"
            assert brochure.content_type == ContentType.PDF
            assert brochure.children == []

            # Third top-level: deeply nested directory
            sem = result.children[2]
            assert sem.name == "Semester - I"
            video = sem.children[0].children[0].children[0]
            assert video.name == "01. Applied Learning.mp4"
            assert video.content_type == ContentType.VIDEO
            assert video.path == "Semester - I/0. Preparatory Topics/1. How to learn/01. Applied Learning.mp4"
        finally:
            os.unlink(path)

    def test_various_content_types(self):
        content = """.
├── ./video.mp4
├── ./document.pdf
├── ./notebook.ipynb
├── ./page.html
├── ./report.docx
├── ./readme.txt
├── ./audio.mp3
├── ./archive.zip
├── ./image.png
└── ./slides.pptx
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            types = [c.content_type for c in result.children]
            assert types == [
                ContentType.VIDEO,
                ContentType.PDF,
                ContentType.NOTEBOOK,
                ContentType.HTML,
                ContentType.DOCX,
                ContentType.TXT,
                ContentType.AUDIO,
                ContentType.ARCHIVE,
                ContentType.IMAGE,
                ContentType.PRESENTATION,
            ]
        finally:
            os.unlink(path)


class TestParseTreeFileEdgeCases:
    """Test parse_tree_file edge cases and error handling."""

    def test_file_not_found_raises(self):
        with pytest.raises(OSError):
            parse_tree_file("/nonexistent/path/to/tree.txt")

    def test_skips_empty_lines_between_entries(self):
        content = """.
├── ./folder1

├── ./folder2

└── ./folder3
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert len(result.children) == 3
        finally:
            os.unlink(path)

    def test_unknown_extension_is_none(self):
        content = """.
└── ./file.xyz
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert result.children[0].content_type is None
        finally:
            os.unlink(path)

    def test_directory_without_extension_is_none(self):
        content = """.
└── ./My Folder Name
"""
        path = _write_tree_file(content)
        try:
            result = parse_tree_file(path)
            assert result.children[0].content_type is None
            assert result.children[0].name == "My Folder Name"
        finally:
            os.unlink(path)
