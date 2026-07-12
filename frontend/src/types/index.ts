/** Lecture within a section. */
export interface Lecture {
  id: number;
  title: string;
  order: number;
  content_type: string;
  file_path: string | null;
  colab_url: string | null;
  duration_seconds: number | null;
}

/** Section within a module. */
export interface Section {
  id: number;
  title: string;
  order: number;
  lectures: Lecture[];
}

/** Module within a course. */
export interface Module {
  id: number;
  title: string;
  order: number;
  sections: Section[];
}

/** Course summary (list view). */
export interface Course {
  id: number;
  title: string;
  description: string | null;
  module_count: number;
  lecture_count: number;
}

/** Course detail with full nested structure. */
export interface CourseDetail extends Course {
  modules: Module[];
}
