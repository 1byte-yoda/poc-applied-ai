import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  markLectureComplete,
  fetchCourseProgress,
  fetchBatchProgress,
  type CourseProgressResponse,
} from "../api/progress";

/** Hook for a specific course's progress (used in CourseDetail). */
export function useCourseProgress(courseId: number) {
  return useQuery<CourseProgressResponse, Error>({
    queryKey: ["courseProgress", courseId],
    queryFn: () => fetchCourseProgress(courseId),
    enabled: courseId > 0,
  });
}

/** Hook for batch progress across all courses (used in CourseList). */
export function useBatchProgress() {
  return useQuery({
    queryKey: ["batchProgress"],
    queryFn: fetchBatchProgress,
  });
}

/** Mutation hook for marking a lecture complete with optimistic update. */
export function useMarkComplete(courseId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (lectureId: number) => markLectureComplete(lectureId),
    onMutate: async (lectureId: number) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({
        queryKey: ["courseProgress", courseId],
      });

      // Snapshot previous value
      const previous = queryClient.getQueryData<CourseProgressResponse>([
        "courseProgress",
        courseId,
      ]);

      // Optimistically update the cache
      if (previous) {
        const alreadyCompleted =
          previous.completed_lecture_ids.includes(lectureId);
        if (!alreadyCompleted) {
          const newCompleted = previous.completed_count + 1;
          const newPercentage =
            previous.total_count > 0
              ? Math.floor((newCompleted / previous.total_count) * 100)
              : 0;
          queryClient.setQueryData<CourseProgressResponse>(
            ["courseProgress", courseId],
            {
              ...previous,
              completed_count: newCompleted,
              percentage: newPercentage,
              completed_lecture_ids: [
                ...previous.completed_lecture_ids,
                lectureId,
              ],
            }
          );
        }
      }

      return { previous };
    },
    onError: (_err, _lectureId, context) => {
      // Rollback on error
      if (context?.previous) {
        queryClient.setQueryData(
          ["courseProgress", courseId],
          context.previous
        );
      }
    },
    onSettled: () => {
      // Refetch to ensure server state
      queryClient.invalidateQueries({
        queryKey: ["courseProgress", courseId],
      });
      queryClient.invalidateQueries({ queryKey: ["batchProgress"] });
    },
  });
}
