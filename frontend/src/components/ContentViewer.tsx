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
}

export function ContentViewer({ lecture, onPrev, onNext, nextLectureTitle }: ContentViewerProps) {
  const contentUrl = getLectureContentUrl(lecture.id);

  const renderContent = () => {
    switch (lecture.content_type) {
      case "mp4":
        return (
          <VideoPlayer
            src={contentUrl}
            title={lecture.title}
            onEnded={onNext}
            nextLectureTitle={nextLectureTitle}
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
                Content type "{lecture.content_type}" is not supported for viewing.
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto">{renderContent()}</div>
      <NavigationBar onPrev={onPrev} onNext={onNext} />
    </div>
  );
}
