"""Tree parser service for parsing directory tree files into course hierarchies."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _extract_leading_integer(name: str) -> int | None:
    """Extract the leading integer from a filename, stripping leading zeros.

    Examples:
        "01. Introduction" → 1
        "1.1 Variables" → 1
        "10.2 Item" → 10
        "No number" → None
    """
    match = re.match(r'^0*(\d+)', name)
    return int(match.group(1)) if match else None


def _extract_full_numeric_prefix(name: str) -> list[int]:
    """Extract all dot-separated numeric components from the prefix of a name.

    Examples:
        "01. Introduction" → [1]
        "1.1 Variables" → [1, 1]
        "1.2.3 Deep Topic" → [1, 2, 3]
        "No number" → []
    """
    match = re.match(r'^([\d.]+)', name)
    if not match:
        return []
    prefix = match.group(1).rstrip('.')
    parts = prefix.split('.')
    return [int(p) for p in parts if p]


def _grouped_sort_key(node: "ParsedNode") -> tuple[int, list[int], str]:
    """Generate a sort key that groups items by leading integer.

    Sort priority:
      1. Primary: leading integer group (items share group if same leading int)
      2. Secondary: full numeric prefix as list of ints (element-by-element)
      3. Tertiary: lowercase name as tiebreaker

    Items without a numeric prefix get group = 999999 (sort last).
    """
    leading = _extract_leading_integer(node.name)
    full_prefix = _extract_full_numeric_prefix(node.name)

    if leading is None:
        return (999999, [], node.name.lower())

    return (leading, full_prefix, node.name.lower())


class ContentType(str, Enum):
    """Supported content types for lecture files."""

    VIDEO = "mp4"
    PDF = "pdf"
    NOTEBOOK = "ipynb"
    HTML = "html"
    DOCX = "docx"
    TXT = "txt"
    AUDIO = "mp3"
    ARCHIVE = "zip"
    IMAGE = "png"
    PRESENTATION = "pptx"


# Mapping from lowercase file extensions to ContentType values
_EXTENSION_MAP: dict[str, ContentType] = {
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


def detect_content_type(filename: str) -> ContentType | None:
    """Determine the content type of a file based on its extension.

    Args:
        filename: The filename (or path) to check.

    Returns:
        The matching ContentType enum value, or None for directories
        (no extension) or unrecognized extensions.
    """
    _, ext = os.path.splitext(filename)
    if not ext:
        return None
    return _EXTENSION_MAP.get(ext.lower(), None)


@dataclass
class ParsedNode:
    """Represents a node in the parsed directory tree hierarchy.

    Attributes:
        name: The display name of this node (last path segment).
        path: The full relative path from root.
        depth: The nesting level (0 for root).
        content_type: The detected content type, or None for directories.
        children: Child nodes in original file order.
    """

    name: str
    path: str
    depth: int
    content_type: ContentType | None
    children: list[ParsedNode] = field(default_factory=list)


# Tree-drawing characters used by the `tree` command
_TREE_BRANCH = "├── "
_TREE_LAST = "└── "
_TREE_VERTICAL = "│   "
_TREE_SPACE = "    "


def _calculate_depth(line: str) -> int:
    """Calculate the depth of a tree line by counting 4-character indent units.

    Each level of nesting in the `tree` command output uses exactly 4 characters:
    either "│   ", "├── ", "└── ", or "    " (4 spaces).

    Args:
        line: A single line from the tree output.

    Returns:
        The nesting depth (number of 4-char indent units before the path content).
    """
    depth = 0
    i = 0
    while i + 3 < len(line):
        chunk = line[i : i + 4]
        if chunk in (_TREE_BRANCH, _TREE_LAST, _TREE_VERTICAL, _TREE_SPACE):
            depth += 1
            i += 4
        elif chunk.startswith("│"):
            # Handle edge case where │ is followed by fewer than 3 spaces
            depth += 1
            i += 4
        elif chunk.startswith(("├", "└")):
            # The branch/last marker counts as one depth level
            depth += 1
            i += 4
        else:
            break
    return depth


def _extract_name_from_path(path: str) -> str:
    """Extract the node name (last path segment) from a full relative path.

    Args:
        path: The full relative path (e.g., "./Semester - I/Course 1").

    Returns:
        The last segment of the path (e.g., "Course 1").
    """
    # Remove trailing slash if present
    path = path.rstrip("/")
    # Get the last segment
    return os.path.basename(path)


def _extract_path_from_line(line: str) -> str:
    """Extract the full relative path from a tree output line.

    The path starts after all tree-drawing prefix characters and is the
    remainder of the line. In the actual tree files, this is a full relative
    path like `./AppliedAI Books and Running Notes/Books`.

    Args:
        line: A single line from the tree output.

    Returns:
        The extracted path string.
    """
    i = 0
    while i + 3 < len(line):
        chunk = line[i : i + 4]
        if chunk in (_TREE_BRANCH, _TREE_LAST, _TREE_VERTICAL, _TREE_SPACE):
            i += 4
        elif chunk.startswith(("│", "├", "└")):
            i += 4
        else:
            break

    # Handle case where we consumed exactly up to the content
    # Also handle lines where content starts with a tree char pattern at position i
    # but the 4-char check above didn't match (e.g., only 3 chars left)
    return line[i:].rstrip()


def parse_tree_file(file_path: str) -> ParsedNode:
    """Parse a directory tree text file (output of `tree` command) into
    a hierarchical ParsedNode structure.

    The algorithm uses a stack to track parent-child relationships:
    1. Read all lines from the file
    2. Create root ParsedNode (depth=0, name="root", path=".")
    3. Initialize stack with [(root, -1)]
    4. For each non-empty line:
       - Skip the root directory line (just "." or similar)
       - Calculate depth from tree-drawing characters
       - Extract the path and name
       - Determine content_type via detect_content_type(name)
       - Pop stack until top has depth < current depth
       - Append new node to parent's children
       - Push new node onto stack

    Args:
        file_path: Path to the tree text file to parse.

    Returns:
        Root ParsedNode with depth=0 containing the full hierarchy.
        Returns root with empty children for empty/whitespace-only files.
    """
    root = ParsedNode(name="root", path=".", depth=0, content_type=None, children=[])

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        logger.error("Failed to read tree file %s: %s", file_path, e)
        raise

    # Stack tracks (node, depth) pairs for building parent-child relationships
    # Root is at depth -1 so any depth-0+ node becomes its child
    stack: list[tuple[ParsedNode, int]] = [(root, -1)]

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n\r")

        # Skip empty or whitespace-only lines
        if not line.strip():
            continue

        # Skip the root directory line (typically just ".")
        stripped = line.strip()
        if stripped == ".":
            continue

        # Calculate depth from tree-drawing characters
        depth = _calculate_depth(line)

        # Extract the path content after tree characters
        path = _extract_path_from_line(line)

        if not path:
            logger.warning(
                "Line %d: Could not extract path from line, skipping: %r",
                line_num,
                line,
            )
            continue

        # Extract the name (last segment of the path)
        name = _extract_name_from_path(path)

        if not name:
            logger.warning(
                "Line %d: Could not extract name from path %r, skipping",
                line_num,
                path,
            )
            continue

        # Determine content type from file extension
        content_type = detect_content_type(name)

        # Build the node's path relative to root
        # The tree files already include full relative paths starting with "./"
        # Normalize by removing the leading "./" for cleaner paths
        node_path = path
        if node_path.startswith("./"):
            node_path = node_path[2:]

        node = ParsedNode(
            name=name,
            path=node_path,
            depth=depth,
            content_type=content_type,
            children=[],
        )

        # Pop stack until the top has depth < current depth (finding the parent)
        # INVARIANT: stack[-1] is always the closest ancestor of the current node
        while len(stack) > 1 and stack[-1][1] >= depth:
            stack.pop()

        # The top of stack is now the parent
        parent = stack[-1][0]
        parent.children.append(node)

        # Push current node as potential parent for subsequent deeper nodes
        stack.append((node, depth))

    return root


async def _process_lectures(
    session: AsyncSession,
    section_id: int,
    nodes: list[ParsedNode],
    start_order: int = 0,
    path_prefix: str = "",
) -> int:
    """Recursively flatten nested nodes into Lecture records under a section.

    Leaf nodes (those with content_type) become Lecture records.
    Non-leaf nodes (directories) at depth-3+ are flattened — their children
    are processed recursively within the same parent section.

    Args:
        session: The active async database session.
        section_id: The parent Section ID for these lectures.
        nodes: List of ParsedNode children to process.
        start_order: The starting order_index for this batch.
        path_prefix: Prefix to prepend to file_path (e.g., course folder name).

    Returns:
        The next available order_index after processing all nodes.
    """
    from app.models import Lecture

    order = start_order
    for node in sorted(nodes, key=_grouped_sort_key):
        if node.content_type is not None:
            # Leaf node → create a Lecture
            file_path = f"{path_prefix}{node.path}" if path_prefix else node.path
            lecture = Lecture(
                section_id=section_id,
                title=node.name,
                order_index=order,
                content_type=node.content_type.value,
                file_path=file_path,
                original_filename=node.name,
            )
            session.add(lecture)
            order += 1
        else:
            # Non-leaf directory at depth 3+ → flatten its children
            order = await _process_lectures(
                session, section_id, node.children, order, path_prefix
            )
    return order


async def seed_database(
    course_name: str,
    root_node: ParsedNode,
    source_file: str | None = None,
    path_prefix: str = "",
    session_factory: async_sessionmaker | None = None,
) -> None:
    """Persist a parsed tree structure into database tables.

    Maps the hierarchy as follows:
    - depth-1 directory nodes → Module records
    - depth-2 directory nodes → Section records
    - depth-3+ leaf nodes → Lecture records
    - depth-1 leaf nodes → default Module + Section + Lecture
    - depth-2 leaf nodes → default Section + Lecture
    - depth-3+ non-leaf nodes → flattened into parent Section as lectures

    Idempotent: checks if a Course with the same source_file already exists.
    If it does, seeding is skipped entirely.

    Args:
        course_name: The title for the Course record.
        root_node: The root ParsedNode from parse_tree_file().
        source_file: The source file identifier for idempotency.
            Defaults to root_node.path if not provided.
        path_prefix: Prefix prepended to all lecture file_path values.
            Use this to map tree-relative paths to the media volume structure.
            E.g., "applied_diploma_ai_ml/" so file_path becomes
            "applied_diploma_ai_ml/Semester - I/...".
        session_factory: Optional async session factory for dependency injection.
            Defaults to AsyncSessionLocal from app.db.
    """
    from app.db import AsyncSessionLocal
    from app.models import Course, Lecture, Module, Section

    if session_factory is None:
        session_factory = AsyncSessionLocal

    if source_file is None:
        source_file = root_node.path

    async with session_factory() as session:
        async with session.begin():
            # Idempotency check: skip if course already seeded from this file
            existing = await session.execute(
                select(Course).where(Course.source_file == source_file)
            )
            if existing.scalar_one_or_none() is not None:
                logger.info(
                    "Course already exists for source_file=%r, skipping seeding.",
                    source_file,
                )
                return

            # Create the Course record
            course = Course(
                title=course_name,
                source_file=source_file,
            )
            session.add(course)
            await session.flush()  # Get course.id

            module_order = 0

            for child in sorted(root_node.children, key=_grouped_sort_key):
                if child.content_type is not None:
                    # Top-level leaf (file at depth-1)
                    # Create a default Module + Section to house it
                    module = Module(
                        course_id=course.id,
                        title="Course Materials",
                        order_index=module_order,
                    )
                    session.add(module)
                    await session.flush()

                    section = Section(
                        module_id=module.id,
                        title="General",
                        order_index=0,
                    )
                    session.add(section)
                    await session.flush()

                    lecture = Lecture(
                        section_id=section.id,
                        title=child.name,
                        order_index=0,
                        content_type=child.content_type.value,
                        file_path=f"{path_prefix}{child.path}" if path_prefix else child.path,
                        original_filename=child.name,
                    )
                    session.add(lecture)
                    module_order += 1
                    continue

                # Depth-1 directory node → Module
                module = Module(
                    course_id=course.id,
                    title=child.name,
                    order_index=module_order,
                )
                session.add(module)
                await session.flush()
                module_order += 1

                section_order = 0

                for section_node in sorted(child.children, key=_grouped_sort_key):
                    if section_node.content_type is not None:
                        # Depth-2 leaf (file directly under module)
                        # Create a default Section to house it
                        # Check if we already created a default section for this module
                        existing_default = await session.execute(
                            select(Section).where(
                                Section.module_id == module.id,
                                Section.title == "Lectures",
                            )
                        )
                        default_section = existing_default.scalar_one_or_none()
                        if default_section is None:
                            default_section = Section(
                                module_id=module.id,
                                title="Lectures",
                                order_index=section_order,
                            )
                            session.add(default_section)
                            await session.flush()
                            section_order += 1

                        # Count existing lectures in default section for order
                        existing_lectures = await session.execute(
                            select(Lecture).where(
                                Lecture.section_id == default_section.id
                            )
                        )
                        lecture_count = len(existing_lectures.scalars().all())

                        lecture = Lecture(
                            section_id=default_section.id,
                            title=section_node.name,
                            order_index=lecture_count,
                            content_type=section_node.content_type.value,
                            file_path=f"{path_prefix}{section_node.path}" if path_prefix else section_node.path,
                            original_filename=section_node.name,
                        )
                        session.add(lecture)
                        continue

                    # Depth-2 directory node → could be a direct section with lectures,
                    # or a container with depth-3 sub-folders (like "Course 1" containing chapters)
                    
                    # Check if this node's children are mostly directories (sub-sections)
                    child_dirs = [c for c in section_node.children if c.content_type is None]
                    child_files = [c for c in section_node.children if c.content_type is not None]
                    
                    if child_dirs:
                        # This depth-2 node has sub-folders → each sub-folder becomes a Section
                        # First, handle any direct file children under this depth-2 node
                        if child_files:
                            section = Section(
                                module_id=module.id,
                                title=section_node.name,
                                order_index=section_order,
                            )
                            session.add(section)
                            await session.flush()
                            section_order += 1
                            
                            file_order = 0
                            for f in sorted(child_files, key=_grouped_sort_key):
                                fp = f"{path_prefix}{f.path}" if path_prefix else f.path
                                lecture = Lecture(
                                    section_id=section.id,
                                    title=f.name,
                                    order_index=file_order,
                                    content_type=f.content_type.value,
                                    file_path=fp,
                                    original_filename=f.name,
                                )
                                session.add(lecture)
                                file_order += 1
                        
                        # Each sub-folder becomes its own Section
                        for sub_dir in sorted(child_dirs, key=_grouped_sort_key):
                            section = Section(
                                module_id=module.id,
                                title=sub_dir.name,
                                order_index=section_order,
                            )
                            session.add(section)
                            await session.flush()
                            section_order += 1
                            
                            await _process_lectures(
                                session, section.id, sub_dir.children, start_order=0,
                                path_prefix=path_prefix,
                            )
                    else:
                        # All children are files → this is a simple section
                        section = Section(
                            module_id=module.id,
                            title=section_node.name,
                            order_index=section_order,
                        )
                        session.add(section)
                        await session.flush()
                        section_order += 1

                        await _process_lectures(
                            session, section.id, section_node.children, start_order=0,
                            path_prefix=path_prefix,
                        )

        # conn = await session.connection()
        # await conn.execute(text("UPDATE lectures SET file_path = REPLACE(file_path, 'applied_roots/', 'applied_roots/3. Course 3 - Machine Learning [7 Credits]/' ) WHERE file_path LIKE 'applied_roots/%';"))
        # await conn.commit()

    logger.info(
        "Successfully seeded course %r from source_file=%r.",
        course_name,
        source_file,
    )
