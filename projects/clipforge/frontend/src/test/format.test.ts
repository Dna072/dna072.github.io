import { describe, expect, it } from 'vitest';
import { formatBytes, formatDuration, timeAgo } from '../utils/format';

describe('formatBytes', () => {
  it('formats byte counts', () => {
    expect(formatBytes(0)).toBe('0 B');
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(1024)).toBe('1.0 KB');
    expect(formatBytes(1024 * 1024)).toBe('1.0 MB');
    expect(formatBytes(5 * 1024 * 1024 * 1024)).toBe('5.0 GB');
  });
});

describe('formatDuration', () => {
  it('formats seconds into mm:ss / h:mm:ss', () => {
    expect(formatDuration(null)).toBe('—');
    expect(formatDuration(0)).toBe('—');
    expect(formatDuration(65)).toBe('1:05');
    expect(formatDuration(3661)).toBe('1:01:01');
  });
});

describe('timeAgo', () => {
  it('returns relative time', () => {
    expect(timeAgo(new Date().toISOString())).toBe('just now');
    const twoHoursAgo = new Date(Date.now() - 2 * 3600 * 1000).toISOString();
    expect(timeAgo(twoHoursAgo)).toBe('2h ago');
  });
});
