import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { tagApi, workspaceApi } from "../api/resources";
import type { Role } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { EmptyState, LoadingState } from "../components/States";
import { Modal } from "../components/Modal";
import { useToast } from "../components/Toast";
import { initials } from "../lib/format";
import { Icon } from "../lib/icons";

const ROLES: Role[] = ["ADMIN", "MEMBER", "VIEWER"];

export function MembersPage() {
  const { user } = useAuth();
  const { currentId, current } = useWorkspace();
  const wsId = currentId!;
  const qc = useQueryClient();
  const toast = useToast();
  const isAdmin = current?.role === "ADMIN";

  const [invite, setInvite] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("MEMBER");

  const { data: members, isLoading } = useQuery({
    queryKey: ["members", wsId],
    queryFn: () => workspaceApi.members(wsId),
  });

  const addMember = useMutation({
    mutationFn: () => workspaceApi.addMember(wsId, email.trim(), role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members", wsId] });
      setInvite(false);
      setEmail("");
      toast.success("Member added");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const changeRole = useMutation({
    mutationFn: ({ membershipId, newRole }: { membershipId: string; newRole: Role }) =>
      workspaceApi.updateMemberRole(wsId, membershipId, newRole),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members", wsId] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const removeMember = useMutation({
    mutationFn: (membershipId: string) => workspaceApi.removeMember(wsId, membershipId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members", wsId] });
      toast.success("Member removed");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="main">
      <div className="topbar">
        <h1 style={{ fontSize: 18, margin: 0 }}>People &amp; permissions</h1>
        <div className="spacer" />
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setInvite(true)}>
            <Icon.Plus size={16} /> Add member
          </button>
        )}
      </div>

      <div className="content">
        {isLoading ? (
          <LoadingState label="Loading members…" />
        ) : !members || members.length === 0 ? (
          <EmptyState title="No members yet" glyph={<Icon.Users size={26} />} />
        ) : (
          <div className="card" style={{ overflow: "hidden", maxWidth: 820 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Role</th>
                  <th style={{ width: 60 }} />
                </tr>
              </thead>
              <tbody>
                {members.map((m) => {
                  const isOwner = m.user.id === current?.owner_id;
                  const isSelf = m.user.id === user?.id;
                  return (
                    <tr key={m.id} style={{ cursor: "default" }}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
                          <span className="avatar">{initials(m.user.full_name, m.user.email)}</span>
                          <div>
                            <div style={{ fontWeight: 600 }}>
                              {m.user.full_name || m.user.email}
                              {isOwner && (
                                <span className="badge" style={{ marginLeft: 8 }}>
                                  Owner
                                </span>
                              )}
                              {isSelf && <span className="muted" style={{ marginLeft: 6, fontSize: 12 }}>(you)</span>}
                            </div>
                            <div className="muted" style={{ fontSize: 12 }}>
                              {m.user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        {isAdmin && !isOwner ? (
                          <select
                            className="select"
                            style={{ width: 130 }}
                            value={m.role}
                            onChange={(e) =>
                              changeRole.mutate({ membershipId: m.id, newRole: e.target.value as Role })
                            }
                          >
                            {ROLES.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <span className={`badge badge-role-${m.role}`}>{m.role}</span>
                        )}
                      </td>
                      <td>
                        {isAdmin && !isOwner && (
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => {
                              if (confirm(`Remove ${m.user.email}?`)) removeMember.mutate(m.id);
                            }}
                            aria-label="Remove member"
                          >
                            <Icon.Trash size={15} />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <TagManager wsId={wsId} canManage={current?.role !== "VIEWER"} />
      </div>

      {invite && (
        <Modal
          title="Add a member"
          onClose={() => setInvite(false)}
          footer={
            <>
              <button className="btn" onClick={() => setInvite(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={!email.trim() || addMember.isPending}
                onClick={() => addMember.mutate()}
              >
                Add member
              </button>
            </>
          }
        >
          <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
            The person must already have a MediaVault account.
          </p>
          <div className="field">
            <label htmlFor="member-email">Email</label>
            <input
              id="member-email"
              className="input"
              type="email"
              value={email}
              autoFocus
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teammate@studio.com"
            />
          </div>
          <div className="field">
            <label htmlFor="member-role">Role</label>
            <select
              id="member-role"
              className="select"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r} — {r === "ADMIN" ? "full control" : r === "MEMBER" ? "upload & organize" : "read only"}
                </option>
              ))}
            </select>
          </div>
        </Modal>
      )}
    </div>
  );
}

function TagManager({ wsId, canManage }: { wsId: string; canManage: boolean }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [name, setName] = useState("");
  const [color, setColor] = useState("#0f766e");

  const { data: tags = [] } = useQuery({ queryKey: ["tags", wsId], queryFn: () => tagApi.list(wsId) });

  const createTag = useMutation({
    mutationFn: () => tagApi.create(wsId, name.trim(), color),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tags", wsId] });
      setName("");
      toast.success("Tag created");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const removeTag = useMutation({
    mutationFn: (id: string) => tagApi.remove(wsId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags", wsId] }),
  });

  return (
    <div style={{ maxWidth: 820, marginTop: 28 }}>
      <div className="content-header">
        <h1 style={{ fontSize: 16 }}>Tags</h1>
      </div>
      {canManage && (
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          <input type="color" value={color} onChange={(e) => setColor(e.target.value)} style={{ width: 42, height: 38, border: "1px solid var(--border)", borderRadius: 7, background: "none" }} />
          <input
            className="input"
            style={{ maxWidth: 240 }}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New tag name"
            onKeyDown={(e) => e.key === "Enter" && name.trim() && createTag.mutate()}
          />
          <button className="btn btn-primary" disabled={!name.trim() || createTag.isPending} onClick={() => createTag.mutate()}>
            Add tag
          </button>
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {tags.length === 0 && <span className="muted" style={{ fontSize: 13 }}>No tags yet.</span>}
        {tags.map((tag) => (
          <span key={tag.id} className="tag-chip" style={{ padding: "5px 10px" }}>
            <span className="tag-dot" style={{ background: tag.color }} />
            {tag.name}
            {canManage && (
              <button
                className="btn btn-ghost btn-sm"
                style={{ padding: 0, marginLeft: 2 }}
                onClick={() => removeTag.mutate(tag.id)}
                aria-label={`Delete ${tag.name}`}
              >
                <Icon.Close size={13} />
              </button>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
