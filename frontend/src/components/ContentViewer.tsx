import { useState } from "react";
import type { Lecture } from "../types";
import { VideoPlayer } from "./VideoPlayer";
import { PdfViewer } from "./PdfViewer";
import { HtmlContent } from "./HtmlContent";
import { ColabRedirect } from "./ColabRedirect";
import { NavigationBar } from "./NavigationBar";
import { getLectureContentUrl } from "../api/client";

interface ContentViewerProps {
  lecture: Lecture;
  onPrev?: () => void;
  onNext?: () => void;
  nextLectureTitle?: string | null;
  isCompleted?: boolean;
  onMarkComplete?: () => void;
  onAutoComplete?: () => void;
  isMarkingComplete?: boolean;
  markCompleteError?: Error | null;
}

export function ContentViewer({
  lecture,
  onPrev,
  onNext,
  nextLectureTitle,
  isCompleted = false,
  onMarkComplete,
  onAutoComplete,
  isMarkingComplete = false,
  markCompleteError,
}: ContentViewerProps) {
  const contentUrl = getLectureContentUrl(lecture.id);
  const [errorDismissed, setErrorDismissed] = useState(false);

  const renderContent = () => {
    switch (lecture.content_type) {
      case "mp4":
        return (
          <VideoPlayer
            src={contentUrl}
            title={lecture.title}
            onEnded={onNext}
            nextLectureTitle={nextLectureTitle}
            onAutoComplete={onAutoComplete}
          />
        );
      case "pdf":
        return <PdfViewer src={contentUrl} title={lecture.title} />;
      case "ipynb":
        return (
          <ColabRedirect
            colabUrl={lecture.colab_url ?? ""}
            title={lecture.title}
          />
        );
      case "docx":
      case "txt":
      case "html":
        return <HtmlContent lectureId={lecture.id} title={lecture.title} />;
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-8 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 font-medium">
                Unsupported content type
              </p>
              <p className="text-yellow-600 text-sm mt-1">
                Content type "{lecture.content_type}" is not supported for
                viewing.
              </p>
            </div>
          </div>
        );
    }
  };

  const renderMarkCompleteButton = () => {
    if (!onMarkComplete) return null;

    if (isCompleted) {
      return (
        <button
          disabled
          className="px-4 py-2 rounded-lg bg-green-600 text-white font-medium cursor-not-allowed flex items-center gap-2"
        >
          <span>✓</span>
          Completed
        </button>
      );
    }

    if (isMarkingComplete) {
      return (
        <button
          disabled
          className="px-4 py-2 rounded-lg border-2 border-green-600 text-green-700 font-medium cursor-not-allowed flex items-center gap-2"
        >
          <span className="animate-spin inline-block w-4 h-4 border-2 border-green-600 border-t-transparent rounded-full" />
          Marking...
        </button>
      );
    }

    return (
      <button
        onClick={() => {
          setErrorDismissed(false);
          onMarkComplete();
        }}
        className="px-4 py-2 rounded-lg border-2 border-green-600 text-green-700 font-medium hover:bg-green-50 transition-colors flex items-center gap-2"
      >
        Mark as Complete
      </button>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-auto">{renderContent()}</div>

      {/* Mark as Complete + Error */}
      {onMarkComplete && (
        <div className="px-4 py-3 border-t border-gray-200 bg-white flex items-center gap-4">
          {renderMarkCompleteButton()}
          {markCompleteError && !errorDismissed && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-1 rounded">
              <span>Failed to save completion. Please try again.</span>
              <button
                onClick={() => setErrorDismissed(true)}
                className="text-red-400 hover:text-red-600"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      )}

      <NavigationBar onPrev={onPrev} onNext={onNext} />
    </div>
  );
}
