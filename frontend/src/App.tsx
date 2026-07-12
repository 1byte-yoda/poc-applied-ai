import { Routes, Route, Link } from "react-router-dom";
import { CourseList } from "./pages/CourseList";
import { CourseDetail } from "./pages/CourseDetail";

export function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 shadow-sm">
        <Link to="/" className="text-xl font-bold text-indigo-600">
          Learning Platform
        </Link>
      </header>
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<CourseList />} />
          <Route path="/courses/:courseId" element={<CourseDetail />} />
        </Routes>
      </div>
    </div>
  );
}
