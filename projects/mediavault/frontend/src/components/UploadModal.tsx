import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { assetApi } from "../api/resources";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { formatBytes } from "../lib/format";
import { Icon } from "../lib/icons";
import { Modal } from "./Modal";
import { Spinner } from "./States";
import { useToast } from "./Toast";

interface Props {
  folderId: string | null;
  onClose: () => void;
}

export function UploadModal({ folderId, onClose }: Props) {
  const { currentId } = useWorkspace();
  const wsId = currentId!;
  const qc = useQueryClient();
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [description, setDescription] = useState("");

  const upload = useMutation({
    mutationFn: async () => {
      for (const file of files) {
        const form = new FormData();
        form.append("file", file);
        form.append("name", file.name);
        if (description) form.append("description", description);
        if (folderId) form.append("folder_id", folderId);
        await assetApi.upload(wsId, form);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets", wsId] });
      qc.invalidateQueries({ queryKey: ["folders", wsId] });
      toast.success(`Uploaded ${files.length} file${files.length > 1 ? "s" : ""}`);
      onClose();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const addFiles = (list: FileList | null) => {
    if (list) setFiles((prev) => [...prev, ...Array.from(list)]);
  };

  return (
    <Modal
      title="Upload assets"
      onClose={onClose}
      footer={
        <>
          <button className="btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            disabled={files.length === 0 || upload.isPending}
            onClick={() => upload.mutate()}
          >
            {upload.isPending ? <Spinner /> : <Icon.Upload size={16} />}
            Upload {files.length > 0 ? `(${files.length})` : ""}
          </button>
        </>
      }
    >
      <div
        className={`dropzone ${dragging ? "drag" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
      >
        <Icon.Upload size={28} style={{ marginBottom: 8 }} />
        <div style={{ fontWeight: 600, color: "var(--text)" }}>
          Drop files here or click to browse
        </div>
        <div style={{ fontSize: 12, marginTop: 4 }}>Video, image and PDF up to 512 MB</div>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 6 }}>
          {files.map((file, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 10px",
                borderRadius: 7,
                background: "var(--surface-2)",
              }}
            >
              <Icon.File size={16} />
              <span style={{ flex: 1, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {file.name}
              </span>
              <span className="muted" style={{ fontSize: 12 }}>
                {formatBytes(file.size)}
              </span>
              <button
                className="btn btn-ghost btn-sm"
                style={{ padding: 2 }}
                onClick={() => setFiles((f) => f.filter((_, idx) => idx !== i))}
                aria-label="Remove"
              >
                <Icon.Close size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="field" style={{ marginTop: 14, marginBottom: 0 }}>
        <label htmlFor="upload-desc">Description (optional)</label>
        <textarea
          id="upload-desc"
          className="textarea"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add context that will apply to these uploads"
        />
      </div>
    </Modal>
  );
}
