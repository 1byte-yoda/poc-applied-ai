import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  markLectureComplete,
  unmarkLectureComplete,
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
      await queryClient.cancelQueries({
        queryKey: ["courseProgress", courseId],
      });

      const previous = queryClient.getQueryData<CourseProgressResponse>([
        "courseProgress",
        courseId,
      ]);

      if (previous) {
        const alreadyCompleted =
          previous.completed_lecture_ids.includes(lectureId);
        if (!alreadyCompleted) {
          const newCompleted = previous.completed_count + 1;
          const newPercentage =
            previous.total_count > 0
              ? Math.max(1, Math.floor((newCompleted / previous.total_count) * 100))
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
      if (context?.previous) {
        queryClient.setQueryData(
          ["courseProgress", courseId],
          context.previous
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["courseProgress", courseId],
      });
      queryClient.invalidateQueries({ queryKey: ["batchProgress"] });
    },
  });
}

/** Mutation hook for unmarking a lecture as complete (toggle back). */
export function useUnmarkComplete(courseId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (lectureId: number) => unmarkLectureComplete(lectureId),
    onMutate: async (lectureId: number) => {
      await queryClient.cancelQueries({
        queryKey: ["courseProgress", courseId],
      });

      const previous = queryClient.getQueryData<CourseProgressResponse>([
        "courseProgress",
        courseId,
      ]);

      if (previous) {
        const newCompletedIds = previous.completed_lecture_ids.filter(
          (id) => id !== lectureId
        );
        const newCompleted = newCompletedIds.length;
        const newPercentage =
          previous.total_count > 0
            ? newCompleted > 0
              ? Math.max(1, Math.floor((newCompleted / previous.total_count) * 100))
              : 0
            : 0;
        queryClient.setQueryData<CourseProgressResponse>(
          ["courseProgress", courseId],
          {
            ...previous,
            completed_count: newCompleted,
            percentage: newPercentage,
            completed_lecture_ids: newCompletedIds,
          }
        );
      }

      return { previous };
    },
    onError: (_err, _lectureId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(
          ["courseProgress", courseId],
          context.previous
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["courseProgress", courseId],
      });
      queryClient.invalidateQueries({ queryKey: ["batchProgress"] });
    },
  });
}
