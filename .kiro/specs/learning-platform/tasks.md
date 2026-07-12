# Implementation Plan: Learning Platform

## Overview

Build a fullstack learning platform with a FastAPI (Python 3.11, uv) backend, React (TypeScript, Vite, TailwindCSS) frontend, PostgreSQL database, and Docker Compose orchestration. The platform parses directory tree files into course hierarchies, serves multi-format content (mp4, pdf, docx, txt, ipynb→Colab), and includes a Colab integration service for notebook upload/mapping.

## Tasks

- [x] 1. Set up project structure, configuration, and database foundation
  - [x] 1.1 Create project directory structure and configuration files
    - Create `backend/pyproject.toml` with all dependencies (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, python-docx, pydantic-settings, google-api-python-client, google-auth, python-multipart)
    - Create `backend/app/__init__.py`, `backend/app/config.py` with Pydantic Settings reading from `.env`
    - Create `.env.example` with POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DATABASE_URL, MEDIA_ROOT, FRONTEND_URL
    - Create `.gitignore` excluding `.env`, `__pycache__`, `node_modules`, `pgdata`
    - _Requirements: 11.4_

  - [x] 1.2 Create SQLAlchemy models and database connection
    - Create `backend/app/db.py` with async engine, session factory, connection pool (10-20 connections), and retry logic (3 attempts, exponential backoff)
    - Create `backend/app/models/course.py`, `module.py`, `section.py`, `lecture.py`, `colab_mapping.py` with SQLAlchemy ORM models matching the ERD
    - Enforce cascading deletes, uniqueness constraints (course_id+order_index for modules, module_id+order_index for sections, section_id+order_index for lectures, filename unique on colab_mappings)
    - Create indexes on `lectures.content_type` and `lectures.section_id`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 12.4_

  - [x] 1.3 Set up Alembic migrations
    - Create `backend/alembic.ini` and `backend/alembic/` directory
    - Generate initial migration with all tables (courses, modules, sections, lectures, colab_mappings)
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 1.4 Create Pydantic response schemas
    - Create `backend/app/schemas/course.py` with CourseResponse, CourseDetailResponse, ModuleResponse, SectionResponse
    - Create `backend/app/schemas/lecture.py` with LectureResponse, LectureMetadataResponse
    - Create `backend/app/schemas/content.py` with ErrorResponse
    - _Requirements: 4.1, 4.2, 4.4_

- [x] 2. Implement Tree Parser Service
  - [x] 2.1 Implement ContentType enum and detect_content_type function
    - Create `backend/app/services/tree_parser.py`
    - Implement `ContentType` enum with all supported types: mp4, pdf, ipynb, html, docx, txt, mp3, zip, png, pptx
    - Implement `detect_content_type(filename: str) -> ContentType | None` with case-insensitive extension matching
    - Return None for directories (no extension) or unrecognized extensions
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 2.2 Write property tests for content type detection
    - **Property 5: Content Type Case Insensitivity**
    - **Property 6: Unknown Extensions Return Null**
    - **Validates: Requirements 2.2, 2.3**

  - [x] 2.3 Implement parse_tree_file function
    - Implement `ParsedNode` dataclass with name, path, depth, content_type, children
    - Implement `parse_tree_file(file_path: str) -> ParsedNode` using stack-based algorithm
    - Handle standard box-drawing characters (├──, └──, │) and space indentation
    - Skip unparseable lines with logged warnings (include line numbers)
    - Return root ParsedNode with empty children for empty/whitespace-only files
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 2.4 Write property tests for tree parsing
    - **Property 1: Tree Parsing Completeness**
    - **Property 2: Hierarchy Preservation**
    - **Property 3: Sibling Order Preservation**
    - **Property 4: Tree Parsing Round Trip**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 2.5 Implement database seeding from parsed tree
    - Implement `seed_database(course_name: str, root_node: ParsedNode) -> None`
    - Map depth-1 nodes to Modules, depth-2 to Sections, depth-3+ leaves to Lectures
    - Handle top-level file leaves by creating default Module/Section
    - Flatten non-leaf depth-3+ nodes into parent Section
    - Assign sequential order_index values starting from 0 with no gaps
    - Implement idempotent seeding (check if course already exists by source_file)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 2.6 Write property tests for database seeding
    - **Property 7: Depth-to-Entity Mapping**
    - **Property 8: Idempotent Seeding**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.5**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Content API (FastAPI routes)
  - [x] 4.1 Implement course browsing endpoints
    - Create `backend/app/routers/courses.py`
    - Implement `GET /api/courses` returning all courses with title, description, module_count, lecture_count
    - Implement `GET /api/courses/{course_id}` returning full nested structure (modules → sections → lectures)
    - Return HTTP 404 with descriptive error for non-existent course IDs
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 4.2 Implement lecture metadata endpoint
    - Create `backend/app/routers/lectures.py`
    - Implement `GET /api/lectures/{lecture_id}` returning title, content_type, file_path, colab_url
    - Return HTTP 404 for non-existent lecture IDs
    - _Requirements: 4.4_

  - [x] 4.3 Implement path security utility
    - Create `backend/app/utils/path_security.py`
    - Validate all file paths resolve within the configured MEDIA_ROOT
    - Reject paths with `../` traversal sequences, symlink escapes, or absolute paths
    - Return HTTP 403 for path traversal attempts
    - Never expose absolute file system paths in API responses
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 4.4 Write property tests for path security
    - **Property 10: Path Traversal Prevention**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 4.5 Implement content resolution endpoint
    - Create `backend/app/services/content_resolver.py`
    - Implement `GET /api/lectures/{lecture_id}/content`
    - For mp4/pdf: return streaming FileResponse with correct MIME type
    - For ipynb: return HTTP 307 redirect to Colab URL (or 404 if no mapping)
    - For docx: convert to HTML using python-docx, return HTMLResponse
    - For txt: wrap in preformatted HTML template, return HTMLResponse
    - Return HTTP 404 for missing files on media volume
    - Return HTTP 415 for unsupported content types
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 4.6 Write property tests for content resolution
    - **Property 9: Content Resolution Correctness**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

  - [x] 4.7 Implement DOCX renderer utility
    - Create `backend/app/utils/docx_renderer.py`
    - Convert `.docx` files to valid HTML
    - Return HTTP 422 for corrupted/unsupported DOCX files
    - _Requirements: 5.4, 12.2_

  - [x] 4.8 Implement FastAPI application entry point
    - Create `backend/app/main.py` with lifespan context manager
    - Initialize database connection on startup, close on shutdown
    - Seed courses on first run if database is empty (using tree files from `data/` directory)
    - Add CORS middleware restricted to FRONTEND_URL
    - Include course and lecture routers with `/api` prefix
    - Implement HTTP 503 with Retry-After header when database is unreachable
    - _Requirements: 12.1, 12.4_

  - [ ]* 4.9 Write unit tests for API endpoints
    - Test course listing, detail, and 404 responses
    - Test lecture metadata and content resolution for each content type
    - Test path security rejection scenarios
    - Test error handling (503 for DB failure, 422 for corrupt DOCX, 415 for unsupported type)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 6.1, 6.2, 12.1, 12.2_

- [ ] 5. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Colab Integration Service
  - [x] 6.1 Implement Colab integration service
    - Create `backend/app/services/colab_integration.py`
    - Implement `get_colab_url(filename: str) -> str | None` for database lookup
    - Implement `upload_and_map(local_path: str) -> ColabMapping` using Google Drive API
    - Implement `batch_upload(directory: str) -> list[ColabMapping]` for directory processing
    - Generate Colab URLs in format `https://colab.research.google.com/drive/{file_id}`
    - Skip already-mapped files during batch operations
    - Log errors per-file and continue on upload failures
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 6.2 Write property tests for Colab integration
    - **Property 11: Colab URL Format Integrity**
    - **Property 13: Batch Upload Resilience**
    - **Validates: Requirements 7.3, 7.4, 7.5**

  - [x] 6.3 Create upload helper CLI script
    - Create `scripts/upload_notebooks.py` with argparse CLI
    - Support `--directory` flag for batch upload of all `.ipynb` files
    - Support `--file` flag for single notebook upload
    - Report results (success count, failures) to stdout
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 7. Implement React Frontend
  - [x] 7.1 Initialize frontend project with Vite, React, TypeScript, and TailwindCSS
    - Create `frontend/` with Vite + React + TypeScript template
    - Install dependencies: react-router-dom, @tanstack/react-query, tailwindcss
    - Configure `vite.config.ts` with API proxy to backend
    - Create `frontend/src/types/index.ts` with Course, Module, Section, Lecture interfaces
    - _Requirements: 8.1_

  - [x] 7.2 Implement API client and data hooks
    - Create `frontend/src/api/client.ts` with functions for getCourses, getCourseDetail, getLectureContent
    - Create `frontend/src/hooks/useCourses.ts`, `useCourseDetail.ts`, `useActiveLecture.ts` using @tanstack/react-query
    - Handle loading states and API errors
    - _Requirements: 8.4, 8.5_

  - [x] 7.3 Implement course list page
    - Create `frontend/src/pages/CourseList.tsx`
    - Display all courses with title, module count, and lecture count
    - Link each course card to its detail page
    - Show loading indicator while fetching
    - Display error message on API failure
    - _Requirements: 8.1, 8.4, 8.5_

  - [x] 7.4 Implement course detail page with sidebar navigation
    - Create `frontend/src/pages/CourseDetail.tsx`
    - Create `frontend/src/components/Sidebar.tsx` with hierarchical tree (modules → sections → lectures)
    - Highlight active lecture in sidebar
    - Show loading indicator during content fetch
    - _Requirements: 8.2, 8.3, 8.4_

  - [x] 7.5 Implement content viewer components
    - Create `frontend/src/components/ContentViewer.tsx` (dispatcher)
    - Create `frontend/src/components/VideoPlayer.tsx` with HTML5 `<video>` and playback controls
    - Create `frontend/src/components/PdfViewer.tsx` with embedded iframe
    - Create `frontend/src/components/HtmlContent.tsx` for docx/txt rendered HTML
    - Create `frontend/src/components/ColabRedirect.tsx` that opens Colab URL in new tab
    - Show "unsupported content type" message for unknown types
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 7.6 Write unit tests for frontend components
    - Test ContentViewer dispatches correct viewer per content_type
    - Test CourseList renders course cards with correct data
    - Test Sidebar renders hierarchical tree structure
    - Test error and loading states
    - **Property 14: Content Viewer Type Dispatch**
    - **Validates: Requirements 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 9.4, 9.5**

  - [x] 7.7 Set up React Router and App shell
    - Create `frontend/src/App.tsx` with routes: `/` (CourseList), `/courses/:courseId` (CourseDetail)
    - Create `frontend/src/main.tsx` with QueryClientProvider and BrowserRouter
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 8. Checkpoint - Ensure all frontend and backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Docker Compose orchestration and wiring
  - [x] 9.1 Create backend Dockerfile
    - Create `backend/Dockerfile` using `python:3.11-slim`
    - Install `uv` from `ghcr.io/astral-sh/uv:latest`
    - Copy `pyproject.toml` and `uv.lock` first for layer caching
    - Run `uv sync --frozen --no-dev` for reproducible dependency installation
    - Expose port 8000, run with `uv run uvicorn`
    - _Requirements: 11.3_

  - [x] 9.2 Create frontend Dockerfile
    - Create `frontend/Dockerfile` with multi-stage build (Node 20 for build, Nginx for serve)
    - Create `frontend/nginx.conf` with `/api` proxy to backend
    - _Requirements: 11.1_

  - [x] 9.3 Create docker-compose.yml
    - Define services: frontend (port 3000), backend (port 8000), postgres (port 5432, postgres:16-alpine)
    - Add PostgreSQL healthcheck (`pg_isready`)
    - Backend depends_on postgres with `condition: service_healthy`
    - Mount `./media` as volume to backend, `pgdata` named volume for postgres
    - Mount `./data` to backend for tree files
    - Use `env_file: .env` for all secrets
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 9.4 Create seed database script
    - Create `scripts/seed_db.py` that initializes DB and runs tree parser seeding
    - Read tree files from `data/applied_diploma_ai_ml.txt` and `data/applied_roots.txt`
    - _Requirements: 3.1, 3.3_

- [ ] 10. Integration testing and cascade delete verification
  - [ ]* 10.1 Write integration tests for full request lifecycle
    - Test seed → query courses → fetch lecture content flow
    - Test streaming responses for media files
    - Test CORS headers
    - Verify cascade deletes (delete course → all children removed)
    - **Property 12: Cascade Delete Integrity**
    - **Validates: Requirements 10.1, 10.2, 10.3, 4.1, 4.2**

  - [ ]* 10.2 Write end-to-end tests with Playwright
    - Test navigation: course list → course detail → sidebar → lecture
    - Verify video player renders for mp4 lectures
    - Verify PDF viewer renders for pdf lectures
    - Verify Colab redirect opens new tab for ipynb lectures
    - Test error states and loading indicators
    - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 9.4_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The backend uses Python 3.11 with uv package manager; the frontend uses TypeScript with Vite
- All Docker services share secrets via `.env` file (gitignored)
- The tree parser and seeding logic is the foundational data pipeline — implement it first

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.4"] },
    { "id": 2, "tasks": ["1.3", "2.1"] },
    { "id": 3, "tasks": ["2.2", "2.3"] },
    { "id": 4, "tasks": ["2.4", "2.5"] },
    { "id": 5, "tasks": ["2.6", "4.1", "4.2", "4.3"] },
    { "id": 6, "tasks": ["4.4", "4.5", "4.7"] },
    { "id": 7, "tasks": ["4.6", "4.8"] },
    { "id": 8, "tasks": ["4.9", "6.1", "7.1"] },
    { "id": 9, "tasks": ["6.2", "6.3", "7.2", "7.7"] },
    { "id": 10, "tasks": ["7.3", "7.4", "7.5"] },
    { "id": 11, "tasks": ["7.6", "9.1", "9.2"] },
    { "id": 12, "tasks": ["9.3", "9.4"] },
    { "id": 13, "tasks": ["10.1", "10.2"] }
  ]
}
```
