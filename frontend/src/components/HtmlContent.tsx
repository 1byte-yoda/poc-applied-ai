import { getLectureContentUrl } from "../api/client";

interface HtmlContentProps {
  lectureId: number;
  title: string;
}

export function HtmlContent({ lectureId, title }: HtmlContentProps) {
  const contentUrl = getLectureContentUrl(lectureId);

  return (
    <div className="flex flex-col h-full p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">{title}</h2>
      <iframe
        src={contentUrl}
        title={title}
        className="flex-1 w-full rounded-lg border border-gray-200 bg-white"
        sandbox="allow-same-origin"
      />
    </div>
  );
}
