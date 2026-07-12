interface VideoPlayerProps {
  src: string;
  title: string;
}

export function VideoPlayer({ src, title }: VideoPlayerProps) {
  return (
    <div className="flex flex-col h-full p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">{title}</h2>
      <div className="flex-1 flex items-center justify-center bg-black rounded-lg overflow-hidden">
        <video
          controls
          className="max-w-full max-h-full"
          src={src}
          aria-label={`Video: ${title}`}
        >
          <track kind="captions" />
          Your browser does not support the video element.
        </video>
      </div>
    </div>
  );
}
