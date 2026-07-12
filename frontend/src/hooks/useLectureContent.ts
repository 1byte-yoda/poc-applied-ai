import { useQuery } from "@tanstack/react-query";
import { getLectureHtmlContent } from "../api/client";

export function useLectureContent(lectureId: number | null) {
  return useQuery<string, Error>({
    queryKey: ["lectureContent", lectureId],
    queryFn: () => getLectureHtmlContent(lectureId!),
    enabled: lectureId !== null && lectureId > 0,
  });
}
