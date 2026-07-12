import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getSectionDetail } from "../api/client";
import { useCourseProgress, useMarkComplete, useUnmarkComplete } from "../hooks/useProgress";
import { ContentViewer } from "../components/ContentViewer";
import type { Lecture } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export function SectionViewer() {
  const { sectionId } = useParams<{ sectionId: string }>();
  const id = Number(sectionId);

  const { data: section, isLoading, error } = useQuery({
    queryKey: ["section", id],
    queryFn: () => getSectionDetail(id),
    enabled: id > 0,
  });

  const courseId = section?.course_id ?? 0;

  const { data: progressData } = useCourseProgress(courseId);
  const { mutate: markComplete, isPending: isMarkingComplete, error: markCompleteError } =
    useMarkComplete(courseId);
  const { mutate: unmarkComplete, isPending: isUnmarking } =
    useUnmarkComplete(courseId);

  const [activeLecture, setActiveLecture] = useState<Lecture | null>(null);
  const [lastViewedRestored, setLastViewedRestored] = useState(false);

  const lectures = useMemo(() => section?.lectures ?? [], [section]);

  // Restore last viewed lecture on first load
  useEffect(() => {
    if (lastViewedRestored || !section || lectures.length === 0) return;

    fetch(`${BASE_URL}/api/progress/courses/${courseId}/last-viewed`)
      .then((res) => res.json())
      .then((data) => {
        if (data.lecture_id) {
          const found = lectures.find((l) => l.id === data.lecture_id);
          if (found) setActiveLecture(found);
        }
      })
      .catch(() => {})
      .finally(() => setLastViewedRestored(true));
  }, [section, lectures, courseId, lastViewedRestored]);

  const handleSelectLecture = useCallback(
    (lecture: Lecture) => {
      setActiveLecture(lecture);
      if (courseId > 0) {
        fetch(
          `${BASE_URL}/api/progress/courses/${courseId}/last-viewed?lecture_id=${lecture.id}`,
          { method: "PUT" }
        ).catch(() => {});
      }
    },
    [courseId]
  );

  const activeIndex = useMemo(
    () =>
      activeLecture ? lectures.findIndex((l) => l.id === activeLecture.id) : -1,
    [activeLecture, lectures]
  );

  const prevLecture = activeIndex > 0 ? lectures[activeIndex - 1] : null;
  const nextLecture =
    activeIndex >= 0 && activeIndex < lectures.length - 1
      ? lectures[activeIndex + 1]
      : null;

  const completedLectureIds = useMemo(
    () => new Set(progressData?.completed_lecture_ids ?? []),
    [progressData]
  );

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
          Failed to load section
        </h2>
        <p className="mt-2 text-red-600">{error.message}</p>
        <Link
          to="/"
          className="mt-4 inline-block text-indigo-600 hover:underline"
        >
          ← Back to home
        </Link>
      </div>
    );
  }

  if (!section) return null;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Breadcrumb */}
      <nav className="px-6 py-3 bg-white border-b border-gray-200 text-sm text-gray-500">
        <Link to="/" className="hover:text-indigo-600">
          Home
        </Link>
        <span className="mx-2">›</span>
        <Link
          to={`/specializations/${section.course_id}`}
          className="hover:text-indigo-600"
        >
          {section.course_title}
        </Link>
        <span className="mx-2">›</span>
        <Link
          to={`/specializations/${section.course_id}/modules/${section.module_id}`}
          className="hover:text-indigo-600"
        >
          {section.module_title}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-gray-900">{section.title}</span>
      </nav>

      <div className="flex flex-1 min-h-0">
        {/* Scoped sidebar - only this section's lectures */}
        <aside className="w-80 border-r bg-white overflow-y-auto">
          <div className="p-4">
            <h2 className="font-semibold text-gray-800 mb-3 text-[14px] leading-relaxed">
              {section.title}
            </h2>
            <ul className="space-y-0.5">
              {lectures.map((lecture) => (
                <li key={lecture.id}>
                  <button
                    onClick={() => handleSelectLecture(lecture)}
                    className={`w-full text-left text-[14px] leading-relaxed py-2 px-3 rounded transition-colors ${
                      activeLecture?.id === lecture.id
                        ? "bg-indigo-100 text-indigo-800 font-medium"
                        : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      {completedLectureIds.has(lecture.id) && (
                        <span className="text-green-600 text-xs">✓</span>
                      )}
                      <span className="truncate">{lecture.title}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Content area */}
        <main className="flex-1 overflow-auto bg-gray-50 flex flex-col">
          {/* Progress bar */}
          {progressData && (
            <div className="px-6 py-3 bg-white border-b border-gray-200 flex items-center gap-3">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <div className="flex-1 max-w-xs bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressData.percentage}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">
                {progressData.percentage}%
              </span>
              <span className="text-xs text-gray-500">
                ({progressData.completed_count}/{progressData.total_count})
              </span>
            </div>
          )}

          <div className="flex-1 min-h-0">
            {activeLecture ? (
              <ContentViewer
                lecture={activeLecture}
                onPrev={
                  prevLecture
                    ? () => handleSelectLecture(prevLecture)
                    : undefined
                }
                onNext={
                  nextLecture
                    ? () => handleSelectLecture(nextLecture)
                    : undefined
                }
                nextLectureTitle={nextLecture?.title ?? null}
                isCompleted={isActiveLectureCompleted}
                onMarkComplete={() => markComplete(activeLecture.id)}
                onUnmarkComplete={() => unmarkComplete(activeLecture.id)}
                onAutoComplete={
                  activeLecture
                    ? () => markComplete(activeLecture.id)
                    : undefined
                }
                isMarkingComplete={isMarkingComplete || isUnmarking}
                markCompleteError={markCompleteError}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                  {section.title}
                </h2>
                <p>Select a lecture from the sidebar to begin.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
