import { useCallback, useMemo, useState } from "react";
import Header from "../components/Header";
import FiltersBar from "../components/FiltersBar";
import KpiCard from "../components/KpiCard";
import Panel from "../components/Panel";
import TimeSeriesChart from "../components/TimeSeriesChart";
import FunnelChart from "../components/FunnelChart";
import DeviceChart from "../components/DeviceChart";
import GeoChart from "../components/GeoChart";
import ReferrerList from "../components/ReferrerList";
import TopVideosTable from "../components/TopVideosTable";
import { audienceApi, deviceApi, geoApi, metricsApi, videosApi } from "../api/client";
import { useAsyncData } from "../hooks/useAsyncData";
import type { DashboardFilters, SortField } from "../types";
import { daysAgoISO, formatCompactNumber, formatHours, formatPercent, todayISO } from "../utils/format";
import "./Dashboard.css";

const DEFAULT_FILTERS: DashboardFilters = {
  start: daysAgoISO(29),
  end: todayISO(),
  videoId: null,
  compare: false,
};

export default function Dashboard() {
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [sort, setSort] = useState<SortField>("views");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const rangeParams = useMemo(
    () => ({ start: filters.start, end: filters.end, videoId: filters.videoId, compare: filters.compare }),
    [filters]
  );

  const videosList = useAsyncData(() => videosApi.list(), []);

  const overview = useAsyncData(() => metricsApi.overview(rangeParams), [
    rangeParams.start,
    rangeParams.end,
    rangeParams.videoId,
    rangeParams.compare,
  ]);

  const timeseries = useAsyncData(() => metricsApi.timeseries(rangeParams), [
    rangeParams.start,
    rangeParams.end,
    rangeParams.videoId,
    rangeParams.compare,
  ]);

  const funnel = useAsyncData(
    () => audienceApi.funnel({ start: filters.start, end: filters.end, videoId: filters.videoId }),
    [filters.start, filters.end, filters.videoId]
  );

  const audience = useAsyncData(
    () => audienceApi.breakdown({ start: filters.start, end: filters.end, videoId: filters.videoId }),
    [filters.start, filters.end, filters.videoId]
  );

  const device = useAsyncData(
    () => deviceApi.breakdown({ start: filters.start, end: filters.end, videoId: filters.videoId }),
    [filters.start, filters.end, filters.videoId]
  );

  const geo = useAsyncData(
    () => geoApi.breakdown({ start: filters.start, end: filters.end, videoId: filters.videoId }),
    [filters.start, filters.end, filters.videoId]
  );

  const performance = useAsyncData(
    () =>
      videosApi.performance({
        start: filters.start,
        end: filters.end,
        videoId: filters.videoId,
        sort,
        order,
        limit: 8,
      }),
    [filters.start, filters.end, filters.videoId, sort, order]
  );

  const handleSortChange = useCallback(
    (field: SortField) => {
      if (field === sort) {
        setOrder((prev) => (prev === "desc" ? "asc" : "desc"));
      } else {
        setSort(field);
        setOrder("desc");
      }
    },
    [sort]
  );

  const kpis = overview.data?.current;
  const deltas = overview.data?.deltas;

  return (
    <div className="dashboard">
      <div className="dashboard__inner">
        <Header />
        <FiltersBar
          filters={filters}
          onChange={setFilters}
          videos={videosList.data ?? []}
          videosLoading={videosList.loading}
        />

        <section className="kpi-grid">
          {overview.loading ? (
            Array.from({ length: 6 }).map((_, i) => <div key={i} className="kpi-card kpi-card--skeleton" />)
          ) : overview.error ? (
            <div className="kpi-grid__error">
              <Panel title="Overview" error={overview.error} onRetry={overview.reload}>
                <div />
              </Panel>
            </div>
          ) : kpis ? (
            <>
              <KpiCard label="Total views" value={formatCompactNumber(kpis.views)} delta={deltas?.views} />
              <KpiCard label="Unique viewers" value={formatCompactNumber(kpis.unique_viewers)} delta={deltas?.unique_viewers} />
              <KpiCard label="Watch time" value={formatHours(kpis.watch_time_hours)} delta={deltas?.watch_time_hours} />
              <KpiCard label="Avg. watched" value={formatPercent(kpis.avg_watch_percent)} delta={deltas?.avg_watch_percent} />
              <KpiCard label="Completion rate" value={formatPercent(kpis.completion_rate)} delta={deltas?.completion_rate} />
              <KpiCard label="Engagement rate" value={formatPercent(kpis.engagement_rate)} delta={deltas?.engagement_rate} />
            </>
          ) : null}
        </section>

        <Panel
          title="Views &amp; watch time over time"
          subtitle={filters.compare ? "Dashed line shows the previous period, aligned by day offset" : undefined}
          loading={timeseries.loading}
          error={timeseries.error}
          onRetry={timeseries.reload}
          isEmpty={!!timeseries.data && timeseries.data.points.every((p) => p.views === 0)}
          emptyMessage="No views recorded in this date range."
          className="dashboard__timeseries"
        >
          {timeseries.data && (
            <TimeSeriesChart points={timeseries.data.points} comparePoints={timeseries.data.compare_points} />
          )}
        </Panel>

        <section className="dashboard__grid-2">
          <Panel
            title="Engagement funnel"
            subtitle="Play → 25% → 50% → 75% → complete"
            loading={funnel.loading}
            error={funnel.error}
            onRetry={funnel.reload}
            isEmpty={!!funnel.data && funnel.data.stages.every((s) => s.count === 0)}
          >
            {funnel.data && <FunnelChart stages={funnel.data.stages} />}
          </Panel>

          <Panel
            title="Device breakdown"
            subtitle="Views by device type"
            loading={device.loading}
            error={device.error}
            onRetry={device.reload}
            isEmpty={!!device.data && device.data.items.every((d) => d.views === 0)}
          >
            {device.data && <DeviceChart devices={device.data.items} />}
          </Panel>
        </section>

        <section className="dashboard__grid-2">
          <Panel
            title="Top countries"
            subtitle="Views by viewer location"
            loading={geo.loading}
            error={geo.error}
            onRetry={geo.reload}
            isEmpty={!!geo.data && geo.data.items.length === 0}
          >
            {geo.data && <GeoChart items={geo.data.items} />}
          </Panel>

          <Panel
            title="Traffic sources"
            subtitle="Share of views by referrer"
            loading={audience.loading}
            error={audience.error}
            onRetry={audience.reload}
            isEmpty={!!audience.data && audience.data.referrers.every((r) => r.views === 0)}
          >
            {audience.data && <ReferrerList referrers={audience.data.referrers} />}
          </Panel>
        </section>

        <Panel
          title="Top videos"
          subtitle="Ranked by the selected metric for this date range"
          loading={performance.loading}
          error={performance.error}
          onRetry={performance.reload}
          isEmpty={!!performance.data && performance.data.items.length === 0}
          emptyMessage="No video activity in this range."
        >
          {performance.data && (
            <TopVideosTable items={performance.data.items} sort={sort} order={order} onSortChange={handleSortChange} />
          )}
        </Panel>
      </div>
    </div>
  );
}
