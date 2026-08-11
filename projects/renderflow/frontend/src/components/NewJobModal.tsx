import { useState, type FormEvent } from 'react'
import { JOB_TYPES, type JobCreate, type JobType } from '../types'

interface NewJobModalProps {
  onClose: () => void
  onSubmit: (payload: JobCreate) => Promise<void>
}

const PARAM_HINTS: Record<JobType, string> = {
  transcode: '{"codec": "libx264", "resolution": "1280:720"}',
  thumbnail: '{"timestamp_seconds": 5}',
  audio_extract: '{"format": "mp3"}',
  metadata: '{}',
}

export function NewJobModal({ onClose, onSubmit }: NewJobModalProps) {
  const [jobType, setJobType] = useState<JobType>('transcode')
  const [inputUri, setInputUri] = useState('')
  const [priority, setPriority] = useState(5)
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [paramsText, setParamsText] = useState(PARAM_HINTS.transcode)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    let params: Record<string, unknown> = {}
    if (paramsText.trim()) {
      try {
        params = JSON.parse(paramsText)
      } catch {
        setError('Params must be valid JSON')
        return
      }
    }

    setSubmitting(true)
    try {
      await onSubmit({
        job_type: jobType,
        input_uri: inputUri,
        priority,
        params,
        idempotency_key: idempotencyKey || undefined,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <form className="drawer" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="drawer-header">
          <h2>Submit a job</h2>
          <button type="button" className="btn-small btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>

        <label className="field">
          <span>Job type</span>
          <select
            value={jobType}
            onChange={(e) => {
              const next = e.target.value as JobType
              setJobType(next)
              setParamsText(PARAM_HINTS[next])
            }}
          >
            {JOB_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Input URI</span>
          <input
            required
            placeholder="s3://bucket/key.mp4 or file:///data/in.mp4"
            value={inputUri}
            onChange={(e) => setInputUri(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Priority (0–10)</span>
          <input
            type="number"
            min={0}
            max={10}
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
          />
        </label>

        <label className="field">
          <span>Idempotency key (optional)</span>
          <input
            placeholder="e.g. request id from the calling system"
            value={idempotencyKey}
            onChange={(e) => setIdempotencyKey(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Params (JSON)</span>
          <textarea rows={4} value={paramsText} onChange={(e) => setParamsText(e.target.value)} />
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="drawer-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit job'}
          </button>
        </div>
      </form>
    </div>
  )
}
