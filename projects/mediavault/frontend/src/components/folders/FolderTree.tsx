import { useQuery } from '@tanstack/react-query'

import { listFolders } from '@/api/folders'
import { FolderTreeNode } from '@/components/folders/FolderTreeNode'

export function FolderTree({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['folders', workspaceId, null],
    queryFn: () => listFolders(workspaceId, null),
  })

  if (isLoading) {
    return (
      <div className="mv-flex-col mv-gap-2">
        <div className="mv-skeleton" style={{ height: 14, width: '80%' }} />
        <div className="mv-skeleton" style={{ height: 14, width: '60%' }} />
      </div>
    )
  }

  if (!data || data.length === 0) {
    return <p className="mv-faint" style={{ fontSize: 12, margin: '4px 0' }}>No folders yet.</p>
  }

  return (
    <div className="mv-flex-col mv-gap-1">
      {data.map((folder) => (
        <FolderTreeNode key={folder.id} workspaceId={workspaceId} folder={folder} depth={0} />
      ))}
    </div>
  )
}
