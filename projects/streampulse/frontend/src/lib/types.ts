// Types mirror the FastAPI Pydantic schemas (app/schemas/analytics.py).

export interface MetricDelta {
  value: number;
  previous: number | null;
  delta_pct: number | null;
}

export interface OverviewMetrics {
  total_views: MetricDelta;
  unique_viewers: MetricDelta;
  total_watch_hours: MetricDelta;
  avg_view_duration_seconds: MetricDelta;
  engagement_rate: MetricDelta;
  completion_rate: MetricDelta;
  comparison_enabled: boolean;
}

export interface TimeSeriesPoint {
  bucket: string;
  views: number;
  watch_hours: number;
  unique_viewers: number;
}

export interface TimeSeriesResponse {
  granularity: string;
  points: TimeSeriesPoint[];
  previous_points: TimeSeriesPoint[] | null;
}

export interface VideoPerformance {
  video_id: number;
  title: string;
  category: string;
  views: number;
  watch_hours: number;
  avg_view_duration_seconds: number;
  engagement_rate: number;
  completion_rate: number;
}

export interface VideoPerformancePage {
  items: VideoPerformance[];
  total: number;
  limit: number;
  offset: number;
}

export interface BreakdownRow {
  key: string;
  label: string;
  views: number;
  watch_hours: number;
  share: number;
}

export interface BreakdownResponse {
  dimension: string;
  rows: BreakdownRow[];
}

export interface FunnelStage {
  stage: string;
  count: number;
  pct_of_top: number;
}

export interface FunnelResponse {
  stages: FunnelStage[];
}

export interface VideoOut {
  id: number;
  title: string;
  category: string;
  duration_seconds: number;
  published_at: string;
  thumbnail_url: string | null;
}

export interface DataBounds {
  min_date: string | null;
  max_date: string | null;
}

export interface AnalyticsFilters {
  startDate: string;
  endDate: string;
  compare: boolean;
  videoId: number | null;
}
