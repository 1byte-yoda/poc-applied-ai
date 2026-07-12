import { useState } from "react";
import type { Module, Lecture } from "../types";

interface SidebarProps {
  modules: Module[];
  activeLectureId: number | null;
  onSelectLecture: (lecture: Lecture) => void;
  completedLectureIds?: Set<number>;
}

export function Sidebar({
  modules,
  activeLectureId,
  onSelectLecture,
  completedLectureIds,
}: SidebarProps) {
  const [expandedModules, setExpandedModules] = useState<Set<number>>(
    () => new Set(modules.map((m) => m.id))
  );
  const [expandedSections, setExpandedSections] = useState<Set<number>>(
    () => new Set(modules.flatMap((m) => m.sections.map((s) => s.id)))
  );

  const toggleModule = (moduleId: number) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleId)) next.delete(moduleId);
      else next.add(moduleId);
      return next;
    });
  };

  const toggleSection = (sectionId: number) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  return (
    <aside className="w-96 border-r border-gray-200 bg-white overflow-y-auto h-full">
      <nav className="p-5" aria-label="Course navigation">
        {modules.map((module) => (
          <div key={module.id} className="mb-3">
            <button
              onClick={() => toggleModule(module.id)}
              className="w-full flex items-center gap-2 text-left font-bold text-gray-900 text-base py-2.5 px-3 rounded-lg hover:bg-gray-100 transition-colors"
              aria-expanded={expandedModules.has(module.id)}
            >
              <span className="text-sm text-gray-400 shrink-0">
                {expandedModules.has(module.id) ? "▼" : "▶"}
              </span>
              <span className="truncate">{module.title}</span>
            </button>

            {expandedModules.has(module.id) && (
              <div className="ml-5 mt-1">
                {module.sections.map((section) => (
                  <div key={section.id} className="mb-1">
                    <button
                      onClick={() => toggleSection(section.id)}
                      className="w-full flex items-center gap-2 text-left text-[15px] font-semibold text-gray-700 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors"
                      aria-expanded={expandedSections.has(section.id)}
                    >
                      <span className="text-sm text-gray-400 shrink-0">
                        {expandedSections.has(section.id) ? "▼" : "▶"}
                      </span>
                      <span className="truncate">{section.title}</span>
                    </button>

                    {expandedSections.has(section.id) && (
                      <ul className="ml-5 mt-0.5">
                        {section.lectures.map((lecture) => (
                          <li key={lecture.id}>
                            <button
                              onClick={() => onSelectLecture(lecture)}
                              className={`w-full text-left text-[14px] leading-relaxed py-2 px-3 rounded-lg flex items-center gap-2 transition-colors ${
                                activeLectureId === lecture.id
                                  ? "bg-indigo-50 text-indigo-800 font-medium border border-indigo-200"
                                  : "text-gray-600 hover:bg-gray-50"
                              }`}
                            >
                              <span className="text-sm shrink-0">
                                {getContentIcon(lecture.content_type)}
                              </span>
                              <span className="truncate flex-1">
                                {lecture.title}
                              </span>
                              {completedLectureIds?.has(lecture.id) && (
                                <span
                                  className="text-green-500 text-sm shrink-0 ml-1"
                                  title="Completed"
                                >
                                  ✓
                                </span>
                              )}
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
}

function getContentIcon(contentType: string): string {
  switch (contentType) {
    case "mp4":
      return "🎬";
    case "pdf":
      return "📄";
    case "ipynb":
      return "📓";
    case "docx":
    case "txt":
    case "html":
      return "📝";
    case "mp3":
      return "🎵";
    case "png":
      return "🖼️";
    default:
      return "📁";
  }
}
