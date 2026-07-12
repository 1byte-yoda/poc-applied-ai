"""Property-based tests for tree parsing.

**Validates: Requirements 1.1, 1.2, 1.3**
"""

import os
import tempfile

from hypothesis import given, settings, strategies as st

from app.services.tree_parser import ContentType, ParsedNode, parse_tree_file

# Strategy: generate valid node names (no path separators, no dots at start for simplicity)
node_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 _-"),
    min_size=1,
    max_size=20,
).map(str.strip).filter(lambda s: len(s) > 0)

# Strategy: generate file names with known extensions
file_extension_strategy = st.sampled_from([".mp4", ".pdf", ".ipynb", ".txt", ".docx", ".html"])

file_name_strategy = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=node_name_strategy,
    ext=file_extension_strategy,
)


def _serialize_tree(root: ParsedNode) -> str:
    """Serialize a ParsedNode tree to tree-file format for round-trip testing."""
    lines = [".\n"]

    def _serialize_children(nodes: list[ParsedNode], prefix: str, parent_path: str):
        for i, node in enumerate(nodes):
            is_last = i == len(nodes) - 1
            connector = "└── " if is_last else "├── "
            node_path = f"{parent_path}/{node.name}" if parent_path != "." else f"./{node.name}"
            lines.append(f"{prefix}{connector}{node_path}\n")

            if node.children:
                child_prefix = prefix + ("    " if is_last else "│   ")
                _serialize_children(node.children, child_prefix, node_path[2:] if node_path.startswith("./") else node_path)

    _serialize_children(root.children, "", ".")
    return "".join(lines)


def _count_nodes(node: ParsedNode) -> int:
    """Count total nodes in a tree (excluding root)."""
    count = 0
    for child in node.children:
        count += 1
        count += _count_nodes(child)
    return count


def _count_content_lines(content: str) -> int:
    """Count non-empty lines that are not the root '.' line."""
    count = 0
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped and stripped != ".":
            count += 1
    return count


def _check_hierarchy(node: ParsedNode, expected_depth: int = 0):
    """Verify all children are at the correct depth relative to parent."""
    for child in node.children:
        assert child.depth == expected_depth + 1, (
            f"Child {child.name!r} at depth {child.depth}, expected {expected_depth + 1}"
        )
        _check_hierarchy(child, expected_depth + 1)


def _collect_siblings_order(node: ParsedNode) -> list[list[str]]:
    """Collect sibling name lists at each level for order verification."""
    result = []
    if node.children:
        result.append([c.name for c in node.children])
    for child in node.children:
        result.extend(_collect_siblings_order(child))
    return result


# Strategy: generate a simple flat tree (depth-1 nodes only)
@st.composite
def flat_tree_strategy(draw):
    """Generate a flat tree with 1-5 depth-1 children."""
    num_children = draw(st.integers(min_value=1, max_value=5))
    children = []
    for _ in range(num_children):
        is_file = draw(st.booleans())
        if is_file:
            name = draw(file_name_strategy)
        else:
            name = draw(node_name_strategy)
        children.append(name)
    return children


# Strategy: generate a nested tree (depth-1 and depth-2 nodes)
@st.composite
def nested_tree_strategy(draw):
    """Generate a tree with directories containing files."""
    num_dirs = draw(st.integers(min_value=1, max_value=3))
    tree = []
    for _ in range(num_dirs):
        dir_name = draw(node_name_strategy)
        num_files = draw(st.integers(min_value=1, max_value=4))
        files = [draw(file_name_strategy) for _ in range(num_files)]
        tree.append((dir_name, files))
    return tree


def _build_tree_content_flat(names: list[str]) -> str:
    """Build tree file content from a flat list of names."""
    lines = [".\n"]
    for i, name in enumerate(names):
        connector = "└── " if i == len(names) - 1 else "├── "
        lines.append(f"{connector}./{name}\n")
    return "".join(lines)


def _build_tree_content_nested(tree: list[tuple[str, list[str]]]) -> str:
    """Build tree file content from a nested structure of (dir_name, [files])."""
    lines = [".\n"]
    for i, (dir_name, files) in enumerate(tree):
        is_last_dir = i == len(tree) - 1
        dir_connector = "└── " if is_last_dir else "├── "
        lines.append(f"{dir_connector}./{dir_name}\n")

        child_prefix = "    " if is_last_dir else "│   "
        for j, fname in enumerate(files):
            is_last_file = j == len(files) - 1
            file_connector = "└── " if is_last_file else "├── "
            lines.append(f"{child_prefix}{file_connector}./{dir_name}/{fname}\n")
    return "".join(lines)


class TestProperty1TreeParsingCompleteness:
    """Property 1: Tree Parsing Completeness

    For any valid tree text file, the total number of ParsedNodes in the output
    tree SHALL equal the number of non-empty content lines in the source file.

    **Validates: Requirements 1.1**
    """

    @given(names=flat_tree_strategy())
    @settings(max_examples=50)
    def test_flat_tree_completeness(self, names: list[str]):
        """Every non-empty content line produces exactly one node."""
        content = _build_tree_content_flat(names)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            expected_count = _count_content_lines(content)
            actual_count = _count_nodes(result)
            assert actual_count == expected_count, (
                f"Expected {expected_count} nodes, got {actual_count}\n"
                f"Content:\n{content}"
            )
        finally:
            os.unlink(path)

    @given(tree=nested_tree_strategy())
    @settings(max_examples=50)
    def test_nested_tree_completeness(self, tree: list[tuple[str, list[str]]]):
        """Nested trees also have one node per content line."""
        content = _build_tree_content_nested(tree)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            expected_count = _count_content_lines(content)
            actual_count = _count_nodes(result)
            assert actual_count == expected_count, (
                f"Expected {expected_count} nodes, got {actual_count}\n"
                f"Content:\n{content}"
            )
        finally:
            os.unlink(path)


class TestProperty2HierarchyPreservation:
    """Property 2: Hierarchy Preservation

    For any pair of lines in a tree file where line B is indented beneath line A,
    B's ParsedNode SHALL be a descendant of A's ParsedNode in the output tree.

    **Validates: Requirements 1.2**
    """

    @given(tree=nested_tree_strategy())
    @settings(max_examples=50)
    def test_children_are_at_correct_depth(self, tree: list[tuple[str, list[str]]]):
        """Children in nested trees are at the correct depth level."""
        content = _build_tree_content_nested(tree)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            # All direct children of root should be depth 1
            for child in result.children:
                assert child.depth == 1
                # All grandchildren should be depth 2
                for grandchild in child.children:
                    assert grandchild.depth == 2
        finally:
            os.unlink(path)

    @given(tree=nested_tree_strategy())
    @settings(max_examples=50)
    def test_files_are_nested_under_their_directory(self, tree: list[tuple[str, list[str]]]):
        """Files specified under a directory appear as children of that directory node."""
        content = _build_tree_content_nested(tree)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            # Each directory child should contain the expected number of file children
            for i, (dir_name, files) in enumerate(tree):
                dir_node = result.children[i]
                assert dir_node.name == dir_name
                assert len(dir_node.children) == len(files)
        finally:
            os.unlink(path)


class TestProperty3SiblingOrderPreservation:
    """Property 3: Sibling Order Preservation

    For any set of sibling entries at the same depth in a tree file,
    the parsed children list SHALL maintain the same relative ordering.

    **Validates: Requirements 1.3**
    """

    @given(names=flat_tree_strategy())
    @settings(max_examples=50)
    def test_flat_siblings_preserve_order(self, names: list[str]):
        """Sibling entries at the same depth maintain original file order."""
        content = _build_tree_content_flat(names)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            parsed_names = [c.name for c in result.children]
            assert parsed_names == names, (
                f"Order not preserved: expected {names}, got {parsed_names}"
            )
        finally:
            os.unlink(path)

    @given(tree=nested_tree_strategy())
    @settings(max_examples=50)
    def test_nested_siblings_preserve_order(self, tree: list[tuple[str, list[str]]]):
        """Children within each directory maintain their original order."""
        content = _build_tree_content_nested(tree)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            result = parse_tree_file(path)
            for i, (dir_name, files) in enumerate(tree):
                dir_node = result.children[i]
                parsed_file_names = [c.name for c in dir_node.children]
                assert parsed_file_names == files, (
                    f"Order not preserved in {dir_name}: expected {files}, got {parsed_file_names}"
                )
        finally:
            os.unlink(path)


class TestProperty4TreeParsingRoundTrip:
    """Property 4: Tree Parsing Round Trip

    For any valid ParsedNode tree, serializing it to tree-file format and
    then parsing the result SHALL produce an equivalent tree structure.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @given(tree=nested_tree_strategy())
    @settings(max_examples=30)
    def test_serialize_then_parse_preserves_structure(self, tree: list[tuple[str, list[str]]]):
        """Serializing and re-parsing a tree yields the same structure."""
        # First, build and parse the original
        content = _build_tree_content_nested(tree)
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            original = parse_tree_file(path)
        finally:
            os.unlink(path)

        # Now serialize the parsed tree and re-parse
        serialized = _serialize_tree(original)
        fd2, path2 = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd2, "w", encoding="utf-8") as f:
                f.write(serialized)
            reparsed = parse_tree_file(path2)
        finally:
            os.unlink(path2)

        # Compare structures
        def compare_nodes(a: ParsedNode, b: ParsedNode, path_ctx: str = "root"):
            assert len(a.children) == len(b.children), (
                f"At {path_ctx}: children count mismatch {len(a.children)} vs {len(b.children)}"
            )
            for i, (ca, cb) in enumerate(zip(a.children, b.children)):
                assert ca.name == cb.name, (
                    f"At {path_ctx}[{i}]: name mismatch {ca.name!r} vs {cb.name!r}"
                )
                assert ca.content_type == cb.content_type, (
                    f"At {path_ctx}[{i}]: content_type mismatch"
                )
                compare_nodes(ca, cb, f"{path_ctx}/{ca.name}")

        compare_nodes(original, reparsed)
