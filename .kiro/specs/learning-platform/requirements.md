# Requirements Document

## Introduction

This document defines the requirements for a fullstack learning platform that enables users to browse courses, navigate hierarchical content structures, and consume various media types (MP4, PDF, DOCX, TXT, IPYNB via Google Colab). Course structures are bootstrapped from directory tree text files. The system uses FastAPI, React, PostgreSQL, and Docker Compose, with Python dependencies managed by uv.

## Glossary

- **Tree_Parser**: The backend service that reads directory tree text files and converts them into hierarchical course structures for database seeding.
- **Content_Resolver**: The backend service that determines how to serve lecture content based on its content type (streaming, rendering, or redirecting).
- **Content_API**: The FastAPI REST layer that exposes course data, content trees, and media to the frontend.
- **Frontend**: The React TypeScript application that renders course navigation, content viewing, and media playback.
- **Colab_Integration_Service**: The service that maps `.ipynb` notebook files to Google Colab URLs and provides upload tooling.
- **Database**: The PostgreSQL instance storing courses, modules, sections, lectures, and Colab mappings.
- **Media_Volume**: The Docker volume where media files (videos, PDFs, documents) are stored on disk.
- **ParsedNode**: A data structure representing a single node in the parsed tree hierarchy, with name, path, depth, content type, and children.
- **Seeding**: The process of populating the database with course structure derived from tree text files.
- **Content_Type**: An enumeration of supported file types: mp4, pdf, ipynb, html, docx, txt, mp3, zip, png, pptx.

## Requirements

### Requirement 1: Tree File Parsing

**User Story:** As a platform administrator, I want to parse directory tree text files into structured course hierarchies, so that I can bootstrap course content from existing file system layouts.

#### Acceptance Criteria

1. WHEN a valid tree text file is provided, THE Tree_Parser SHALL parse every non-empty content line into exactly one ParsedNode in the output hierarchy.
2. WHEN a line in the tree file is indented beneath another line, THE Tree_Parser SHALL represent that line as a descendant of the parent line's ParsedNode.
3. WHEN a tree file contains sibling entries at the same depth, THE Tree_Parser SHALL preserve their original ordering in the children list.
4. WHEN a tree file contains unparseable lines (broken encoding or non-standard tree characters), THE Tree_Parser SHALL skip those lines, log warnings with line numbers, and continue parsing the remaining content.
5. WHEN a tree file is empty or contains only whitespace, THE Tree_Parser SHALL return a root ParsedNode with an empty children list.

### Requirement 2: Content Type Detection

**User Story:** As a platform administrator, I want file extensions to be automatically detected and classified, so that the system knows how to serve each piece of content.

#### Acceptance Criteria

1. THE Tree_Parser SHALL detect content types from file extensions for all supported types: mp4, pdf, ipynb, html, docx, txt, mp3, zip, png, pptx.
2. WHEN a filename has a recognized extension in any letter case, THE Tree_Parser SHALL return the same Content_Type regardless of case (e.g., `.PDF` equals `.pdf`).
3. WHEN a filename has no extension or an unrecognized extension, THE Tree_Parser SHALL return a null content type.
4. THE Tree_Parser SHALL produce the same Content_Type value for any given filename on every invocation (deterministic behavior).

### Requirement 3: Database Seeding from Tree Structure

**User Story:** As a platform administrator, I want parsed tree structures to be mapped to the database hierarchy, so that courses are browsable through the API.

#### Acceptance Criteria

1. WHEN a parsed tree is seeded, THE Tree_Parser SHALL map depth-1 nodes to Module records, depth-2 nodes to Section records, and depth-3+ leaf nodes to Lecture records.
2. WHEN a seeded Module, Section, or Lecture set is created, THE Tree_Parser SHALL assign sequential order_index values starting from 0 with no gaps within each parent.
3. WHEN seeding is run multiple times with the same tree file, THE Tree_Parser SHALL create only one Course record for that source file (idempotent seeding).
4. WHEN a depth-1 node has a file extension (is a leaf), THE Tree_Parser SHALL create a default Module and Section to contain that lecture.
5. WHEN a depth-3+ node is a directory (not a leaf), THE Tree_Parser SHALL flatten its children as lectures into the parent Section.

### Requirement 4: Course Browsing API

**User Story:** As a learner, I want to browse available courses and their hierarchical content structure, so that I can find and navigate learning materials.

#### Acceptance Criteria

1. WHEN a client requests the course list endpoint, THE Content_API SHALL return all courses with their title, description, module count, and lecture count.
2. WHEN a client requests a specific course by ID, THE Content_API SHALL return the full nested structure (modules containing sections containing lectures).
3. WHEN a client requests a course ID that does not exist, THE Content_API SHALL return HTTP 404 with a descriptive error message.
4. WHEN a client requests lecture metadata by lecture ID, THE Content_API SHALL return the lecture title, content type, file path, and Colab URL (if applicable).

### Requirement 5: Content Resolution and Serving

**User Story:** As a learner, I want to consume lecture content in the appropriate format, so that I can watch videos, read documents, and open notebooks seamlessly.

#### Acceptance Criteria

1. WHEN a lecture with content_type mp4 or pdf is requested for content, THE Content_Resolver SHALL return a streaming file response with the correct MIME type.
2. WHEN a lecture with content_type ipynb is requested for content AND a valid Colab URL exists in the mapping table, THE Content_Resolver SHALL return an HTTP 307 redirect to the Colab URL.
3. WHEN a lecture with content_type ipynb is requested for content AND no Colab URL mapping exists, THE Content_Resolver SHALL return HTTP 404 with a message indicating the Colab URL is not configured.
4. WHEN a lecture with content_type docx is requested for content, THE Content_Resolver SHALL convert the document to HTML and return an HTML response.
5. WHEN a lecture with content_type txt is requested for content, THE Content_Resolver SHALL wrap the text content in a preformatted HTML template and return an HTML response.
6. WHEN a lecture references a file that does not exist on the Media_Volume, THE Content_Resolver SHALL return HTTP 404 with a descriptive error message.
7. WHEN a lecture has an unsupported content type, THE Content_Resolver SHALL return HTTP 415 with an error indicating the type is unsupported.

### Requirement 6: Path Security

**User Story:** As a system operator, I want all file access to be scoped to the media volume, so that directory traversal attacks are prevented.

#### Acceptance Criteria

1. THE Content_Resolver SHALL validate all file paths against the configured Media_Volume root before serving content.
2. WHEN a resolved file path would escape the Media_Volume root (e.g., using `../`), THE Content_Resolver SHALL reject the request and return HTTP 403.
3. THE Content_Resolver SHALL never expose absolute file system paths in API responses.

### Requirement 7: Colab Integration

**User Story:** As a platform administrator, I want to upload notebooks to Google Drive and maintain a mapping table, so that learners can open notebooks in Google Colab.

#### Acceptance Criteria

1. WHEN the upload helper script is run with a single notebook file, THE Colab_Integration_Service SHALL upload the file to Google Drive and store the mapping (filename, drive file ID, Colab URL) in the Database.
2. WHEN the upload helper script is run with a directory, THE Colab_Integration_Service SHALL batch upload all `.ipynb` files and store their mappings.
3. WHEN an upload fails for a specific file, THE Colab_Integration_Service SHALL log the error and continue processing remaining files.
4. WHEN a notebook has already been mapped, THE Colab_Integration_Service SHALL skip re-uploading that file during batch operations.
5. THE Colab_Integration_Service SHALL generate Colab URLs in the format `https://colab.research.google.com/drive/{file_id}`.

### Requirement 8: Frontend Course Navigation

**User Story:** As a learner, I want to browse courses and navigate their hierarchical structure through a sidebar, so that I can quickly find specific lectures.

#### Acceptance Criteria

1. WHEN the course list page loads, THE Frontend SHALL display all available courses with their title, module count, and lecture count.
2. WHEN a learner selects a course, THE Frontend SHALL display a sidebar tree showing modules, sections, and lectures in hierarchical order.
3. WHEN a learner selects a lecture from the sidebar, THE Frontend SHALL render the appropriate content viewer for that lecture's content type.
4. WHILE content is loading, THE Frontend SHALL display a loading indicator.
5. IF an API request fails, THEN THE Frontend SHALL display an error message with contextual information.

### Requirement 9: Frontend Content Viewers

**User Story:** As a learner, I want media content rendered appropriately by type, so that I can consume videos, documents, and notebooks in the best available format.

#### Acceptance Criteria

1. WHEN a lecture with content_type mp4 is selected, THE Frontend SHALL render an HTML5 video player with playback controls.
2. WHEN a lecture with content_type pdf is selected, THE Frontend SHALL render the PDF in an embedded viewer (iframe or pdf.js).
3. WHEN a lecture with content_type docx or txt is selected, THE Frontend SHALL display the HTML-rendered content in a styled container.
4. WHEN a lecture with content_type ipynb is selected, THE Frontend SHALL redirect the user to the Google Colab URL in a new browser tab.
5. WHEN a lecture has an unsupported content type, THE Frontend SHALL display a message indicating the content type is not supported.

### Requirement 10: Database Integrity

**User Story:** As a system operator, I want the database to enforce referential integrity and cascading deletes, so that no orphan records exist.

#### Acceptance Criteria

1. WHEN a Course is deleted, THE Database SHALL cascade-delete all associated Modules, Sections, and Lectures.
2. WHEN a Module is deleted, THE Database SHALL cascade-delete all associated Sections and Lectures.
3. THE Database SHALL enforce uniqueness on (course_id, order_index) for Modules, (module_id, order_index) for Sections, and (section_id, order_index) for Lectures.
4. THE Database SHALL enforce that the filename column in colab_mappings is unique.

### Requirement 11: Docker Compose Orchestration

**User Story:** As a developer, I want the entire platform to run via Docker Compose, so that the development environment is reproducible and self-contained.

#### Acceptance Criteria

1. WHEN `docker-compose up` is executed, THE system SHALL start the frontend, backend, and PostgreSQL services.
2. THE backend service SHALL wait for PostgreSQL to be healthy (via healthcheck) before starting.
3. THE backend service SHALL use `uv sync --frozen` to install dependencies from the lockfile, ensuring reproducible builds.
4. THE system SHALL store all secrets (database credentials, API keys) in a `.env` file that is gitignored.
5. THE system SHALL mount the media directory as a volume accessible to the backend service.

### Requirement 12: Error Handling and Fault Tolerance

**User Story:** As a system operator, I want the platform to handle errors gracefully and continue operating, so that partial failures do not bring down the entire system.

#### Acceptance Criteria

1. IF the Database becomes unreachable during an API request, THEN THE Content_API SHALL return HTTP 503 with a Retry-After header.
2. IF a DOCX file is corrupted or uses unsupported features, THEN THE Content_Resolver SHALL return HTTP 422 with a descriptive error message.
3. IF the Google Drive API returns an error during upload, THEN THE Colab_Integration_Service SHALL log the error per-file and continue with remaining files.
4. WHEN the backend starts, THE Content_API SHALL use connection pool retry logic (3 attempts, exponential backoff) for transient database failures.
