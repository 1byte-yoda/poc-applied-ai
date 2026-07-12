"""Property-based tests for content type detection.

**Validates: Requirements 2.2, 2.3**
"""

import string

from hypothesis import given, strategies as st

from app.services.tree_parser import ContentType, detect_content_type

# All recognized extensions mapped to their expected ContentType
KNOWN_EXTENSIONS = {
    ".mp4": ContentType.VIDEO,
    ".pdf": ContentType.PDF,
    ".ipynb": ContentType.NOTEBOOK,
    ".html": ContentType.HTML,
    ".docx": ContentType.DOCX,
    ".txt": ContentType.TXT,
    ".mp3": ContentType.AUDIO,
    ".zip": ContentType.ARCHIVE,
    ".png": ContentType.IMAGE,
    ".pptx": ContentType.PRESENTATION,
}

# Strategy: generate a recognized extension in any case variation
known_ext_strategy = st.sampled_from(list(KNOWN_EXTENSIONS.keys()))

# Strategy: generate case variations of known extensions
case_variation_strategy = known_ext_strategy.flatmap(
    lambda ext: st.sampled_from(
        [ext.lower(), ext.upper(), ext.title(), ext.swapcase()]
    )
)

# Strategy: generate filenames with a known extension in any case
filename_with_known_ext = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=st.text(
        alphabet=st.sampled_from(string.ascii_letters + string.digits + " _-"),
        min_size=1,
        max_size=50,
    ),
    ext=case_variation_strategy,
)

# Strategy: generate unrecognized extensions
unrecognized_ext_strategy = st.text(
    alphabet=st.sampled_from(string.ascii_lowercase),
    min_size=1,
    max_size=10,
).filter(lambda s: f".{s}" not in KNOWN_EXTENSIONS)

# Strategy: filenames with unrecognized extensions
filename_with_unknown_ext = st.builds(
    lambda name, ext: f"{name}.{ext}",
    name=st.text(
        alphabet=st.sampled_from(string.ascii_letters + string.digits + " _-"),
        min_size=1,
        max_size=50,
    ),
    ext=unrecognized_ext_strategy,
)

# Strategy: filenames without any extension (directories)
filename_without_ext = st.text(
    alphabet=st.sampled_from(string.ascii_letters + string.digits + " _-"),
    min_size=1,
    max_size=50,
).filter(lambda s: "." not in s)


class TestProperty5ContentTypeCaseInsensitivity:
    """Property 5: Content Type Case Insensitivity

    For any filename with a recognized extension, detect_content_type()
    SHALL return the same ContentType value regardless of the letter case
    of the extension.

    **Validates: Requirements 2.2**
    """

    @given(filename=filename_with_known_ext)
    def test_case_insensitive_detection(self, filename: str):
        """detect_content_type returns the same value regardless of extension case."""
        result = detect_content_type(filename)
        # Get the lowercase extension to find expected value
        import os

        _, ext = os.path.splitext(filename)
        expected = KNOWN_EXTENSIONS[ext.lower()]
        assert result == expected, (
            f"Expected {expected} for filename {filename!r}, got {result}"
        )

    @given(ext=known_ext_strategy)
    def test_all_case_variations_yield_same_result(self, ext: str):
        """All case variations of a known extension yield the same ContentType."""
        base = "testfile"
        lower_result = detect_content_type(f"{base}{ext.lower()}")
        upper_result = detect_content_type(f"{base}{ext.upper()}")
        title_result = detect_content_type(f"{base}{ext.title()}")
        swap_result = detect_content_type(f"{base}{ext.swapcase()}")

        assert lower_result == upper_result == title_result == swap_result
        assert lower_result is not None


class TestProperty6UnknownExtensionsReturnNull:
    """Property 6: Unknown Extensions Return Null

    For any filename with no extension or an unrecognized extension,
    detect_content_type() SHALL return None.

    **Validates: Requirements 2.3**
    """

    @given(filename=filename_with_unknown_ext)
    def test_unknown_extension_returns_none(self, filename: str):
        """Filenames with unrecognized extensions return None."""
        result = detect_content_type(filename)
        assert result is None, (
            f"Expected None for filename {filename!r} with unknown extension, got {result}"
        )

    @given(filename=filename_without_ext)
    def test_no_extension_returns_none(self, filename: str):
        """Filenames without any extension (directories) return None."""
        result = detect_content_type(filename)
        assert result is None, (
            f"Expected None for filename {filename!r} without extension, got {result}"
        )
