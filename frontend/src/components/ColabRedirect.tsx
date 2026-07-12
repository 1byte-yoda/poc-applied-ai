import { useEffect } from "react";

interface ColabRedirectProps {
  colabUrl: string;
  title: string;
}

export function ColabRedirect({ colabUrl, title }: ColabRedirectProps) {
  useEffect(() => {
    if (colabUrl) {
      window.open(colabUrl, "_blank", "noopener,noreferrer");
    }
  }, [colabUrl]);

  if (!colabUrl) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-8 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800 font-medium">
            Colab URL not configured
          </p>
          <p className="text-yellow-600 text-sm mt-1">
            No Google Colab link is available for this notebook.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="text-center p-8 bg-green-50 border border-green-200 rounded-lg">
        <h2 className="text-lg font-semibold text-green-800 mb-2">{title}</h2>
        <p className="text-green-700 mb-4">
          Opening notebook in Google Colab...
        </p>
        <a
          href={colabUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          Open in Colab ↗
        </a>
      </div>
    </div>
  );
}
