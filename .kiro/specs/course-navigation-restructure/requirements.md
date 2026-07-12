# Requirements Document

## Introduction

This document specifies requirements for restructuring the learning platform's navigation from a flat two-level pattern (course list → course detail) into a multi-level drill-down experience. Users navigate through Specializations → Modules → Sections → Content Viewer with a scoped sidebar. The feature introduces three new backend endpoints with aggregate counts, a grouped sort algorithm replacing natural sort, two new frontend pages, a modified content viewer with scoped sidebar, and updated React Router routes.

## Glossary

- **Specialization**: The top-level navigation entity displayed to users, corresponding to a Course record in the database.
- **Module**: A semester-level grouping within a Specialization, corresponding to a Module record in the database.
- **Section**: A course/topic grouping within a Module, corresponding to a Section record in the database.
- **Lecture**: An individual content item within a Section, corresponding to a Lecture record in the database.
- **Navigation_Card**: A clickable UI element displaying an entity's title and aggregate counts, linking to the next drill-down level.
- **Scoped_Sidebar**: A sidebar panel in the content viewer that displays only lectures belonging to the currently active Section.
- **Leading_Integer**: The first contiguous sequence of digits at the start of a filename, with leading zeros stripped (e.g., "01." → 1, "1.1" → 1).
- **Full_Numeric_Prefix**: All dot-separated numeric components from the start of a filename (e.g., "1.2.3 Topic" → [1, 2, 3]).
- **Grouped_Sort**: A sorting algorithm that groups items by their Leading_Integer, orders groups sequentially, and sorts within each group by Full_Numeric_Prefix.
- **Content_Viewer**: The page component that renders lecture content (video, PDF, notebook, etc.) alongside the Scoped_Sidebar.
- **Breadcrumb**: A navigation trail showing the user's current position in the hierarchy (Home > Specialization > Module > Section).
- **API**: The FastAPI backend providing RESTful JSON endpoints.
- **Frontend**: The React single-page application consuming the API.

## Requirements

### Requirement 1: Multi-Level Navigation Structure

**User Story:** As a learner, I want to navigate through Specializations → Modules → Sections → Content, so that I can progressively drill down into the learning material at a comfortable pace.

#### Acceptance Criteria

1. WHEN a user visits the home page, THE Frontend SHALL display all Specializations as Navigation_Cards with title, description, module count, and lecture count.
2. WHEN a user clicks a Specialization card, THE Frontend SHALL navigate to the Specialization detail page and display that Specialization's Modules as Navigation_Cards with title, section count, and lecture count.
3. WHEN a user clicks a Module card, THE Frontend SHALL navigate to the Module detail page and display that Module's Sections as Navigation_Cards with title and lecture count.
4. WHEN a user clicks a Section card, THE Frontend SHALL navigate to the Content_Viewer page displaying the Scoped_Sidebar with that Section's lectures.

### Requirement 2: Backend Module Listing Endpoint

**User Story:** As a frontend developer, I want an endpoint that returns modules for a specific course with aggregate counts, so that I can render Specialization detail pages without loading the entire course tree.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/courses/{course_id}/modules` with a valid course_id, THE API SHALL return a JSON array of modules ordered by order_index ascending, each containing id, title, order, section_count, and lecture_count.
2. WHEN a GET request is made to `/api/courses/{course_id}/modules` with a course_id that does not exist in the database, THE API SHALL return HTTP 404 with a detail message indicating the course was not found.
3. THE API SHALL compute section_count as the exact number of Section records whose module_id matches the module.
4. THE API SHALL compute lecture_count as the exact number of Lecture records nested under all Sections belonging to the module.

### Requirement 3: Backend Section Listing Endpoint

**User Story:** As a frontend developer, I want an endpoint that returns sections for a specific module with lecture counts, so that I can render Module detail pages efficiently.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/modules/{module_id}/sections` with a valid module_id, THE API SHALL return a JSON array of sections ordered by order_index ascending, each containing id, title, order, and lecture_count.
2. WHEN a GET request is made to `/api/modules/{module_id}/sections` with a module_id that does not exist in the database, THE API SHALL return HTTP 404 with a detail message indicating the module was not found.
3. THE API SHALL compute lecture_count as the exact number of Lecture records whose section_id matches the section.

### Requirement 4: Backend Section Detail Endpoint

**User Story:** As a frontend developer, I want an endpoint that returns a section with its lectures and parent context, so that the Content_Viewer can render the Scoped_Sidebar and breadcrumb navigation.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/sections/{section_id}` with a valid section_id, THE API SHALL return a JSON object containing id, title, module_id, module_title, course_id, course_title, and a lectures array.
2. WHEN a GET request is made to `/api/sections/{section_id}` with a section_id that does not exist in the database, THE API SHALL return HTTP 404 with a detail message indicating the section was not found.
3. THE API SHALL include in the lectures array only Lecture records whose section_id matches the requested section_id.
4. THE API SHALL order the lectures array by order_index ascending.
5. THE API SHALL populate module_id and module_title from the Section's parent Module record, and course_id and course_title from the Module's parent Course record.

### Requirement 5: Scoped Sidebar in Content Viewer

**User Story:** As a learner, I want the content viewer sidebar to show only lectures from my current section, so that I can focus on the relevant material without being overwhelmed by the full course tree.

#### Acceptance Criteria

1. WHEN the Content_Viewer page loads, THE Frontend SHALL render a sidebar containing only lectures belonging to the current Section.
2. WHEN a user clicks a lecture in the Scoped_Sidebar, THE Content_Viewer SHALL display that lecture's content in the main content area.
3. WHILE a lecture is active in the Content_Viewer, THE Scoped_Sidebar SHALL visually distinguish the active lecture from other lectures in the list.
4. WHEN the Content_Viewer page loads, THE Frontend SHALL display Breadcrumb navigation showing the path Home > Specialization > Module > Section.
5. IF the section detail API request fails or returns an error, THEN THE Frontend SHALL display an error page with a message and a link back to the home page.

### Requirement 6: Grouped Sort Algorithm

**User Story:** As a learner, I want lectures to be grouped by their leading number so that related sub-topics (e.g., 1.1, 1.2) appear immediately after their parent topic (e.g., 01. Introduction), rather than being separated by other numbered items.

#### Acceptance Criteria

1. THE Grouped_Sort algorithm SHALL place all items sharing the same Leading_Integer into adjacent positions in the sorted output.
2. THE Grouped_Sort algorithm SHALL order groups by their Leading_Integer value in ascending numeric order.
3. WHILE items are within the same Leading_Integer group, THE Grouped_Sort algorithm SHALL order them by their Full_Numeric_Prefix, comparing element-by-element as integers.
4. WHEN an item has no numeric prefix, THE Grouped_Sort algorithm SHALL place that item after all numerically-prefixed items.
5. THE Grouped_Sort algorithm SHALL produce a deterministic output for items with identical sort keys by using the lowercase item name as a tiebreaker.

### Requirement 7: Leading Integer Extraction

**User Story:** As a developer, I want a reliable function to extract the leading integer from filenames, so that the grouped sort can correctly assign items to groups.

#### Acceptance Criteria

1. WHEN a filename starts with one or more digits (possibly zero-padded), THE _extract_leading_integer function SHALL return the integer value with leading zeros stripped.
2. WHEN a filename does not start with a digit, THE _extract_leading_integer function SHALL return None.
3. THE _extract_leading_integer function SHALL treat "01" and "1" as the same leading integer value of 1.
4. THE _extract_leading_integer function SHALL extract only the first contiguous integer before any non-digit character (e.g., "1.2 Topic" → 1, "10.3 Item" → 10).

### Requirement 8: Full Numeric Prefix Extraction

**User Story:** As a developer, I want a function to extract all dot-separated numeric components from a filename prefix, so that within-group ordering is correct.

#### Acceptance Criteria

1. WHEN a filename starts with a dot-separated numeric prefix, THE _extract_full_numeric_prefix function SHALL return a list of integers representing each numeric component.
2. WHEN a filename does not start with digits, THE _extract_full_numeric_prefix function SHALL return an empty list.
3. THE _extract_full_numeric_prefix function SHALL ignore trailing dots in the prefix (e.g., "1." → [1]).
4. THE _extract_full_numeric_prefix function SHALL parse multi-level prefixes correctly (e.g., "1.2.3 Topic" → [1, 2, 3]).

### Requirement 9: Frontend Route Structure

**User Story:** As a developer, I want well-defined React Router routes for the multi-level navigation, so that each level of the hierarchy has a unique URL and supports direct linking.

#### Acceptance Criteria

1. THE Frontend SHALL route the path `/` to the SpecializationList page component.
2. THE Frontend SHALL route the path `/specializations/:courseId` to the SpecializationDetail page component.
3. THE Frontend SHALL route the path `/specializations/:courseId/modules/:moduleId` to the ModuleDetail page component.
4. THE Frontend SHALL route the path `/courses/:sectionId` to the SectionViewer (Content_Viewer) page component.
5. WHEN a user navigates directly to a valid route URL, THE Frontend SHALL render the correct page and fetch the required data for that navigation level.
6. IF a page component encounters a rendering error after successful data fetching, THEN THE Frontend SHALL display an error page rather than crashing silently.

### Requirement 10: Navigation Card Display

**User Story:** As a learner, I want navigation cards to display meaningful aggregate counts, so that I can gauge the scope of content at each level before drilling down.

#### Acceptance Criteria

1. WHEN displaying a Specialization card, THE Frontend SHALL show the module count and total lecture count for that Specialization.
2. WHEN displaying a Module card, THE Frontend SHALL show the section count and total lecture count for that Module.
3. WHEN displaying a Section card, THE Frontend SHALL show the lecture count for that Section.
4. THE Frontend SHALL display counts that exactly match the values returned by the corresponding API endpoint.
