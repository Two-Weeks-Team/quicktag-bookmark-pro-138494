'use client'

import { useEffect, useState } from 'react'
import { getBookmarks } from '@/lib/api'

export function AITagGraph() {
  const [nodes, setNodes] = useState<any[]>([])
  const [edges, setEdges] = useState<any[]>([])

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const bookmarks = await getBookmarks()
        
        // Build tag network
        const tagMap = new Map<string, { id: string; count: number }>()
        const edgeMap = new Map<string, { weight: number }>()
        
        bookmarks.forEach((bm: any) => {
          bm.suggestedTags.forEach((tag: any) => {
            if (!tagMap.has(tag.tag)) {
              tagMap.set(tag.tag, {
                id: tag.tag,
                count: 1
              })
            } else {
              tagMap.get(tag.tag)!.count += 1
            }
          })
        })

        setNodes(Array.from(tagMap.values()))
        
        // Build edges between co-occurring tags
        bookmarks.forEach((bm: any) => {
          const tags = bm.suggestedTags.map((t: any) => t.tag)
          for (let i = 0; i < tags.length; i++) {
            for (let j = i + 1; j < tags.length; j++) {
              const pair = [tags[i], tags[j]].sort().join('-')
              if (!edgeMap.has(pair)) {
                edgeMap.set(pair, { weight: 1 })
              } else {
                edgeMap.get(pair)!.weight += 1
              }
            }
          }
        })

        setEdges(Array.from(edgeMap.values()))
      } catch (err) {
        console.error('Failed to fetch graph data', err)
      }
    }

    fetchGraphData()
  }, [])

  return (
    <div className="h-96 bg-white rounded-lg shadow p-4">
      <h3 className="font-bold text-lg mb-2">AI Tag Network</h3>
      <div className="h-full w-full">
        {nodes.length > 0 ? (
          <div className="text-sm text-gray-600">
            <p>Nodes ({nodes.length}): {nodes.map(n => n.id).join(', ')}</p>
            <p>Edges ({edges.length}): {edges.map((e, i) => e.weight).join(', ')}</p>
          </div>
        ) : (
          <p className="text-gray-500">Loading tag relationships...</p>
        )}
      </div>
    </div>
  )
}