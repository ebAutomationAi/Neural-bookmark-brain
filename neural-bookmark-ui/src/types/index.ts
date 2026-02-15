// Tipos para Neural Bookmark Brain

export type BookmarkStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Bookmark {
  id: number;
  url: string;
  domain: string;
  original_title: string;
  clean_title?: string;
  summary?: string;
  content?: string;
  category?: string;
  tags?: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  word_count?: number;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface BookmarkFilters {
  status_filter?: 'all' | 'pending' | 'processing' | 'completed' | 'failed';
  category?: string;
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}

export interface ProcessingStats {
  total_bookmarks: number;
  completed: number;
  pending: number;
  processing: number;
  failed: number;
  total_tags?: number;
  total_categories?: number;
}

export interface CategoryStats {
  category: string;
  count: number;
  percentage: number;
}

export interface TagStats {
  tag: string;
  count: number;
  percentage: number;
}

export interface SearchResponse {
  query: string;
  results: Bookmark[];
  total: number;
  execution_time: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}