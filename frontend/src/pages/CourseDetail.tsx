import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useCourseDetail } from "../hooks/useCourseDetail";
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
  const { data: course, isLoading, error } = useCourseDetail(Number(courseId));
  const [activeLecture, setActiveLecture] = useState<Lecture | null>(null);

  // Flat list of all lectures in order for next/prev navigation
  const allLectures = useMemo(
    () => (course ? flattenLectures(course.modules) : []),
    [course]
  );

  const activeIndex = useMemo(
    () => (activeLecture ? allLectures.findIndex((l) => l.id === activeLecture.id) : -1),
    [activeLecture, allLectures]
  );

  const prevLecture = activeIndex > 0 ? allLectures[activeIndex - 1] : null;
  const nextLecture =
    activeIndex >= 0 && activeIndex < allLectures.length - 1
      ? allLectures[activeIndex + 1]
      : null;

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
        <Link to="/" className="mt-4 inline-block text-indigo-600 hover:underline">
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
      />
      <main className="flex-1 overflow-auto bg-gray-50">
        {activeLecture ? (
          <ContentViewer
            lecture={activeLecture}
            onPrev={prevLecture ? () => setActiveLecture(prevLecture) : undefined}
            onNext={nextLecture ? () => setActiveLecture(nextLecture) : undefined}
            nextLectureTitle={nextLecture?.title ?? null}
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
      </main>
    </div>
  );
}
