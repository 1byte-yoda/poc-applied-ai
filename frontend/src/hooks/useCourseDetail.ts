import { useQuery } from "@tanstack/react-query";
import { getCourseDetail } from "../api/client";
import type { CourseDetail } from "../types";

export function useCourseDetail(courseId: number) {
  return useQuery<CourseDetail, Error>({
    queryKey: ["course", courseId],
    queryFn: () => getCourseDetail(courseId),
    enabled: courseId > 0,
  });
}
