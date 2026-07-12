import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useCourseDetail } from "../hooks/useCourseDetail";
import { useCourseProgress, useMarkComplete } from "../hooks/useProgress";
import { Sidebar } from "../components/Sidebar";
import { ContentViewer } from "../components/ContentViewer";
import type { Lecture, Module } from "../types";

/** Flatten all lectures from the nested module/section structure into a single ordered list. */
function flattenLectures(modules: Module[]): Lecture[] {
  const lectures: Lecture[] = [];
  for (const mod of modules) {
    for (const section of mod.sections) {
      for (const lecture of section.lectures) {
        lectures.push(lecture);
      }
    }
  }
  return lectures;
}

export function CourseDetail() {
  const { courseId } = useParams<{ courseId: string }>();
  const numericCourseId = Number(courseId);
  const { data: course, isLoading, error } = useCourseDetail(numericCourseId);
  const {
    data: progressData,
    error: progressError,
  } = useCourseProgress(numericCourseId);
  const {
    mutate: markComplete,
    isPending: isMarkingComplete,
    error: markCompleteError,
  } = useMarkComplete(numericCourseId);

  const [activeLecture, setActiveLecture] = useState<Lecture | null>(null);

  // Flat list of all lectures in order for next/prev navigation
  const allLectures = useMemo(
    () => (course ? flattenLectures(course.modules) : []),
    [course]
  );

  const activeIndex = useMemo(
    () =>
      activeLecture
        ? allLectures.findIndex((l) => l.id === activeLecture.id)
        : -1,
    [activeLecture, allLectures]
  );

  const prevLecture = activeIndex > 0 ? allLectures[activeIndex - 1] : null;
  const nextLecture =
    activeIndex >= 0 && activeIndex < allLectures.length - 1
      ? allLectures[activeIndex + 1]
      : null;

  // Derive completed lecture IDs as a Set for Sidebar
  const completedLectureIds = useMemo(
    () => new Set(progressData?.completed_lecture_ids ?? []),
    [progressData]
  );

  // Check if active lecture is completed
  const isActiveLectureCompleted = activeLecture
    ? completedLectureIds.has(activeLecture.id)
    : false;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-red-50 border border-red-200 rounded-lg">
        <h2 className="text-lg font-semibold text-red-800">
          Failed to load course
        </h2>
        <p className="mt-2 text-red-600">{error.message}</p>
        <Link
          to="/"
          className="mt-4 inline-block text-indigo-600 hover:underline"
        >
          ← Back to courses
        </Link>
      </div>
    );
  }

  if (!course) return null;

  return (
    <div className="flex h-[calc(100vh-64px)]">
      <Sidebar
        modules={course.modules}
        activeLectureId={activeLecture?.id ?? null}
        onSelectLecture={setActiveLecture}
        completedLectureIds={completedLectureIds}
      />
      <main className="flex-1 overflow-auto bg-gray-50 flex flex-col">
        {/* Progress bar above content area */}
        <div className="px-6 py-3 bg-white border-b border-gray-200 flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <div className="flex-1 max-w-xs bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-indigo-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressData?.percentage ?? 0}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700">
            {progressData?.percentage ?? 0}%
          </span>
          {progressError && (
            <span className="text-xs text-yellow-600 ml-2">
              (progress unavailable)
            </span>
          )}
        </div>

        <div className="flex-1 min-h-0">
          {activeLecture ? (
            <ContentViewer
              lecture={activeLecture}
              onPrev={
                prevLecture ? () => setActiveLecture(prevLecture) : undefined
              }
              onNext={
                nextLecture ? () => setActiveLecture(nextLecture) : undefined
              }
              nextLectureTitle={nextLecture?.title ?? null}
              isCompleted={isActiveLectureCompleted}
              onMarkComplete={() => markComplete(activeLecture.id)}
              onAutoComplete={
                activeLecture
                  ? () => markComplete(activeLecture.id)
                  : undefined
              }
              isMarkingComplete={isMarkingComplete}
              markCompleteError={markCompleteError}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                {course.title}
              </h2>
              {course.description && (
                <p className="text-gray-600 mb-4">{course.description}</p>
              )}
              <p>Select a lecture from the sidebar to begin.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
