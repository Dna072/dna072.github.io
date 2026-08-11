import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from '../components/StatusBadge';

describe('StatusBadge', () => {
  it('renders the status label with the matching class', () => {
    const { container } = render(<StatusBadge status="ready" />);
    expect(screen.getByText('ready')).toBeInTheDocument();
    expect(container.querySelector('.badge-ready')).not.toBeNull();
  });
});
