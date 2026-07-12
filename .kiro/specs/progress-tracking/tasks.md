# Implementation Plan: Progress Tracking

## Overview

This plan implements lecture completion tracking across the full stack: a new database table and Alembic migration, a progress service with business logic, FastAPI endpoints, a React custom hook via @tanstack/react-query, and updates to existing frontend components (ContentViewer, VideoPlayer, Sidebar, CourseList, CourseDetail). Tasks are ordered so each step builds on the previous, with property-based and unit tests close to the code they verify.

## Tasks

- [x] 1. Create the database model and migration
  - [x] 1.1 Create the LectureProgress SQLAlchemy model
    - Create `backend/app/models/lecture_progress.py` with the `LectureProgress` class as specified in the design (id, lecture_id with UNIQUE + FK, completed_at with server_default)
    - Register the model in `backend/app/models/__init__.py`
    - _Requirements: 1.1, 1.2_

  - [x] 1.2 Create the Alembic migration for lecture_progress table
    - Generate a new migration file in `backend/alembic/versions/` that creates the `lecture_progress` table with the unique constraint and index on `lecture_id`
    - Ensure ON DELETE CASCADE on the lecture_id foreign key
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. Implement the Progress Service
  - [x] 2.1 Create the ProgressService class
    - Create `backend/app/services/progress_service.py` with `ProgressService` class
    - Implement `mark_lecture_complete(lecture_id)` using INSERT ... ON CONFLICT DO NOTHING for idempotency
    - Implement `get_course_progress(course_id)` joining through modules → sections → lectures → lecture_progress
    - Implement `get_batch_progress()` returning {course_id: percentage} for all courses
    - Implement `calculate_percentage(completed, total)` as a pure function: `floor(completed/total*100)` when total > 0, else 0
    - Raise appropriate domain exceptions for non-existent lectures/courses
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 2.2 Write property test: Idempotent Completion
    - **Property 1: Idempotent Completion**
    - Generate random valid lecture IDs, call `mark_lecture_complete` 1–5 times, assert exactly one DB record exists and all responses return the same `lecture_id` and `completed_at`
    - Use Hypothesis with `@settings(max_examples=100)`
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 2.3 Write property test: Non-existent Lecture Rejection
    - **Property 2: Non-existent Lecture Rejection**
    - Generate random integers not present in the lectures table, call `mark_lecture_complete`, assert raises LectureNotFoundError and no record is created
    - Use Hypothesis with `@settings(max_examples=100)`
    - **Validates: Requirements 1.5**

  - [ ]* 2.4 Write property test: Progress Percentage Correctness
    - **Property 3: Progress Percentage Correctness**
    - Generate random (completed, total) pairs with `0 <= completed <= total <= 1000`, call `calculate_percentage`, assert result matches `floor(completed/total*100)` or 0 when total=0, and is in [0, 100]
    - Use Hypothesis with `@settings(max_examples=100)`
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [ ]* 2.5 Write property test: Course-Isolated Progress
    - **Property 4: Course-Isolated Progress**
    - Generate a multi-course fixture (2–5 courses, 1–20 lectures each, random completions), call `get_course_progress` for each course, assert each course's count only includes its own lectures
    - Use Hypothesis with `@settings(max_examples=100)`
    - **Validates: Requirements 4.3, 6.4**

- [ ] 3. Implement the Progress API Router
  - [x] 3.1 Create the progress router with all endpoints
    - Create `backend/app/routers/progress.py` with:
      - `POST /api/progress/lectures/{lecture_id}/complete` → returns 200 with {lecture_id, completed_at}, 404 if not found, 503 on DB failure
      - `GET /api/progress/courses/{course_id}` → returns 200 with {course_id, percentage, completed_count, total_count, completed_lecture_ids}, 404 if not found
      - `GET /api/progress/courses` → returns 200 with {progress: {course_id: percentage}}
    - Add `Retry-After: 30` header on 503 responses
    - Register the router in `backend/app/main.py`
    - _Requirements: 1.3, 1.5, 1.6, 4.3, 5.4_

  - [x] 3.2 Create Pydantic response schemas
    - Create `backend/app/schemas/progress.py` with `LectureCompleteResponse`, `CourseProgressResponse`, and `BatchProgressResponse` models
    - _Requirements: 1.3, 4.3, 5.4_

  - [ ]* 3.3 Write unit tests for the progress router
    - Test happy path mark complete (200), duplicate mark complete returns existing (200), invalid lecture (404), course progress (200), batch progress (200), DB failure (503 + Retry-After header)
    - _Requirements: 1.1, 1.3, 1.5, 1.6, 4.3, 5.4, 6.5_

- [x] 4. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Create the useProgress hook (Frontend)
  - [x] 5.1 Create progress API client functions
    - Create `frontend/src/api/progress.ts` with functions: `markLectureComplete(lectureId)`, `fetchCourseProgress(courseId)`, `fetchBatchProgress()`
    - _Requirements: 2.2, 4.4, 5.4_

  - [x] 5.2 Create the useProgress hooks
    - Create `frontend/src/hooks/useProgress.ts` with:
      - `useCourseProgress(courseId)` — react-query hook for single course progress
      - `useBatchProgress()` — react-query hook for all courses progress
      - `useMarkComplete()` — mutation hook with optimistic update (adds lecture ID to completed set, recalculates percentage) and rollback on error
    - Invalidate course progress queries on successful mutation
    - _Requirements: 2.2, 2.3, 4.4, 5.3, 5.4_

- [x] 6. Update ContentViewer with Mark as Complete button
  - [x] 6.1 Add Mark as Complete button to ContentViewer
    - Update `frontend/src/components/ContentViewer.tsx` to accept `isCompleted` and `onMarkComplete` props
    - Render button states: "Mark as Complete" (idle) → spinner (loading) → "Completed ✓" (done)
    - Disable button while mutation is in-flight or lecture is already complete
    - Show inline error toast if mutation fails, re-enable button
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 7. Update VideoPlayer with auto-complete logic
  - [x] 7.1 Add auto-complete callback to VideoPlayer
    - Update `frontend/src/components/VideoPlayer.tsx` to accept `onAutoComplete` callback prop
    - Call `onAutoComplete()` when countdown reaches zero (before `onEnded`)
    - Call `onAutoComplete()` when "Play now" is clicked (before `onEnded`)
    - Do NOT call `onAutoComplete()` when countdown is cancelled
    - Fire-and-forget: do not block navigation on API response
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 8. Update Sidebar with completion indicators
  - [ ] 8.1 Add checkmark indicators to Sidebar
    - Update `frontend/src/components/Sidebar.tsx` to accept `completedLectureIds: Set<number>` prop
    - Render a green checkmark (✓) next to each completed lecture title
    - Use subtle styling that doesn't interfere with active-lecture highlight
    - _Requirements: 5.2_

- [ ] 9. Update CourseList and CourseDetail pages
  - [x] 9.1 Add progress display to CourseList page
    - Update `frontend/src/pages/CourseList.tsx` to use `useBatchProgress()` hook
    - Display percentage next to each course card alongside existing module/lecture counts
    - Show 0% for all courses if the batch endpoint fails, with subtle error banner
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [x] 9.2 Add progress display and wire hooks in CourseDetail page
    - Update `frontend/src/pages/CourseDetail.tsx` to use `useCourseProgress(courseId)` and `useMarkComplete()` hooks
    - Display progress percentage above content viewer area
    - Pass `completedLectureIds` set to Sidebar component
    - Pass `isCompleted` and `onMarkComplete` to ContentViewer
    - Pass `onAutoComplete` to VideoPlayer
    - Ensure reactive updates within 1 second after mark-complete without full page reload
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The backend uses Hypothesis for property-based testing (already in test dependencies)
- Frontend tests can use vitest + @testing-library/react (standard for the project stack)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "3.1", "3.2"] },
    { "id": 3, "tasks": ["3.3", "5.1"] },
    { "id": 4, "tasks": ["5.2"] },
    { "id": 5, "tasks": ["6.1", "7.1", "8.1"] },
    { "id": 6, "tasks": ["9.1", "9.2"] }
  ]
}
```
