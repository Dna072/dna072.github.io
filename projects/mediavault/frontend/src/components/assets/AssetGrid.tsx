import { AssetCard } from '@/components/assets/AssetCard'
import type { Asset } from '@/types'

export function AssetGrid({ assets, onOpen }: { assets: Asset[]; onOpen: (asset: Asset) => void }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 16,
      }}
    >
      {assets.map((asset) => (
        <AssetCard key={asset.id} asset={asset} onOpen={() => onOpen(asset)} />
      ))}
    </div>
  )
}
