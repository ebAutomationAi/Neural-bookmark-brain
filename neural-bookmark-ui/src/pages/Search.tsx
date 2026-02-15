// Search.tsx - Página de búsqueda avanzada
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import BookmarkGrid from '../components/bookmarks/BookmarkGrid';
import { api } from '../services/api';
import type { Bookmark } from '../types';

const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initialQuery = searchParams.get('q');
    if (initialQuery) {
      setQuery(initialQuery);
      performSearch(initialQuery);
    }
  }, [searchParams]);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.search(searchQuery, 50);
      setResults(response.results || []);
    } catch (err: any) {
      setError(err.message || 'Error al realizar la búsqueda');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery);
    setSearchParams({ q: searchQuery });
    await performSearch(searchQuery);
  };

  const handleClear = () => {
    setQuery('');
    setSearchParams({});
    setResults([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">🔍 Búsqueda Avanzada</h1>
        <p className="text-gray-500 mt-1">
          Busca en tus bookmarks usando búsqueda semántica
        </p>
      </div>

      {/* Search Bar */}
      <SearchBar 
        onSearch={handleSearch}
        onClear={handleClear}
        placeholder="🔍 ¿Qué estás buscando?..."
        initialValue={query}
      />

      {/* Results Info */}
      {!loading && query && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800 font-medium">
            {error 
              ? `⚠️ ${error}`
              : loading 
                ? 'Buscando...'
                : `${results.length} resultado${results.length !== 1 ? 's' : ''} para "${query}"`
            }
          </p>
        </div>
      )}

      {/* Results Grid */}
      <BookmarkGrid
        bookmarks={results}
        isLoading={loading}
        showActions={false}
        emptyMessage={
          query 
            ? error || 'No se encontraron resultados'
            : 'Ingresa una búsqueda para ver resultados'
        }
      />
    </div>
  );
};

export default SearchPage;