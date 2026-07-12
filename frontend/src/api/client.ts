import type { Course, CourseDetail } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

/** Fetch all courses. */
export function getCourses(): Promise<Course[]> {
  return fetchJson<Course[]>("/api/courses");
}

/** Fetch course detail with full nested structure. */
export function getCourseDetail(courseId: number): Promise<CourseDetail> {
  return fetchJson<CourseDetail>(`/api/courses/${courseId}`);
}

/** Get the URL for streaming/fetching lecture content. */
export function getLectureContentUrl(lectureId: number): string {
  return `${BASE_URL}/api/lectures/${lectureId}/content`;
}

/** Fetch lecture HTML content (for docx/txt/html types). */
export async function getLectureHtmlContent(
  lectureId: number
): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/lectures/${lectureId}/content`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.text();
}
