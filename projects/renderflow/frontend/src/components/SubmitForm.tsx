import { useState } from "react";
import { api, type JobType } from "../api/client";

const JOB_TYPES: { value: JobType; label: string; params: string }[] = [
  { value: "transcode", label: "Transcode", params: '{ "height": 720 }' },
  { value: "thumbnail", label: "Thumbnail", params: '{ "timestamp": "00:00:01" }' },
  { value: "audio_extract", label: "Audio extract", params: '{ "format": "mp3" }' },
  { value: "metadata", label: "Metadata", params: "{}" },
];

export function SubmitForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [jobType, setJobType] = useState<JobType>("transcode");
  const [inputUri, setInputUri] = useState("file://samples/demo.mp4");
  const [priority, setPriority] = useState(0);
  const [paramsText, setParamsText] = useState(JOB_TYPES[0].params);
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(
    null,
  );

  function onTypeChange(value: JobType) {
    setJobType(value);
    const preset = JOB_TYPES.find((t) => t.value === value);
    if (preset) setParamsText(preset.params);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      let params: Record<string, unknown> = {};
      if (paramsText.trim()) params = JSON.parse(paramsText);
      const job = await api.submitJob({
        job_type: jobType,
        input_uri: inputUri,
        params,
        priority,
        idempotency_key: idempotencyKey.trim() || null,
      });
      setMessage({ kind: "ok", text: `Submitted job ${job.id.slice(0, 8)} (${job.status})` });
      onSubmitted();
    } catch (err) {
      setMessage({
        kind: "err",
        text: err instanceof Error ? err.message : "Submit failed",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card submit-form" onSubmit={submit}>
      <h2>Submit job</h2>
      <div className="form-row">
        <label>
          Job type
          <select value={jobType} onChange={(e) => onTypeChange(e.target.value as JobType)}>
            {JOB_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
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
      </div>
      <label>
        Input URI
        <input
          type="text"
          value={inputUri}
          onChange={(e) => setInputUri(e.target.value)}
          placeholder="file://... , https://... , or s3://bucket/key"
          required
        />
      </label>
      <label>
        Params (JSON)
        <textarea
          rows={3}
          value={paramsText}
          onChange={(e) => setParamsText(e.target.value)}
          spellCheck={false}
        />
      </label>
      <label>
        Idempotency key (optional)
        <input
          type="text"
          value={idempotencyKey}
          onChange={(e) => setIdempotencyKey(e.target.value)}
          placeholder="dedupe repeated submissions"
        />
      </label>
      <button type="submit" className="btn btn-primary" disabled={busy}>
        {busy ? "Submitting…" : "Submit job"}
      </button>
      {message && (
        <p className={message.kind === "ok" ? "msg-ok" : "msg-err"}>{message.text}</p>
      )}
    </form>
  );
}
