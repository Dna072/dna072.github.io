import { useState } from 'react';

import FilterBar from './components/FilterBar';
import KpiCards from './components/KpiCards';
import TopVideosTable from './components/TopVideosTable';
import DeviceChart from './components/charts/DeviceChart';
import FunnelChart from './components/charts/FunnelChart';
import GeoChart from './components/charts/GeoChart';
import ViewsChart from './components/charts/ViewsChart';
import { EmptyState, Panel, QueryBoundary } from './components/states';
import { useAuth } from './context/AuthContext';
import {
  useDeviceBreakdown,
  useFunnel,
  useGeoBreakdown,
  useOverview,
  useTimeSeries,
  useVideoPerformance,
} from './lib/queries';
import type { AnalyticsFilters } from './lib/types';

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

type Metric = 'views' | 'watch_hours' | 'unique_viewers';
type SortKey = 'views' | 'watch_hours' | 'engagement_rate' | 'completion_rate';

const PAGE_SIZE = 8;

export default function Dashboard() {
  const { logout } = useAuth();

  const [filters, setFilters] = useState<AnalyticsFilters>({
    startDate: isoDaysAgo(30),
    endDate: new Date().toISOString().slice(0, 10),
    compare: false,
    videoId: null,
  });

  const [metric, setMetric] = useState<Metric>('views');
  const [sortBy, setSortBy] = useState<SortKey>('views');
  const [page, setPage] = useState(0);

  const overview = useOverview(filters);
  const timeseries = useTimeSeries(filters);
  const geo = useGeoBreakdown(filters);
  const device = useDeviceBreakdown(filters);
  const funnel = useFunnel(filters);
  const videos = useVideoPerformance(filters, {
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    sortBy,
  });

  function updateFilters(next: AnalyticsFilters) {
    setPage(0);
    setFilters(next);
  }

  function handleSort(key: SortKey) {
    setPage(0);
    setSortBy(key);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">S</span>
          <div>
            StreamPulse
            <small>Video Analytics</small>
          </div>
        </div>
        <div className="topbar-right">
          <span className="demo-banner">Synthetic demo data</span>
          <button className="btn ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="container">
        <FilterBar filters={filters} onChange={updateFilters} />

        {/* KPI row */}
        <QueryBoundary query={overview} loadingHeight={128}>
          {(data) => <KpiCards data={data} />}
        </QueryBoundary>

        <div className="grid">
          {/* Time series */}
          <Panel
            className="col-8"
            title="Performance over time"
            subtitle={`Aggregated server-side${
              filters.compare ? ' · dashed = previous period' : ''
            }`}
            right={
              <select value={metric} onChange={(e) => setMetric(e.target.value as Metric)}>
                <option value="views">Views</option>
                <option value="watch_hours">Watch hours</option>
                <option value="unique_viewers">Unique viewers</option>
              </select>
            }
          >
            <QueryBoundary
              query={timeseries}
              loadingHeight={300}
              isEmpty={(d) => d.points.length === 0}
            >
              {(data) => <ViewsChart data={data} metric={metric} />}
            </QueryBoundary>
          </Panel>

          {/* Engagement funnel */}
          <Panel
            className="col-4"
            title="Engagement funnel"
            subtitle="Impressions → views → retention"
          >
            <QueryBoundary
              query={funnel}
              loadingHeight={300}
              isEmpty={(d) => d.stages.every((s) => s.count === 0)}
            >
              {(data) => <FunnelChart data={data} />}
            </QueryBoundary>
          </Panel>

          {/* Devices */}
          <Panel className="col-4" title="Devices" subtitle="Views by device type">
            <QueryBoundary
              query={device}
              loadingHeight={260}
              isEmpty={(d) => d.rows.length === 0}
            >
              {(data) => <DeviceChart data={data} />}
            </QueryBoundary>
          </Panel>

          {/* Geo */}
          <Panel className="col-8" title="Top countries" subtitle="Views by viewer country">
            <QueryBoundary
              query={geo}
              loadingHeight={260}
              isEmpty={(d) => d.rows.length === 0}
            >
              {(data) => <GeoChart data={data} />}
            </QueryBoundary>
          </Panel>

          {/* Top videos */}
          <Panel
            className="col-12"
            title="Video performance"
            subtitle="Click a column header to sort"
          >
            <QueryBoundary query={videos} loadingHeight={320}>
              {(data) =>
                data.items.length === 0 ? (
                  <EmptyState message="No videos received views in this range." />
                ) : (
                  <TopVideosTable
                    data={data}
                    sortBy={sortBy}
                    onSort={handleSort}
                    page={page}
                    onPage={setPage}
                  />
                )
              }
            </QueryBoundary>
          </Panel>
        </div>

        <footer
          style={{
            textAlign: 'center',
            color: 'var(--text-dim)',
            fontSize: 12,
            padding: '28px 0 12px',
          }}
        >
          StreamPulse · portfolio project · all data is synthetic and generated by a seed
          script.
        </footer>
      </main>
    </div>
  );
}
