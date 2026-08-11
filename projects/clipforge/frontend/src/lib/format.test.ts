import { describe, expect, it } from 'vitest';

import { formatBytes, formatDuration } from './format';

describe('formatDuration', () => {
  it('formats minutes and seconds', () => {
    expect(formatDuration(90)).toBe('1:30');
  });

  it('formats hours', () => {
    expect(formatDuration(3661)).toBe('1:01:01');
  });

  it('handles null', () => {
    expect(formatDuration(null)).toBe('--:--');
  });
});

describe('formatBytes', () => {
  it('formats megabytes', () => {
    expect(formatBytes(5 * 1024 * 1024)).toBe('5 MB');
  });

  it('formats gigabytes with decimals', () => {
    expect(formatBytes(1.5 * 1024 * 1024 * 1024)).toBe('1.5 GB');
  });

  it('handles zero', () => {
    expect(formatBytes(0)).toBe('0 B');
  });
});
