import {
  fetchDashboardStats,
  fetchVideo,
  fetchVideoJob,
  fetchVideos,
  fetchWorkspaces,
  uploadVideo,
} from './client';

export const dashboardApi = {
  stats: fetchDashboardStats,
};

export const videoApi = {
  list: fetchVideos,
  get: fetchVideo,
  job: fetchVideoJob,
  upload: uploadVideo,
};

export const workspaceApi = {
  list: fetchWorkspaces,
};

export * from './client';
