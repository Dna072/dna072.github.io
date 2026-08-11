export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DateRange {
  start: string;
  end: string;
  compare_start: string | null;
  compare_end: string | null;
}

export interface KPISet {
  views: number;
  unique_viewers: number;
  watch_time_hours: number;
  avg_watch_percent: number;
  completion_rate: number;
  likes: number;
  comments: number;
  shares: number;
  engagement_rate: number;
}

export interface KPIDelta {
  absolute: number;
  percent: number | null;
}

export interface OverviewResponse {
  range: DateRange;
  current: KPISet;
  previous: KPISet | null;
  deltas: Record<string, KPIDelta> | null;
}

export interface TimeSeriesPoint {
  date: string;
  views: number;
  unique_viewers: number;
  watch_time_hours: number;
  avg_watch_percent: number;
  completion_rate: number;
}

export interface TimeSeriesResponse {
  range: DateRange;
  points: TimeSeriesPoint[];
  compare_points: TimeSeriesPoint[] | null;
}

export interface VideoSummary {
  id: number;
  title: string;
  category: string;
  duration_seconds: number;
  thumbnail_url: string | null;
  published_at: string;
}

export interface VideoPerformance {
  video_id: number;
  title: string;
  category: string;
  thumbnail_url: string | null;
  published_at: string;
  views: number;
  unique_viewers: number;
  watch_time_hours: number;
  avg_watch_percent: number;
  completion_rate: number;
  likes: number;
  comments: number;
  shares: number;
}

export interface VideoPerformanceResponse {
  range: DateRange;
  total: number;
  items: VideoPerformance[];
}

export interface VideoDetailResponse {
  video: VideoSummary;
  range: DateRange;
  metrics: KPISet;
}

export interface FunnelStage {
  stage: string;
  label: string;
  count: number;
  percent_of_plays: number;
}

export interface FunnelResponse {
  range: DateRange;
  video_id: number | null;
  stages: FunnelStage[];
}

export interface DeviceBreakdown {
  device_type: string;
  views: number;
  watch_time_hours: number;
  share_percent: number;
}

export interface ReferrerBreakdown {
  referrer_source: string;
  views: number;
  share_percent: number;
}

export interface AudienceResponse {
  range: DateRange;
  devices: DeviceBreakdown[];
  referrers: ReferrerBreakdown[];
}

export interface GeoBreakdown {
  country_code: string;
  country_name: string;
  views: number;
  unique_viewers: number;
  watch_time_hours: number;
  share_percent: number;
}

export interface GeoResponse {
  range: DateRange;
  items: GeoBreakdown[];
}

export interface DeviceResponse {
  range: DateRange;
  items: DeviceBreakdown[];
}

export type SortField = "views" | "watch_time_hours" | "avg_watch_percent" | "completion_rate" | "unique_viewers";

export interface DashboardFilters {
  start: string;
  end: string;
  videoId: number | null;
  compare: boolean;
}
