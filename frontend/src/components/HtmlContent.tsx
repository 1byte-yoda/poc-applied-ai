import { getLectureContentUrl } from "../api/client";

interface HtmlContentProps {
  lectureId: number;
  title: string;
}

export function HtmlContent({ lectureId, title }: HtmlContentProps) {
  const contentUrl = getLectureContentUrl(lectureId);

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-lg font-semibold text-gray-800 px-4 pt-4 pb-2">{title}</h2>
      <div className="flex-1 min-h-0 mx-4 mb-4">
        <iframe
          src={contentUrl}
          title={title}
          className="w-full h-full rounded-lg border border-gray-200 bg-white"
          sandbox="allow-same-origin"
        />
      </div>
    </div>
  );
}
