// useBookmarks.ts - Hook personalizado para gestionar bookmarks
import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Bookmark, BookmarkFilters, ProcessingStats } from '../types';

interface UseBookmarksReturn {
  bookmarks: Bookmark[];
  stats: ProcessingStats | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  addBookmark: (url: string) => Promise<void>;
  deleteBookmark: (id: number) => Promise<void>;
  search: (query: string) => Promise<void>;
  loadStats: () => Promise<void>;
}

const useBookmarks = (initialFilters: BookmarkFilters = {}): UseBookmarksReturn => {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [stats, setStats] = useState<ProcessingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<BookmarkFilters>(initialFilters);

  const loadBookmarks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBookmarks(filters);
      setBookmarks(data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar los bookmarks');
      console.error('Error loading bookmarks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
    } catch (err: any) {
      console.error('Error loading stats:', err);
    }
  };

  const refetch = async () => {
    await Promise.all([loadBookmarks(), loadStats()]);
  };

  const addBookmark = async (url: string) => {
    try {
      const newBookmark = await api.addBookmark(url);
      setBookmarks((prev) => [newBookmark, ...prev]);
      await loadStats();
    } catch (err: any) {
      setError(err.message || 'Error al agregar el bookmark');
      throw err;
    }
  };

  const deleteBookmark = async (id: number) => {
    try {
      await api.deleteBookmark(id);
      setBookmarks((prev) => prev.filter((b) => b.id !== id));
      await loadStats();
    } catch (err: any) {
      setError(err.message || 'Error al eliminar el bookmark');
      throw err;
    }
  };

  const search = async (query: string) => {
    if (!query.trim()) {
      await loadBookmarks();
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.search(query);
      setBookmarks(response.results);
    } catch (err: any) {
      setError(err.message || 'Error en la búsqueda');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refetch();
  }, [filters]);

  return {
    bookmarks,
    stats,
    loading,
    error,
    refetch,
    addBookmark,
    deleteBookmark,
    search,
    loadStats
  };
};

export default useBookmarks;