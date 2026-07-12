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
        # With _grouped_sort_key, non-numeric names sort alphabetically:
        # "Advanced" < "Introduction"
        sections = (await session.execute(
            select(Section).order_by(Section.order_index)
        )).scalars().all()
        assert len(sections) == 2
        assert sections[0].title == "Advanced"
        assert sections[0].order_index == 0
        assert sections[1].title == "Introduction"
        assert sections[1].order_index == 1

        # Verify lectures
        # Section order changed: Advanced (id=1) comes before Introduction (id=2)
        # due to alphabetical sorting of non-numeric names
        lectures = (await session.execute(
            select(Lecture).order_by(Lecture.section_id, Lecture.order_index)
        )).scalars().all()
        assert len(lectures) == 3
        # First section (Advanced) has 1 lecture
        assert lectures[0].title == "deep.ipynb"
        assert lectures[0].content_type == "ipynb"
        assert lectures[0].order_index == 0
        # Second section (Introduction) has 2 lectures
        assert lectures[1].title == "lesson1.mp4"
        assert lectures[1].content_type == "mp4"
        assert lectures[1].order_index == 0
        assert lectures[2].title == "notes.pdf"
        assert lectures[2].content_type == "pdf"
        assert lectures[2].order_index == 1


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
    """Test seeding when a depth-1 directory directly contains only files.
    
    With dynamic level detection, a directory containing only files is treated
    as a section. When it's the first level (path_parts has 1 element), both
    module_title and section_name will be the directory name.
    """
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
        assert sections[0].title == "Module X"

        # With _grouped_sort_key, non-numeric names sort alphabetically:
        # "guide.pdf" < "readme.txt"
        lectures = (await session.execute(
            select(Lecture).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(lectures) == 2
        assert lectures[0].title == "guide.pdf"
        assert lectures[0].order_index == 0
        assert lectures[1].title == "readme.txt"
        assert lectures[1].order_index == 1


@pytest.mark.asyncio
async def test_seed_flatten_deep_directories(session_factory):
    """Test that a mixed node (files + subdirs) creates a Materials section for loose files
    and recurses into sub-directories as separate sections."""
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
        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 1
        # Module title is the collapsed path above the section level
        assert modules[0].title == "Module > Section"

        sections = (await session.execute(
            select(Section).order_by(Section.order_index)
        )).scalars().all()
        # Mixed node: "Materials" for loose files, "SubDir" for the sub-directory
        assert len(sections) == 2
        assert sections[0].title == "Materials"
        assert sections[0].order_index == 0
        assert sections[1].title == "SubDir"
        assert sections[1].order_index == 1

        # Materials section has the loose file
        materials_lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == sections[0].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(materials_lectures) == 1
        assert materials_lectures[0].title == "top_lecture.pdf"

        # SubDir section has the deep files
        subdir_lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == sections[1].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(subdir_lectures) == 2
        assert subdir_lectures[0].title == "deep_doc.docx"
        assert subdir_lectures[1].title == "deep_video.mp4"


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


@pytest.mark.asyncio
async def test_seed_four_level_hierarchy(session_factory):
    """Test seeding a 4-level hierarchy like applied_diploma_ai_ml.txt:
    Semester I → Course 1 → Section 1 → lectures.
    
    Intermediate levels are collapsed into Module title with ' > ' separator.
    """
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Semester - I", "Semester - I", 1, children=[
            _make_dir("0. Preparatory Topics", "Semester - I/0. Preparatory Topics", 2, children=[
                _make_dir("1. How to learn", "Semester - I/0. Preparatory Topics/1. How to learn", 3, children=[
                    _make_leaf("01. Video.mp4", "Semester - I/0. Preparatory Topics/1. How to learn/01. Video.mp4", 4, ContentType.VIDEO),
                    _make_leaf("notes.pdf", "Semester - I/0. Preparatory Topics/1. How to learn/notes.pdf", 4, ContentType.PDF),
                ]),
                _make_dir("2. Math Basics", "Semester - I/0. Preparatory Topics/2. Math Basics", 3, children=[
                    _make_leaf("01. Intro.mp4", "Semester - I/0. Preparatory Topics/2. Math Basics/01. Intro.mp4", 4, ContentType.VIDEO),
                ]),
            ]),
            _make_dir("1. Course 1 - AI Essentials", "Semester - I/1. Course 1 - AI Essentials", 2, children=[
                _make_dir("1. Python Intro", "Semester - I/1. Course 1 - AI Essentials/1. Python Intro", 3, children=[
                    _make_leaf("01. Lesson.mp4", "Semester - I/1. Course 1 - AI Essentials/1. Python Intro/01. Lesson.mp4", 4, ContentType.VIDEO),
                ]),
            ]),
        ]),
    ])

    await seed_database("Diploma AI ML", root, source_file="diploma.txt", session_factory=session_factory)

    async with session_factory() as session:
        modules = (await session.execute(
            select(Module).order_by(Module.order_index)
        )).scalars().all()
        assert len(modules) == 2
        assert modules[0].title == "Semester - I > 0. Preparatory Topics"
        assert modules[1].title == "Semester - I > 1. Course 1 - AI Essentials"

        # Sections for first module
        mod0_sections = (await session.execute(
            select(Section).where(Section.module_id == modules[0].id).order_by(Section.order_index)
        )).scalars().all()
        assert len(mod0_sections) == 2
        assert mod0_sections[0].title == "1. How to learn"
        assert mod0_sections[1].title == "2. Math Basics"

        # Sections for second module
        mod1_sections = (await session.execute(
            select(Section).where(Section.module_id == modules[1].id).order_by(Section.order_index)
        )).scalars().all()
        assert len(mod1_sections) == 1
        assert mod1_sections[0].title == "1. Python Intro"

        # Lectures in first section
        lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == mod0_sections[0].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(lectures) == 2
        assert lectures[0].title == "01. Video.mp4"
        assert lectures[1].title == "notes.pdf"


@pytest.mark.asyncio
async def test_seed_mixed_files_and_dirs(session_factory):
    """Test seeding when a directory has BOTH files and sub-directories.
    
    Like applied_roots.txt where '3. Foundations of NLP' has .mp4 files
    AND sub-folders. Loose files go into a 'Materials' section.
    """
    root = _make_dir("root", ".", 0, children=[
        _make_dir("3. Course 3", "3. Course 3", 1, children=[
            _make_dir("3. Foundations of NLP", "3. Course 3/3. Foundations of NLP", 2, children=[
                # Loose files at this level
                _make_leaf("01. Using HackerRank.mp4", "3. Course 3/3. Foundations of NLP/01. Using HackerRank.mp4", 3, ContentType.VIDEO),
                _make_leaf("02. Problem-1.mp4", "3. Course 3/3. Foundations of NLP/02. Problem-1.mp4", 3, ContentType.VIDEO),
                # Sub-directories (sections with their own files)
                _make_dir("1. Real world problem", "3. Course 3/3. Foundations of NLP/1. Real world problem", 3, children=[
                    _make_leaf("1. Dataset overview.mp4", "3. Course 3/3. Foundations of NLP/1. Real world problem/1. Dataset overview.mp4", 4, ContentType.VIDEO),
                    _make_leaf("2. Data Cleaning.mp4", "3. Course 3/3. Foundations of NLP/1. Real world problem/2. Data Cleaning.mp4", 4, ContentType.VIDEO),
                ]),
                _make_dir("5. Performance measurement", "3. Course 3/3. Foundations of NLP/5. Performance measurement", 3, children=[
                    _make_leaf("1. Accuracy.mp4", "3. Course 3/3. Foundations of NLP/5. Performance measurement/1. Accuracy.mp4", 4, ContentType.VIDEO),
                ]),
            ]),
        ]),
    ])

    await seed_database("Applied Roots", root, source_file="roots.txt", session_factory=session_factory)

    async with session_factory() as session:
        modules = (await session.execute(select(Module))).scalars().all()
        assert len(modules) == 1
        assert modules[0].title == "3. Course 3 > 3. Foundations of NLP"

        sections = (await session.execute(
            select(Section).where(Section.module_id == modules[0].id).order_by(Section.order_index)
        )).scalars().all()
        # "1. Real world problem", "5. Performance measurement", then "Materials" (no numeric prefix sorts last)
        assert len(sections) == 3
        assert sections[0].title == "1. Real world problem"
        assert sections[1].title == "5. Performance measurement"
        assert sections[2].title == "Materials"

        # Real world problem section
        rwp_lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == sections[0].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(rwp_lectures) == 2
        assert rwp_lectures[0].title == "1. Dataset overview.mp4"
        assert rwp_lectures[1].title == "2. Data Cleaning.mp4"

        # Performance measurement section
        perf_lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == sections[1].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(perf_lectures) == 1
        assert perf_lectures[0].title == "1. Accuracy.mp4"

        # Materials section has the loose .mp4 files
        materials_lectures = (await session.execute(
            select(Lecture).where(Lecture.section_id == sections[2].id).order_by(Lecture.order_index)
        )).scalars().all()
        assert len(materials_lectures) == 2
        assert materials_lectures[0].title == "01. Using HackerRank.mp4"
        assert materials_lectures[1].title == "02. Problem-1.mp4"


@pytest.mark.asyncio
async def test_seed_path_prefix(session_factory):
    """Test that path_prefix is correctly prepended to all lecture file_paths."""
    root = _make_dir("root", ".", 0, children=[
        _make_dir("Module A", "Module A", 1, children=[
            _make_dir("Section 1", "Module A/Section 1", 2, children=[
                _make_leaf("video.mp4", "Module A/Section 1/video.mp4", 3, ContentType.VIDEO),
            ]),
        ]),
    ])

    await seed_database(
        "Prefix Course", root,
        source_file="prefix.txt",
        path_prefix="media/courses/",
        session_factory=session_factory,
    )

    async with session_factory() as session:
        lectures = (await session.execute(select(Lecture))).scalars().all()
        assert len(lectures) == 1
        assert lectures[0].file_path == "media/courses/Module A/Section 1/video.mp4"
