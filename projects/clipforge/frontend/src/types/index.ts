export type VideoStatus = 'uploaded' | 'queued' | 'processing' | 'completed' | 'failed';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  workspace_id: string;
  created_at: string;
}

export interface Chapter {
  start: number;
  title: string;
}

export interface Video {
  id: string;
  project_id: string;
  title: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: VideoStatus;
  error_message: string | null;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  codec: string | null;
  frame_rate: number | null;
  bitrate: number | null;
  thumbnail_path: string | null;
  audio_path: string | null;
  transcript: string | null;
  summary: string | null;
  chapters: Chapter[] | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface VideoListItem {
  id: string;
  project_id: string;
  title: string;
  status: VideoStatus;
  duration_seconds: number | null;
  thumbnail_path: string | null;
  tags: string[] | null;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobStep {
  name: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped';
  detail: string | null;
}

export interface Job {
  id: string;
  video_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  attempts: number;
  max_attempts: number;
  steps: JobStep[] | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface DashboardStats {
  total_videos: number;
  total_projects: number;
  total_duration_seconds: number;
  total_storage_bytes: number;
  status_breakdown: StatusCount[];
  recent_videos: VideoListItem[];
}
