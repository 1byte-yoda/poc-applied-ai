import { Routes, Route, Link } from "react-router-dom";
import { SpecializationList } from "./pages/SpecializationList";
import { SpecializationDetail } from "./pages/SpecializationDetail";
import { ModuleDetail } from "./pages/ModuleDetail";
import { SectionViewer } from "./pages/SectionViewer";
import { ErrorBoundary } from "./components/ErrorBoundary";

export function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 shadow-sm">
        <Link to="/" className="text-xl font-bold text-indigo-600">
          Learning Platform
        </Link>
      </header>
      <div className="flex-1">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<SpecializationList />} />
            <Route path="/specializations/:courseId" element={<SpecializationDetail />} />
            <Route path="/specializations/:courseId/modules/:moduleId" element={<ModuleDetail />} />
            <Route path="/courses/:sectionId" element={<SectionViewer />} />
          </Routes>
        </ErrorBoundary>
      </div>
    </div>
  );
}
