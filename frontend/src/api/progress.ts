const BASE_URL = import.meta.env.VITE_API_URL || "";

export interface LectureCompleteResponse {
  lecture_id: number;
  completed_at: string;
}

export interface CourseProgressResponse {
  course_id: number;
  percentage: number;
  completed_count: number;
  total_count: number;
  completed_lecture_ids: number[];
}

export interface BatchProgressResponse {
  progress: Record<number, number>;
}

/** Mark a lecture as completed. Idempotent — safe to call multiple times. */
export async function markLectureComplete(
  lectureId: number
): Promise<LectureCompleteResponse> {
  const res = await fetch(
    `${BASE_URL}/api/progress/lectures/${lectureId}/complete`,
    { method: "POST" }
  );
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

/** Fetch progress for a single course including completed lecture IDs. */
export async function fetchCourseProgress(
  courseId: number
): Promise<CourseProgressResponse> {
  const res = await fetch(`${BASE_URL}/api/progress/courses/${courseId}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

/** Fetch progress percentages for all courses in a single request. */
export async function fetchBatchProgress(): Promise<BatchProgressResponse> {
  const res = await fetch(`${BASE_URL}/api/progress/courses`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

/** Unmark a lecture as complete (toggle back to incomplete). */
export async function unmarkLectureComplete(
  lectureId: number
): Promise<{ lecture_id: number; was_completed: boolean }> {
  const res = await fetch(
    `${BASE_URL}/api/progress/lectures/${lectureId}/complete`,
    { method: "DELETE" }
  );
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}
