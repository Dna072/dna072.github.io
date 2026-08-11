import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { listFolders } from '@/api/folders'
import type { Folder } from '@/types'

interface FolderTreeNodeProps {
  workspaceId: string
  folder: Folder
  depth: number
}

export function FolderTreeNode({ workspaceId, folder, depth }: FolderTreeNodeProps) {
  const [expanded, setExpanded] = useState(false)
  const [searchParams] = useSearchParams()
  const isActive = searchParams.get('folder') === folder.id

  const childrenQuery = useQuery({
    queryKey: ['folders', workspaceId, folder.id],
    queryFn: () => listFolders(workspaceId, folder.id),
    enabled: expanded,
  })

  const hasChildren = folder.subfolder_count > 0

  return (
    <div>
      <div
        className="mv-flex mv-items-center mv-gap-1"
        style={{ paddingLeft: depth * 14 }}
      >
        <button
          onClick={() => setExpanded((v) => !v)}
          aria-label={expanded ? 'Collapse' : 'Expand'}
          style={{
            background: 'none',
            border: 'none',
            cursor: hasChildren ? 'pointer' : 'default',
            color: 'var(--mv-text-faint)',
            width: 16,
            flexShrink: 0,
            visibility: hasChildren ? 'visible' : 'hidden',
            transform: expanded ? 'rotate(90deg)' : 'none',
            transition: 'transform 100ms ease',
            padding: 0,
          }}
        >
          ▸
        </button>
        <Link
          to={`/w/${workspaceId}/library?folder=${folder.id}`}
          className="mv-sidebar-link mv-truncate"
          style={{
            flex: 1,
            background: isActive ? 'var(--mv-accent-100)' : 'transparent',
            color: isActive ? 'var(--mv-accent-900)' : 'var(--mv-text-muted)',
            fontWeight: isActive ? 700 : 500,
          }}
          title={folder.name}
        >
          {folder.name}
        </Link>
        {folder.asset_count > 0 && (
          <span className="mv-faint" style={{ fontSize: 11 }}>
            {folder.asset_count}
          </span>
        )}
      </div>
      {expanded && childrenQuery.data?.map((child) => (
        <FolderTreeNode key={child.id} workspaceId={workspaceId} folder={child} depth={depth + 1} />
      ))}
    </div>
  )
}
