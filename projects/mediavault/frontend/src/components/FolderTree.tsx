import { useState } from "react";
import type { FolderNode } from "../api/types";
import { Icon } from "../lib/icons";

interface Props {
  nodes: FolderNode[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

export function FolderTree({ nodes, selectedId, onSelect }: Props) {
  return (
    <div className="folder-tree">
      <div
        className={`folder-row ${selectedId === null ? "active" : ""}`}
        onClick={() => onSelect(null)}
      >
        <Icon.Library size={15} />
        <span>All assets</span>
      </div>
      {nodes.map((node) => (
        <FolderRow key={node.id} node={node} depth={0} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </div>
  );
}

function FolderRow({
  node,
  depth,
  selectedId,
  onSelect,
}: {
  node: FolderNode;
  depth: number;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}) {
  const [open, setOpen] = useState(depth < 1);
  const hasChildren = node.children.length > 0;

  return (
    <>
      <div
        className={`folder-row ${selectedId === node.id ? "active" : ""}`}
        style={{ paddingLeft: 8 + depth * 14 }}
        onClick={() => onSelect(node.id)}
      >
        <span
          onClick={(e) => {
            e.stopPropagation();
            if (hasChildren) setOpen((o) => !o);
          }}
          style={{ display: "grid", placeItems: "center", width: 14 }}
        >
          {hasChildren ? (
            <Icon.Chevron size={13} className={`folder-caret ${open ? "open" : ""}`} />
          ) : (
            <span style={{ width: 13 }} />
          )}
        </span>
        <Icon.Folder size={15} />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {node.name}
        </span>
        {node.asset_count > 0 && <span className="count">{node.asset_count}</span>}
      </div>
      {open &&
        node.children.map((child) => (
          <FolderRow
            key={child.id}
            node={child}
            depth={depth + 1}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}
