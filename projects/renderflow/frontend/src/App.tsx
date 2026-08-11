import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { JobsPage } from './pages/JobsPage'
import { SubmitJobPage } from './pages/SubmitJobPage'
import { FailedJobsPage } from './pages/FailedJobsPage'
import { WorkersPage } from './pages/WorkersPage'
import { JobDetailPage } from './pages/JobDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="jobs/:id" element={<JobDetailPage />} />
          <Route path="submit" element={<SubmitJobPage />} />
          <Route path="failed" element={<FailedJobsPage />} />
          <Route path="workers" element={<WorkersPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
