import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useCourseDetail } from "../hooks/useCourseDetail";
import { Sidebar } from "../components/Sidebar";
import { ContentViewer } from "../components/ContentViewer";
import type { Lecture } from "../types";

export function CourseDetail() {
  const { courseId } = useParams<{ courseId: string }>();
  const { data: course, isLoading, error } = useCourseDetail(Number(courseId));
  const [activeLecture, setActiveLecture] = useState<Lecture | null>(null);

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
          <ContentViewer lecture={activeLecture} />
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
