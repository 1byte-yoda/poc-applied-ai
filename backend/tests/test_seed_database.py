"""Unit tests for the seed_database function."""

import pytest
import pytest_asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.course import Base, Course
from app.models.module import Module
from app.models.section import Section
from app.models.lecture import Lecture
from app.services.tree_parser import (
    ContentType,
    ParsedNode,
    seed_database,
)


@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory async SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(async_engine):
    """Create a session factory bound to the test engine."""
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return factory


def _make_leaf(name: str, path: str, depth: int, content_type: ContentType) -> ParsedNode:
    """Helper to create a leaf ParsedNode."""
    return ParsedNode(
        name=name,
        path=path,
        depth=depth,
        content_type=content_type,
        children=[],
    )


def _make_dir(name: str, path: str, depth: int, children: list[ParsedNode]) -> ParsedNode:
    """Helper to create a directory ParsedNode."""
    return ParsedNode(
        name=name,
        path=path,
        depth=depth,
        content_type=None,
        children=children,
    )


@pytest.mark.asyncio
async def test_seed_basic_hierarchy(session_factory):
    """Test seeding a standard 3-level hierarchy: module → section → lectures."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Semester I", "Semester I", 1, children=[
            _make_dir("Introduction", "Semester I/Introduction", 2, children=[
                _make_leaf("lesson1.mp4", "Semester I/Introduction/lesson1.mp4", 3, ContentType.VIDEO),
                _make_leaf("notes.pdf", "Semester I/Introduction/notes.pdf", 3, ContentType.PDF),
            ]),
            _make_dir("Advanced", "Semester I/Advanced", 2, children=[
                _make_leaf("deep.ipynb", "Semester I/Advanced/deep.ipynb", 3, ContentType.NOTEBOOK),
            ]),
        ]),
    ])

    await seed_database("Test Course", root, source_file="test.txt", session_factory=session_factory)

    async with session_factory() as session:
        # Verify course
        courses = (await session.execute(select(Course))).scalars().all()
        assert len(courses) == 1
        assert courses[0].title == "Test Course"
        assert courses[0].source_file == "test.txt"

        # Verify module
        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 1
        assert modules[0].title == "Semester I"
        assert modules[0].order_index == 0

        # Verify sections
        sections = (await session.execute(
            select(Section).order_by(Section.order_index)
        )).scalars().all()
        assert len(sections) == 2
        assert sections[0].title == "Introduction"
        assert sections[0].order_index == 0
        assert sections[1].title == "Advanced"
        assert sections[1].order_index == 1

        # Verify lectures
        lectures = (await session.execute(
            select(Lecture).order_by(Lecture.section_id, Lecture.order_index)
        )).scalars().all()
        assert len(lectures) == 3
        assert lectures[0].title == "lesson1.mp4"
        assert lectures[0].content_type == "mp4"
        assert lectures[0].order_index == 0
        assert lectures[1].title == "notes.pdf"
        assert lectures[1].content_type == "pdf"
        assert lectures[1].order_index == 1
        assert lectures[2].title == "deep.ipynb"
        assert lectures[2].content_type == "ipynb"
        assert lectures[2].order_index == 0


@pytest.mark.asyncio
async def test_seed_idempotent(session_factory):
    """Test that seeding the same source_file twice creates only one course."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Module A", "Module A", 1, children=[
            _make_dir("Section 1", "Module A/Section 1", 2, children=[
                _make_leaf("video.mp4", "Module A/Section 1/video.mp4", 3, ContentType.VIDEO),
            ]),
        ]),
    ])

    await seed_database("My Course", root, source_file="same.txt", session_factory=session_factory)
    await seed_database("My Course", root, source_file="same.txt", session_factory=session_factory)

    async with session_factory() as session:
        courses = (await session.execute(select(Course))).scalars().all()
        assert len(courses) == 1


@pytest.mark.asyncio
async def test_seed_top_level_leaf(session_factory):
    """Test seeding when depth-1 node is a leaf file (creates default module/section)."""
    root = _make_dir("root", ".", 0, children=[
        _make_leaf("brochure.pdf", "brochure.pdf", 1, ContentType.PDF),
    ])

    await seed_database("Leaf Course", root, source_file="leaf.txt", session_factory=session_factory)

    async with session_factory() as session:
        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 1
        assert modules[0].title == "Course Materials"
        assert modules[0].order_index == 0

        sections = (await session.execute(select(Section))).scalars().all()
        assert len(sections) == 1
        assert sections[0].title == "General"

        lectures = (await session.execute(select(Lecture))).scalars().all()
        assert len(lectures) == 1
        assert lectures[0].title == "brochure.pdf"
        assert lectures[0].content_type == "pdf"
        assert lectures[0].order_index == 0


@pytest.mark.asyncio
async def test_seed_depth2_leaf(session_factory):
    """Test seeding when depth-2 node is a leaf (creates default section)."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Module X", "Module X", 1, children=[
            _make_leaf("readme.txt", "Module X/readme.txt", 2, ContentType.TXT),
            _make_leaf("guide.pdf", "Module X/guide.pdf", 2, ContentType.PDF),
        ]),
    ])

    await seed_database("D2 Course", root, source_file="d2.txt", session_factory=session_factory)

    async with session_factory() as session:
        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 1
        assert modules[0].title == "Module X"

        sections = (await session.execute(select(Section))).scalars().all()
        assert len(sections) == 1
        assert sections[0].title == "Lectures"

        lectures = (await session.execute(
            select(Lecture).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(lectures) == 2
        assert lectures[0].title == "readme.txt"
        assert lectures[0].order_index == 0
        assert lectures[1].title == "guide.pdf"
        assert lectures[1].order_index == 1


@pytest.mark.asyncio
async def test_seed_flatten_deep_directories(session_factory):
    """Test that non-leaf depth-3+ directories are flattened into the parent section."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Module", "Module", 1, children=[
            _make_dir("Section", "Module/Section", 2, children=[
                _make_dir("SubDir", "Module/Section/SubDir", 3, children=[
                    _make_leaf("deep_video.mp4", "Module/Section/SubDir/deep_video.mp4", 4, ContentType.VIDEO),
                    _make_leaf("deep_doc.docx", "Module/Section/SubDir/deep_doc.docx", 4, ContentType.DOCX),
                ]),
                _make_leaf("top_lecture.pdf", "Module/Section/top_lecture.pdf", 3, ContentType.PDF),
            ]),
        ]),
    ])

    await seed_database("Deep Course", root, source_file="deep.txt", session_factory=session_factory)

    async with session_factory() as session:
        sections = (await session.execute(select(Section))).scalars().all()
        assert len(sections) == 1
        assert sections[0].title == "Section"

        lectures = (await session.execute(
            select(Lecture).order_by(Lecture.order_index)
        )).scalars().all()
        # Flattened: SubDir's 2 children + top_lecture = 3 lectures all in same section
        assert len(lectures) == 3
        assert lectures[0].title == "deep_video.mp4"
        assert lectures[0].order_index == 0
        assert lectures[1].title == "deep_doc.docx"
        assert lectures[1].order_index == 1
        assert lectures[2].title == "top_lecture.pdf"
        assert lectures[2].order_index == 2


@pytest.mark.asyncio
async def test_seed_sequential_order_indexes(session_factory):
    """Test that order_index values are sequential starting from 0 with no gaps."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Mod1", "Mod1", 1, children=[
            _make_dir("Sec A", "Mod1/Sec A", 2, children=[
                _make_leaf("a.mp4", "Mod1/Sec A/a.mp4", 3, ContentType.VIDEO),
            ]),
            _make_dir("Sec B", "Mod1/Sec B", 2, children=[
                _make_leaf("b.pdf", "Mod1/Sec B/b.pdf", 3, ContentType.PDF),
            ]),
        ]),
        _make_dir("Mod2", "Mod2", 1, children=[
            _make_dir("Sec C", "Mod2/Sec C", 2, children=[
                _make_leaf("c.txt", "Mod2/Sec C/c.txt", 3, ContentType.TXT),
            ]),
        ]),
    ])

    await seed_database("Order Course", root, source_file="order.txt", session_factory=session_factory)

    async with session_factory() as session:
        modules = (await session.execute(
            select(Module).order_by(Module.order_index)
        )).scalars().all()
        assert len(modules) == 2
        assert modules[0].order_index == 0
        assert modules[1].order_index == 1

        # Sections within Mod1
        mod1_sections = (await session.execute(
            select(Section).where(Section.module_id == modules[0].id).order_by(Section.order_index)
        )).scalars().all()
        assert len(mod1_sections) == 2
        assert mod1_sections[0].order_index == 0
        assert mod1_sections[1].order_index == 1

        # Sections within Mod2
        mod2_sections = (await session.execute(
            select(Section).where(Section.module_id == modules[1].id).order_by(Section.order_index)
        )).scalars().all()
        assert len(mod2_sections) == 1
        assert mod2_sections[0].order_index == 0


@pytest.mark.asyncio
async def test_seed_empty_root(session_factory):
    """Test seeding an empty root node creates a course with no modules."""
    root = _make_dir("root", ".", 0, children=[])

    await seed_database("Empty Course", root, source_file="empty.txt", session_factory=session_factory)

    async with session_factory() as session:
        courses = (await session.execute(select(Course))).scalars().all()
        assert len(courses) == 1
        assert courses[0].title == "Empty Course"

        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 0


@pytest.mark.asyncio
async def test_seed_source_file_defaults_to_root_path(session_factory):
    """Test that source_file defaults to root_node.path when not provided."""
    root = _make_dir("root", "my_tree.txt", 0, children=[])

    await seed_database("Default Source", root, session_factory=session_factory)

    async with session_factory() as session:
        courses = (await session.execute(select(Course))).scalars().all()
        assert len(courses) == 1
        assert courses[0].source_file == "my_tree.txt"
