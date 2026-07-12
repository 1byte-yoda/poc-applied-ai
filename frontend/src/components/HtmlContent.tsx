import { useLectureContent } from "../hooks/useLectureContent";

interface HtmlContentProps {
  lectureId: number;
  title: string;
}

export function HtmlContent({ lectureId, title }: HtmlContentProps) {
  const { data: html, isLoading, error } = useLectureContent(lectureId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">Failed to load content</p>
          <p className="text-red-600 text-sm mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">{title}</h2>
      <div
        className="flex-1 prose prose-sm max-w-none overflow-auto bg-white p-6 rounded-lg border border-gray-200"
        dangerouslySetInnerHTML={{ __html: html ?? "" }}
      />
    </div>
  );
}
