import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { JobType } from '../types'

const JOB_TYPES: JobType[] = ['transcode', 'thumbnail', 'audio_extract', 'metadata']

export function SubmitJobPage() {
  const navigate = useNavigate()
  const [jobType, setJobType] = useState<JobType>('transcode')
  const [inputUri, setInputUri] = useState('')
  const [priority, setPriority] = useState(5)
  const [maxRetries, setMaxRetries] = useState(3)
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [paramsJson, setParamsJson] = useState('{}')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    let parsedParams: Record<string, unknown>
    try {
      parsedParams = JSON.parse(paramsJson) as Record<string, unknown>
    } catch {
      setError('Params must be valid JSON')
      setSubmitting(false)
      return
    }

    try {
      const job = await api.createJob({
        job_type: jobType,
        input_uri: inputUri,
        priority,
        max_retries: maxRetries,
        idempotency_key: idempotencyKey || undefined,
        params: parsedParams,
      })
      navigate(`/jobs/${job.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submit failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Submit job</h1>
          <p className="page-subtitle">Enqueue a new media processing task</p>
        </div>
      </header>

      <section className="panel panel-form">
        <form onSubmit={handleSubmit} className="form">
          <label>
            Job type
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value as JobType)}
              required
            >
              {JOB_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label>
            Input URI
            <input
              type="text"
              value={inputUri}
              onChange={(e) => setInputUri(e.target.value)}
              placeholder="s3://bucket/video.mp4"
              required
            />
          </label>

          <div className="form-row">
            <label>
              Priority (0–10)
              <input
                type="number"
                min={0}
                max={10}
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
              />
            </label>
            <label>
              Max retries
              <input
                type="number"
                min={0}
                max={10}
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
              />
            </label>
          </div>

          <label>
            Idempotency key (optional)
            <input
              type="text"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              placeholder="unique-client-key"
            />
          </label>

          <label>
            Params (JSON)
            <textarea
              value={paramsJson}
              onChange={(e) => setParamsJson(e.target.value)}
              rows={4}
              spellCheck={false}
            />
          </label>

          {error && <div className="alert alert-error">{error}</div>}

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit job'}
          </button>
        </form>
      </section>
    </div>
  )
}
