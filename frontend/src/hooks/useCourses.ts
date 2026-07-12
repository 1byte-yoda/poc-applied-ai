import { useQuery } from "@tanstack/react-query";
import { getCourses } from "../api/client";
import type { Course } from "../types";

export function useCourses() {
  return useQuery<Course[], Error>({
    queryKey: ["courses"],
    queryFn: getCourses,
  });
}
