# Requirements Document

## Introduction

This feature adds progress tracking to the learning platform, allowing a user to see how far they have progressed through each course. Lectures can be marked as completed either manually (via a button) or automatically (when a video ends and the player advances to the next lecture). Course completion percentages are displayed on the course list page and the course detail page, and all progress data is persisted in PostgreSQL so it survives page refreshes and browser restarts.

Because the platform is a single-user application with no authentication, progress is stored globally without any user identifier.

## Glossary

- **Progress_Service**: The backend service responsible for recording and calculating lecture completion status.
- **Progress_API**: The set of FastAPI REST endpoints that the frontend calls to read and write progress data.
- **Content_Viewer**: The React component that displays lecture content and hosts the Mark as Complete button.
- **Video_Player**: The React component that plays MP4 lectures, including auto-advance countdown logic.
- **Course_List_Page**: The home page displaying all available courses with summary metadata.
- **Course_Detail_Page**: The page showing the sidebar navigation tree and content viewer for a specific course.
- **Lecture_Progress**: A database record indicating that a specific lecture has been completed.
- **Course_Progress_Percentage**: The ratio of completed lectures to total lectures in a course, expressed as a whole-number percentage (0–100).

## Requirements

### Requirement 1: Persist Lecture Completion

**User Story:** As a learner, I want my lecture completion status saved in the database, so that my progress is preserved across page refreshes and browser sessions.

#### Acceptance Criteria

1. WHEN a lecture is marked as completed, THE Progress_Service SHALL create a Lecture_Progress record containing the lecture ID and a completion timestamp recorded in UTC.
2. THE Progress_Service SHALL store Lecture_Progress records in PostgreSQL with a unique constraint on lecture ID to prevent duplicate entries.
3. IF a completion request is received for an already-completed lecture, THEN THE Progress_API SHALL return an HTTP 200 response with the existing completion data without creating a duplicate record.
4. WHEN the application restarts, THE Progress_Service SHALL retain all previously stored Lecture_Progress records.
5. IF a completion request references a lecture ID that does not exist in the lectures table, THEN THE Progress_API SHALL return an HTTP 404 response with an error message indicating the lecture was not found, without creating a Lecture_Progress record.
6. IF the database is unreachable when a completion request is received, THEN THE Progress_API SHALL return an HTTP 503 response with a Retry-After header.

### Requirement 2: Mark Lecture as Complete Manually

**User Story:** As a learner, I want a "Mark as Complete" button in the content viewer, so that I can explicitly indicate I have finished a lecture.

#### Acceptance Criteria

1. WHILE a lecture is displayed in the Content_Viewer, THE Content_Viewer SHALL display a "Mark as Complete" button.
2. WHEN the user clicks the "Mark as Complete" button, THE Content_Viewer SHALL disable the button to prevent duplicate submissions and send a completion request to the Progress_API for the active lecture.
3. WHEN the Progress_API confirms completion, THE Content_Viewer SHALL update the button to show a "Completed" state with a checkmark icon.
4. WHILE a lecture is already marked as completed, THE Content_Viewer SHALL display the button in its "Completed" state as disabled when the lecture is loaded.
5. IF the completion request to the Progress_API fails, THEN THE Content_Viewer SHALL re-enable the "Mark as Complete" button and display an error message indicating the completion was not saved.

### Requirement 3: Auto-Complete on Video Advance

**User Story:** As a learner, I want the current video lecture to be automatically marked as completed when the player advances to the next lecture, so that I do not need to manually mark videos I fully watched.

#### Acceptance Criteria

1. WHEN the Video_Player countdown reaches zero and triggers navigation to the next lecture, THE Video_Player SHALL send a completion request to the Progress_API for the lecture that just ended before initiating navigation to the next lecture.
2. WHEN the user clicks the "Play now" button during the countdown, THE Video_Player SHALL send a completion request to the Progress_API for the lecture that just ended before initiating navigation to the next lecture.
3. IF the user cancels the countdown, THEN THE Video_Player SHALL NOT send a completion request for the current lecture.
4. IF the completion request to the Progress_API fails, THEN THE Video_Player SHALL still proceed with navigation to the next lecture without blocking the user.
5. IF the current lecture is the last lecture in the course and no next lecture exists, THEN THE Video_Player SHALL NOT display the auto-advance countdown overlay.

### Requirement 4: Display Course Progress on Course List

**User Story:** As a learner, I want to see my completion percentage for each course on the home page, so that I can quickly gauge my overall progress.

#### Acceptance Criteria

1. THE Course_List_Page SHALL display the Course_Progress_Percentage as a numeric whole-number percentage (e.g., "45%") for each course alongside the existing module and lecture counts.
2. IF no lectures have been completed for a course, THEN THE Course_List_Page SHALL display 0% as the progress for that course.
3. THE Progress_API SHALL provide a batch endpoint that returns a mapping of course identifiers to their respective Course_Progress_Percentage values for all courses in a single request.
4. WHEN the user navigates to the Course_List_Page, THE Course_List_Page SHALL fetch progress data from the batch endpoint and display the current Course_Progress_Percentage for each course.
5. IF the batch progress endpoint returns an error or is unavailable, THEN THE Course_List_Page SHALL display 0% for all courses and show an error message indicating that progress data could not be loaded.

### Requirement 5: Display Course Progress on Course Detail

**User Story:** As a learner, I want to see my progress percentage on the course detail page and see which lectures are completed in the sidebar, so that I know what I have covered and what remains.

#### Acceptance Criteria

1. THE Course_Detail_Page SHALL display the Course_Progress_Percentage in a visible location above the content viewer area.
2. THE Course_Detail_Page sidebar SHALL display a completion indicator (checkmark icon) next to each completed lecture title.
3. WHEN a lecture is marked as completed while viewing the course, THE Course_Detail_Page SHALL update the sidebar indicator and progress percentage within 1 second without requiring a full page reload.
4. WHEN the Course_Detail_Page loads, THE Progress_API SHALL return the set of completed lecture IDs for that course so the sidebar can render indicators immediately.

### Requirement 6: Calculate Course Progress Percentage

**User Story:** As a learner, I want progress calculated as the ratio of completed lectures to total lectures, so that the percentage accurately reflects my progress through the course content.

#### Acceptance Criteria

1. THE Progress_Service SHALL calculate Course_Progress_Percentage as: (number of completed lectures / total number of lectures in the course) × 100, rounded down to the nearest integer.
2. WHEN a course contains zero lectures, THE Progress_Service SHALL return 0 as the Course_Progress_Percentage.
3. THE Progress_Service SHALL return a Course_Progress_Percentage value between 0 and 100 inclusive.
4. THE Progress_Service SHALL count all lectures across all modules and sections of a course when computing the total, counting only Lecture_Progress records that belong to lectures within that course.
5. IF a progress calculation is requested for a course ID that does not exist, THEN THE Progress_Service SHALL return an error response indicating the course was not found.
