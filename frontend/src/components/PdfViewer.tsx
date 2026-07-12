interface PdfViewerProps {
  src: string;
  title: string;
}

export function PdfViewer({ src, title }: PdfViewerProps) {
  return (
    <div className="flex flex-col h-full p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">{title}</h2>
      <iframe
        src={src}
        className="flex-1 w-full border border-gray-200 rounded-lg"
        title={`PDF: ${title}`}
      />
    </div>
  );
}
