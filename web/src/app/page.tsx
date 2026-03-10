'use client'

import { useState } from 'react'
import { addBookmark } from '@/lib/api'
import SmartAddModal from '@/components/SmartAddModal'

export default function Home() {
  const [bookmarks, setBookmarks] = useState([])

  const handleAddBookmark = async (data: any) => {
    const result = await addBookmark(data)
    setBookmarks([...bookmarks, result])
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-4xl font-bold">QuickTag Bookmark Pro</h1>
        <p className="text-gray-600 mt-2">Capture, organize, and discover web resources with AI-powered intelligence</p>
      </header>
      
      <SmartAddModal onAdd={handleAddBookmark} />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {bookmarks.map(bookmark => (
          <div key={bookmark.id} className="bg-white p-4 rounded shadow">
            <h3 className="font-bold text-lg">{bookmark.title}</h3>
            <a href={bookmark.url} className="text-blue-600 hover:underline block mt-1">{bookmark.url}</a>
            <p className="mt-2 text-sm text-gray-700">{bookmark.summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {bookmark.suggestedTags.map(tag => (
                <span key={tag.tag} className="px-2 py-1 bg-gray-100 rounded text-xs">
                  {tag.tag} ({tag.confidence.toFixed(2)})
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}