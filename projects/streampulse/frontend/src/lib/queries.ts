import { useQuery } from '@tanstack/react-query';

import { api } from './api';
import type {
  AnalyticsFilters,
  BreakdownResponse,
  DataBounds,
  FunnelResponse,
  OverviewMetrics,
  TimeSeriesResponse,
  VideoOut,
  VideoPerformancePage,
} from './types';

// Build the query params shared by every analytics endpoint.
function baseParams(f: AnalyticsFilters): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = {
    start_date: f.startDate,
    end_date: f.endDate,
    compare: f.compare,
  };
  if (f.videoId != null) params.video_id = f.videoId;
  return params;
}

// A stable key fragment so React Query caches per filter combination.
function filterKey(f: AnalyticsFilters) {
  return [f.startDate, f.endDate, f.compare, f.videoId] as const;
}

export function useOverview(f: AnalyticsFilters) {
  return useQuery({
    queryKey: ['overview', ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<OverviewMetrics>('/api/v1/analytics/overview', {
        params: baseParams(f),
      });
      return data;
    },
  });
}

export function useTimeSeries(f: AnalyticsFilters, granularity = 'auto') {
  return useQuery({
    queryKey: ['timeseries', granularity, ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<TimeSeriesResponse>('/api/v1/analytics/timeseries', {
        params: { ...baseParams(f), granularity },
      });
      return data;
    },
  });
}

export function useVideoPerformance(
  f: AnalyticsFilters,
  opts: { limit: number; offset: number; sortBy: string },
) {
  return useQuery({
    queryKey: ['videos', opts.limit, opts.offset, opts.sortBy, ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<VideoPerformancePage>('/api/v1/analytics/videos', {
        params: {
          ...baseParams(f),
          limit: opts.limit,
          offset: opts.offset,
          sort_by: opts.sortBy,
        },
      });
      return data;
    },
  });
}

export function useGeoBreakdown(f: AnalyticsFilters) {
  return useQuery({
    queryKey: ['geo', ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<BreakdownResponse>('/api/v1/analytics/audience/geo', {
        params: { ...baseParams(f), limit: 8 },
      });
      return data;
    },
  });
}

export function useDeviceBreakdown(f: AnalyticsFilters) {
  return useQuery({
    queryKey: ['device', ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<BreakdownResponse>(
        '/api/v1/analytics/audience/device',
        { params: baseParams(f) },
      );
      return data;
    },
  });
}

export function useFunnel(f: AnalyticsFilters) {
  return useQuery({
    queryKey: ['funnel', ...filterKey(f)],
    queryFn: async () => {
      const { data } = await api.get<FunnelResponse>('/api/v1/analytics/funnel', {
        params: baseParams(f),
      });
      return data;
    },
  });
}

export function useVideoCatalog() {
  return useQuery({
    queryKey: ['catalog'],
    queryFn: async () => {
      const { data } = await api.get<VideoOut[]>('/api/v1/analytics/videos/catalog');
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useDataBounds() {
  return useQuery({
    queryKey: ['bounds'],
    queryFn: async () => {
      const { data } = await api.get<DataBounds>('/api/v1/analytics/meta/bounds');
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
