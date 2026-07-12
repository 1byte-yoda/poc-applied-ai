import { Link } from "react-router-dom";
import { useCourses } from "../hooks/useCourses";

export function CourseList() {
  const { data: courses, isLoading, error } = useCourses();

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
          Failed to load courses
        </h2>
        <p className="mt-2 text-red-600">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Courses</h1>
      {courses && courses.length === 0 && (
        <p className="text-gray-500">No courses available yet.</p>
      )}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {courses?.map((course) => (
          <Link
            key={course.id}
            to={`/courses/${course.id}`}
            className="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {course.title}
            </h2>
            {course.description && (
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                {course.description}
              </p>
            )}
            <div className="flex gap-4 text-sm text-gray-500">
              <span>{course.module_count} modules</span>
              <span>{course.lecture_count} lectures</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
