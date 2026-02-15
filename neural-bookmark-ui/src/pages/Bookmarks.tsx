// Bookmarks.tsx - Página de lista de todos los bookmarks
import React, { useState } from 'react';
import BookmarkGrid from '../components/bookmarks/BookmarkGrid';
import SearchBar from '../components/search/SearchBar';
import useBookmarks from '../hooks/useBookmarks';
import Button from '../components/ui/Button';
import AddBookmarkModal from '../components/modals/AddBookmarkModal';
import type { Bookmark } from '../types';

const Bookmarks: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { 
    bookmarks, 
    loading, 
    search, 
    addBookmark,
    deleteBookmark,
    refetch 
  } = useBookmarks({
    status_filter: 'completed',
    limit: 50
  });

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    await search(query);
  };

  const handleAdd = async (url: string) => {
    await addBookmark(url);
    await refetch();
  };

  const handleDelete = async (id: number) => {
    if (confirm('¿Estás seguro de que quieres eliminar este bookmark?')) {
      await deleteBookmark(id);
      await refetch();
    }
  };

  const handleClearSearch = async () => {
    setSearchQuery('');
    await refetch();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📚 Todos los Bookmarks</h1>
          <p className="text-gray-500 mt-1">
            {loading ? 'Cargando...' : `${bookmarks.length} bookmarks`}
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setShowModal(true)}
        >
          ➕ Agregar Bookmark
        </Button>
      </div>

      {/* Search Bar */}
      <SearchBar 
        onSearch={handleSearch}
        onClear={handleClearSearch}
        placeholder="🔍 Buscar en tus bookmarks..."
        initialValue={searchQuery}
      />

      {/* Bookmarks Grid */}
      <BookmarkGrid
        bookmarks={bookmarks}
        onEdit={(bookmark: Bookmark) => console.log('Editar:', bookmark)}
        onDelete={handleDelete}
        isLoading={loading}
        emptyMessage={
          searchQuery 
            ? 'No se encontraron resultados para tu búsqueda'
            : 'No hay bookmarks todavía. ¡Agrega tu primer bookmark!'
        }
      />

      {/* Add Bookmark Modal */}
      <AddBookmarkModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onAdd={handleAdd}
      />
    </div>
  );
};

export default Bookmarks;