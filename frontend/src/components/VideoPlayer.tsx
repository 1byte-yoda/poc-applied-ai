import { useCallback, useEffect, useRef, useState } from "react";

interface VideoPlayerProps {
  src: string;
  title: string;
  onEnded?: () => void;
  nextLectureTitle?: string | null;
  onAutoComplete?: () => void;
}

/** Generate a localStorage key for saving playback position. */
function getStorageKey(src: string): string {
  return `video-progress:${src}`;
}

export function VideoPlayer({
  src,
  title,
  onEnded,
  nextLectureTitle,
  onAutoComplete,
}: VideoPlayerProps) {
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const saveIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cancelCountdown = useCallback(() => {
    setShowCountdown(false);
    setCountdown(5);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const handleVideoEnd = useCallback(() => {
    // Clear saved position when video completes
    localStorage.removeItem(getStorageKey(src));

    if (!onEnded) return;
    setShowCountdown(true);
    setCountdown(5);

    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          cancelCountdown();
          onAutoComplete?.();
          onEnded();
          return 5;
        }
        return prev - 1;
      });
    }, 1000);
  }, [src, onEnded, cancelCountdown, onAutoComplete]);

  // Restore playback position when video loads
  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const saved = localStorage.getItem(getStorageKey(src));
    if (saved) {
      const time = parseFloat(saved);
      // Only resume if not near the end (within 5 seconds of end = start over)
      if (!isNaN(time) && time > 0 && time < video.duration - 5) {
        video.currentTime = time;
      }
    }
  }, [src]);

  // Save playback position periodically (every 3 seconds)
  useEffect(() => {
    saveIntervalRef.current = setInterval(() => {
      const video = videoRef.current;
      if (video && !video.paused && video.currentTime > 0) {
        localStorage.setItem(
          getStorageKey(src),
          video.currentTime.toString()
        );
      }
    }, 3000);

    return () => {
      // Save final position on unmount
      const video = videoRef.current;
      if (video && video.currentTime > 0 && video.currentTime < video.duration - 5) {
        localStorage.setItem(
          getStorageKey(src),
          video.currentTime.toString()
        );
      }
      if (saveIntervalRef.current) {
        clearInterval(saveIntervalRef.current);
      }
    };
  }, [src]);

  // Clean up countdown timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Reset countdown when src changes (new lecture loaded)
  useEffect(() => {
    cancelCountdown();
  }, [src, cancelCountdown]);

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-lg font-semibold text-gray-800 px-4 pt-4 pb-2">{title}</h2>
      <div className="relative flex-1 flex items-center justify-center bg-black rounded-lg overflow-hidden mx-4 mb-4">
        <video
          ref={videoRef}
          controls
          autoPlay
          className="w-full h-full object-contain"
          src={src}
          onEnded={handleVideoEnd}
          onLoadedMetadata={handleLoadedMetadata}
          aria-label={`Video: ${title}`}
        >
          <track kind="captions" />
          Your browser does not support the video element.
        </video>

        {/* Auto-advance countdown overlay */}
        {showCountdown && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="text-center text-white">
              <p className="text-sm text-gray-300 mb-2">Up next</p>
              <p className="text-lg font-semibold mb-4 max-w-md px-4">
                {nextLectureTitle ?? "Next lecture"}
              </p>

              {/* Circular countdown */}
              <div className="relative inline-flex items-center justify-center mb-4">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    fill="none"
                    stroke="#374151"
                    strokeWidth="4"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="4"
                    strokeDasharray={2 * Math.PI * 36}
                    strokeDashoffset={2 * Math.PI * 36 * (1 - countdown / 5)}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-linear"
                  />
                </svg>
                <span className="absolute text-2xl font-bold">{countdown}</span>
              </div>

              <div className="flex gap-3 justify-center">
                <button
                  onClick={cancelCountdown}
                  className="px-4 py-2 rounded-lg border border-gray-500 text-gray-300 hover:bg-gray-700 transition-colors text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    cancelCountdown();
                    onAutoComplete?.();
                    onEnded?.();
                  }}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors text-sm"
                >
                  Play now
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
