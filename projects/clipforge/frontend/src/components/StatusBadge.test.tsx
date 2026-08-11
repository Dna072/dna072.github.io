import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders the human label for a status', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('applies the status class', () => {
    const { container } = render(<StatusBadge status="processing" />);
    expect(container.querySelector('.badge.processing')).toBeTruthy();
  });
});
