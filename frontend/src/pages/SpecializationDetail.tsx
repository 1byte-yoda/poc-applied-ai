import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getModulesForCourse, getCourses } from "../api/client";

export function SpecializationDetail() {
  const { courseId } = useParams<{ courseId: string }>();
  const id = Number(courseId);

  const { data: modules, isLoading, error } = useQuery({
    queryKey: ["modules", id],
    queryFn: () => getModulesForCourse(id),
    enabled: id > 0,
  });

  const { data: courses } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
  });

  const courseName = courses?.find((c) => c.id === id)?.title ?? "Specialization";

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
          Failed to load modules
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

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link to="/" className="hover:text-indigo-600">
          Home
        </Link>
        <span className="mx-2">›</span>
        <span className="text-gray-900">{courseName}</span>
      </nav>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">{courseName}</h1>

      {modules && modules.length === 0 && (
        <p className="text-gray-500">No modules available yet.</p>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {modules?.map((mod) => (
          <Link
            key={mod.id}
            to={`/specializations/${courseId}/modules/${mod.id}`}
            className="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {mod.title}
            </h2>
            <div className="flex gap-4 text-sm text-gray-500">
              <span>{mod.section_count} courses</span>
              <span>{mod.lecture_count} lectures</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
