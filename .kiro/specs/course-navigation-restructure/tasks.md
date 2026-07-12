# Implementation Plan: Course Navigation Restructure

## Overview

Restructure the learning platform from a flat two-level navigation (CourseList → CourseDetail) into a multi-level drill-down experience (Specializations → Modules → Sections → Content Viewer). This involves replacing the sort algorithm, adding three new backend endpoints with aggregate counts, creating two new frontend pages, modifying the content viewer with a scoped sidebar, and updating React Router routes.

## Tasks

- [ ] 1. Backend: Implement grouped sort algorithm
  - [ ] 1.1 Implement `_extract_leading_integer`, `_extract_full_numeric_prefix`, and `_grouped_sort_key` in `backend/app/services/tree_parser.py`
    - Replace the existing `_natural_sort_key` function with the three new functions as specified in the design
    - `_extract_leading_integer(name: str) -> int | None`: regex-based extraction of leading integer with zero-stripping
    - `_extract_full_numeric_prefix(name: str) -> list[int]`: dot-separated numeric prefix extraction
    - `_grouped_sort_key(node: ParsedNode) -> tuple[int, list[int], str]`: composite sort key using leading group, full prefix, and lowercase name as tiebreaker
    - Update all references from `_natural_sort_key` to `_grouped_sort_key` within the module (used in `_process_lectures` and `seed_database`)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 1.2 Write property tests for the grouped sort algorithm
    - **Property 1: Group Adjacency** — For any sorted list, items sharing the same leading integer are always adjacent with no interleaving from other groups
    - **Property 2: Group Ordering** — For any two groups, the group with the smaller leading integer appears entirely before the group with the larger one
    - **Property 3: Intra-Group Ordering** — Within a group, items are ordered by full numeric prefix element-by-element
    - **Property 9: Non-Numeric Items Sort Last** — Items without a numeric prefix always appear after all numerically-prefixed items
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

  - [ ]* 1.3 Write unit tests for `_extract_leading_integer` and `_extract_full_numeric_prefix`
    - **Property 7: Leading Integer Extraction Correctness** — zero-padded values are stripped, non-numeric inputs return None, only first contiguous integer before non-digit is extracted
    - **Property 8: Full Numeric Prefix Extraction Correctness** — multi-level prefixes parse correctly, trailing dots ignored, non-numeric inputs return empty list
    - Test the documented examples from the design: "01." → 1, "1.1" → 1, "1.2.3 Topic" → [1, 2, 3], "No number" → None/[]
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4**

- [ ] 2. Backend: Add new Pydantic response schemas
  - [ ] 2.1 Create `ModuleListResponse`, `SectionListResponse`, and `SectionDetailResponse` schemas in `backend/app/schemas/course.py`
    - `ModuleListResponse`: id, title, order, section_count, lecture_count
    - `SectionListResponse`: id, title, order, lecture_count
    - `SectionDetailResponse`: id, title, module_id, module_title, course_id, course_title, lectures (list[LectureResponse])
    - All count fields are `int >= 0`
    - _Requirements: 2.1, 3.1, 4.1_

- [ ] 3. Backend: Implement new API endpoints
  - [ ] 3.1 Implement `GET /api/courses/{course_id}/modules` endpoint in `backend/app/routers/courses.py`
    - Verify course exists, return 404 if not
    - Query modules with LEFT JOIN to sections and lectures for aggregate counts using `func.count(distinct(...))` and `group_by`
    - Order results by `Module.order_index` ascending
    - Return `list[ModuleListResponse]` with section_count and lecture_count per module
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.2 Implement `GET /api/modules/{module_id}/sections` endpoint in `backend/app/routers/courses.py`
    - Verify module exists, return 404 if not
    - Query sections with LEFT JOIN to lectures for lecture_count using `func.count` and `group_by`
    - Order results by `Section.order_index` ascending
    - Return `list[SectionListResponse]` with lecture_count per section
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 3.3 Implement `GET /api/sections/{section_id}` endpoint in `backend/app/routers/courses.py`
    - Verify section exists, return 404 if not
    - Eager-load lectures via `selectinload`, plus parent module and grandparent course for breadcrumb data
    - Order lectures by `order_index` ascending
    - Return `SectionDetailResponse` with module_id, module_title, course_id, course_title, and lectures array
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.4 Write unit tests for the three new endpoints
    - **Property 4: Section Scoping** — GET /api/sections/{id} returns ONLY lectures whose section_id matches the requested section
    - **Property 5: Breadcrumb Consistency** — SectionDetailResponse module_id/course_id correctly reference the parent chain
    - **Property 6: Count Accuracy** — section_count and lecture_count match actual record counts in the database
    - **Property 10: Endpoint 404 for Invalid IDs** — non-existent IDs return HTTP 404
    - **Property 11: Endpoint Result Ordering** — results are ordered by order_index ascending
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5**

- [ ] 4. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Frontend: Add new TypeScript types and API client functions
  - [ ] 5.1 Add `ModuleListItem`, `SectionListItem`, and `SectionDetail` interfaces to `frontend/src/types/index.ts`
    - `ModuleListItem`: id, title, order, section_count, lecture_count
    - `SectionListItem`: id, title, order, lecture_count
    - `SectionDetail`: id, title, module_id, module_title, course_id, course_title, lectures (Lecture[])
    - _Requirements: 2.1, 3.1, 4.1_

  - [ ] 5.2 Add `getModulesForCourse`, `getSectionsForModule`, and `getSectionDetail` functions to `frontend/src/api/client.ts`
    - `getModulesForCourse(courseId: number): Promise<ModuleListItem[]>` → GET `/api/courses/${courseId}/modules`
    - `getSectionsForModule(moduleId: number): Promise<SectionListItem[]>` → GET `/api/modules/${moduleId}/sections`
    - `getSectionDetail(sectionId: number): Promise<SectionDetail>` → GET `/api/sections/${sectionId}`
    - _Requirements: 2.1, 3.1, 4.1_

- [ ] 6. Frontend: Create new page components
  - [ ] 6.1 Create `SpecializationList` page in `frontend/src/pages/SpecializationList.tsx`
    - Replaces the existing `CourseList` page as the home page
    - Fetch courses using existing `GET /api/courses` endpoint
    - Render Navigation_Cards with title, description, module_count, and lecture_count
    - Link each card to `/specializations/:courseId`
    - Display empty state if no specializations exist (show cards with zero counts)
    - _Requirements: 1.1, 10.1_

  - [ ] 6.2 Create `SpecializationDetail` page in `frontend/src/pages/SpecializationDetail.tsx`
    - Fetch modules via `getModulesForCourse(courseId)` using `@tanstack/react-query`
    - Render Navigation_Cards with title, section_count, and lecture_count
    - Link each card to `/specializations/:courseId/modules/:moduleId`
    - Show breadcrumb: Home > Specialization Name (breadcrumb data blocks page loading until available)
    - Handle loading and error states (show error page on fetch failure)
    - _Requirements: 1.2, 5.4, 10.2_

  - [ ] 6.3 Create `ModuleDetail` page in `frontend/src/pages/ModuleDetail.tsx`
    - Fetch sections via `getSectionsForModule(moduleId)` using `@tanstack/react-query`
    - Render Navigation_Cards with title and lecture_count
    - Link each card to `/courses/:sectionId`
    - Show breadcrumb: Home > Specialization > Module (breadcrumb data blocks page loading until available)
    - Handle loading and error states (show error page on fetch failure)
    - _Requirements: 1.3, 5.4, 10.3_

  - [ ] 6.4 Create `SectionViewer` page in `frontend/src/pages/SectionViewer.tsx`
    - Fetch section detail via `getSectionDetail(sectionId)` using `@tanstack/react-query`
    - Render Scoped_Sidebar showing ONLY lectures from the current section
    - Visually distinguish the active lecture in the sidebar (highlight/background color change)
    - Render breadcrumb: Home > Specialization > Module > Section using course_title, module_title from response
    - On sidebar lecture click, display that lecture's content in the main area
    - If section detail API request fails, display an error page with message and link back to home
    - _Requirements: 1.4, 5.1, 5.2, 5.3, 5.4, 5.5, 10.3_

- [ ] 7. Frontend: Update routing and wire pages together
  - [ ] 7.1 Update `frontend/src/App.tsx` with new route definitions
    - Replace existing routes with the new multi-level hierarchy:
      - `/` → `SpecializationList`
      - `/specializations/:courseId` → `SpecializationDetail`
      - `/specializations/:courseId/modules/:moduleId` → `ModuleDetail`
      - `/courses/:sectionId` → `SectionViewer`
    - Remove imports for old `CourseList` and `CourseDetail` components
    - Add an error boundary wrapper around routes to catch rendering errors and display error page (Requirement 9.6)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 7.2 Write integration tests for frontend routing
    - Verify each route renders the correct page component
    - Verify direct URL navigation works (Requirement 9.5)
    - Verify error boundary catches rendering failures and shows error page (Requirement 9.6)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The database schema is NOT modified — only new endpoints and sort logic are added
- The existing `CourseDetail` page and `/courses/:courseId` route will be replaced; the old files can be removed or kept as reference
- Backend uses Python (FastAPI + SQLAlchemy async), Frontend uses TypeScript (React 18 + TailwindCSS + @tanstack/react-query + react-router-dom)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "5.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "3.1", "3.2", "3.3", "5.2"] },
    { "id": 2, "tasks": ["3.4", "6.1", "6.2", "6.3", "6.4"] },
    { "id": 3, "tasks": ["7.1"] },
    { "id": 4, "tasks": ["7.2"] }
  ]
}
```
