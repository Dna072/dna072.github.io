import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { VideoCard } from './VideoCard';
import type { VideoListItem } from '@/types';

const video: VideoListItem = {
  id: 'v1',
  project_id: 'p1',
  title: 'Launch Keynote',
  status: 'completed',
  duration_seconds: 125,
  thumbnail_path: null,
  tags: ['demo', 'launch'],
  created_at: new Date().toISOString(),
};

function renderCard(v: VideoListItem) {
  return render(
    <MemoryRouter>
      <VideoCard video={v} />
    </MemoryRouter>,
  );
}

describe('VideoCard', () => {
  it('shows title, duration and status', () => {
    renderCard(video);
    expect(screen.getByText('Launch Keynote')).toBeInTheDocument();
    expect(screen.getByText('2:05')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders up to three tags', () => {
    renderCard({ ...video, tags: ['a', 'b', 'c', 'd'] });
    expect(screen.getByText('a')).toBeInTheDocument();
    expect(screen.queryByText('d')).not.toBeInTheDocument();
  });

  it('links to the video detail page', () => {
    renderCard(video);
    expect(screen.getByRole('link')).toHaveAttribute('href', '/videos/v1');
  });
});
