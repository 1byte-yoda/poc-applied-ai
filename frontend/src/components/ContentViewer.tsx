import type { Lecture } from "../types";
import { VideoPlayer } from "./VideoPlayer";
import { PdfViewer } from "./PdfViewer";
import { HtmlContent } from "./HtmlContent";
import { ColabRedirect } from "./ColabRedirect";
import { getLectureContentUrl } from "../api/client";

interface ContentViewerProps {
  lecture: Lecture;
}

export function ContentViewer({ lecture }: ContentViewerProps) {
  const contentUrl = getLectureContentUrl(lecture.id);

  switch (lecture.content_type) {
    case "mp4":
      return <VideoPlayer src={contentUrl} title={lecture.title} />;
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
}
