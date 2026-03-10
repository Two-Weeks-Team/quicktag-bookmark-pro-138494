import { API } from 'next/dist/server/api-utils'

export async function addBookmark(data: { url: string; title?: string; tags?: string[] }) {
  const res = await fetch('/api/bookmarks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  
  if (!res.ok) throw new Error('Failed to add bookmark')
  return await res.json()
}

export async function getBookmarks(filters: { tags?: string[] } = {}) {
  const res = await fetch('/api/bookmarks', {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })
  
  if (!res.ok) throw new Error('Failed to fetch bookmarks')
  return await res.json()
}

export async function summarizeURL(url: string) {
  const res = await fetch('/api/ai/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, max_sentences: 2 })
  })
  
  if (!res.ok) throw new Error('Summarization failed')
  return await res.json()
}

export async function suggestTags(url: string) {
  const res = await fetch('/api/ai/suggest-tags', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  })
  
  if (!res.ok) throw new Error('Tag suggestion failed')
  return await res.json()
}