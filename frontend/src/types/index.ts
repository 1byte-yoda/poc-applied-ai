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

/** Module card for specialization detail page. */
export interface ModuleListItem {
  id: number;
  title: string;
  order: number;
  section_count: number;
  lecture_count: number;
}

/** Section card for module detail page. */
export interface SectionListItem {
  id: number;
  title: string;
  order: number;
  lecture_count: number;
}

/** Section detail for content viewer. */
export interface SectionDetail {
  id: number;
  title: string;
  module_id: number;
  module_title: string;
  course_id: number;
  course_title: string;
  lectures: Lecture[];
}
