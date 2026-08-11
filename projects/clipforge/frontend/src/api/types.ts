export type VideoStatus =
  | 'uploaded'
  | 'queued'
  | 'processing'
  | 'ready'
  | 'failed';

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export type JobStage =
  | 'queued'
  | 'probe'
  | 'thumbnail'
  | 'audio'
  | 'transcript'
  | 'ai_analysis'
  | 'persist'
  | 'done';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface Video {
  id: string;
  workspace_id: string;
  title: string;
  description: string | null;
  status: VideoStatus;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  thumbnail_path: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface VideoDetail extends Video {
  transcript: string | null;
  summary: string | null;
  chapters: Chapter[] | null;
  error_message: string | null;
}

export interface Chapter {
  title: string;
  start: number;
  end: number;
}

export interface Job {
  id: string;
  video_id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  attempts: number;
  stage_history: Record<string, unknown>[] | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
  video_count: number;
}

export interface StatusBreakdown {
  uploaded: number;
  queued: number;
  processing: number;
  ready: number;
  failed: number;
}

export interface DashboardStats {
  total_videos: number;
  total_workspaces: number;
  total_duration_seconds: number;
  total_storage_bytes: number;
  status_breakdown: StatusBreakdown;
  active_jobs: number;
  recent_videos: Video[];
  top_tags: { tag: string; count: number }[];
}

export interface VideoUploadResponse {
  video: Video;
  job_id: string;
}

export interface ApiError {
  detail: string | { msg: string }[];
}
