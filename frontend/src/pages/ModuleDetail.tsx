import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getSectionsForModule, getModulesForCourse, getCourses } from "../api/client";

export function ModuleDetail() {
  const { courseId, moduleId } = useParams<{
    courseId: string;
    moduleId: string;
  }>();
  const numCourseId = Number(courseId);
  const numModuleId = Number(moduleId);

  const { data: sections, isLoading, error } = useQuery({
    queryKey: ["sections", numModuleId],
    queryFn: () => getSectionsForModule(numModuleId),
    enabled: numModuleId > 0,
  });

  const { data: courses } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
  });

  const { data: modules } = useQuery({
    queryKey: ["modules", numCourseId],
    queryFn: () => getModulesForCourse(numCourseId),
    enabled: numCourseId > 0,
  });

  const courseName =
    courses?.find((c) => c.id === numCourseId)?.title ?? "Specialization";
  const moduleName =
    modules?.find((m) => m.id === numModuleId)?.title ?? "Module";

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
          Failed to load sections
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
        <Link
          to={`/specializations/${courseId}`}
          className="hover:text-indigo-600"
        >
          {courseName}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-gray-900">{moduleName}</span>
      </nav>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">{moduleName}</h1>

      {sections && sections.length === 0 && (
        <p className="text-gray-500">No sections available yet.</p>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {sections?.map((section) => (
          <Link
            key={section.id}
            to={`/courses/${section.id}`}
            className="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {section.title}
            </h2>
            <div className="text-sm text-gray-500">
              <span>{section.lecture_count} lectures</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
