// Servicio API para Neural Bookmark Brain
// FIXED BUG-02: search ahora usa POST + JSON body (backend: @app.post("/search"))
import type { 
  Bookmark, 
  BookmarkFilters, 
  ProcessingStats, 
  CategoryStats, 
  TagStats, 
  SearchResponse 
} from '../types';a

// Vite usa import.meta.env en lugar de process.env
// Las variables deben empezar con VITE_
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.1.40:8090';

export const api = {
  // ========== Bookmarks ==========
  getBookmarks: async (params: BookmarkFilters = {}): Promise<Bookmark[]> => {
    const query = new URLSearchParams(params as any).toString();
    const response = await fetch(`${API_BASE_URL}/bookmarks?${query}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    return await response.json();
  },

  getBookmarkById: async (id: number): Promise<Bookmark> => {
    const response = await fetch(`${API_BASE_URL}/bookmarks/${id}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    return await response.json();
  },

  addBookmark: async (url: string): Promise<Bookmark> => {
    const response = await fetch(`${API_BASE_URL}/bookmarks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    return await response.json();
  },

  deleteBookmark: async (id: number): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/bookmarks/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  },

  // ========== Stats ==========
  getStats: async (): Promise<ProcessingStats> => {
    const response = await fetch(`${API_BASE_URL}/stats/processing`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const raw = await response.json();
    // Normalize: backend returns { total, ... }, frontend type expects total_bookmarks
    return {
      total_bookmarks: raw.total ?? raw.total_bookmarks ?? 0,
      completed: raw.completed ?? 0,
      pending: raw.pending ?? 0,
      processing: raw.processing ?? 0,
      failed: raw.failed ?? 0,
    };
  },

  getCategories: async (): Promise<CategoryStats[]> => {
    const response = await fetch(`${API_BASE_URL}/stats/categories`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const raw = await response.json();
    // Backend returns { categories: [...] }
    const cats: Array<{ category: string; count: number }> = raw.categories ?? raw ?? [];
    return cats.map((c, i) => ({
      category: c.category,
      count: c.count,
      percentage: 0, // calculated by consumer if needed
    }));
  },

  getTags: async (limit: number = 20): Promise<TagStats[]> => {
    const response = await fetch(`${API_BASE_URL}/stats/tags?limit=${limit}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const raw = await response.json();
    // Backend returns { tags: [...] }
    const tagList: Array<{ tag: string; count: number }> = raw.tags ?? raw ?? [];
    return tagList.map((t) => ({
      tag: t.tag,
      count: t.count,
      percentage: 0,
    }));
  },

  // ========== Search ==========
  // FIXED: backend is @app.post("/search", ...) expecting JSON body {query, limit, include_nsfw}
  // Previous (broken): GET /search?q=...&limit=...  → 405 Method Not Allowed
  // Fixed: POST /search  body: { query, limit, include_nsfw }
  search: async (query: string, limit: number = 10): Promise<SearchResponse> => {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit, include_nsfw: false }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const raw = await response.json();
    // Backend returns { query, results: [{bookmark, similarity_score}], total, execution_time }
    // Flatten: extract bookmark from each result to match SearchResponse.results: Bookmark[]
    return {
      query: raw.query,
      results: (raw.results ?? []).map((r: any) => r.bookmark ?? r),
      total: raw.total ?? 0,
      execution_time: raw.execution_time ?? 0,
    };
  },

  // ========== Health ==========
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
};

export default api;