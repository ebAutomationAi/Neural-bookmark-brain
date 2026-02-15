// BookmarkGrid.tsx - Grid/List de bookmarks
import React from 'react';
import BookmarkCard from './BookmarkCard';
import type { Bookmark } from '../../types';

interface BookmarkGridProps {
  bookmarks: Bookmark[];
  onEdit?: (bookmark: Bookmark) => void;
  onDelete?: (id: number) => void;
  showActions?: boolean;
  isLoading?: boolean;
  emptyMessage?: string;
}

const BookmarkGrid: React.FC<BookmarkGridProps> = ({ 
  bookmarks, 
  onEdit, 
  onDelete, 
  showActions = true,
  isLoading = false,
  emptyMessage = 'No hay bookmarks para mostrar'
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div 
            key={i} 
            className="bg-white rounded-xl shadow-sm border border-gray-100 animate-pulse"
          >
            <div className="p-5">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6 mb-4"></div>
              <div className="flex gap-2">
                <div className="h-6 bg-gray-200 rounded px-3 py-1 w-20"></div>
                <div className="h-6 bg-gray-200 rounded px-3 py-1 w-16"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (bookmarks.length === 0) {
    return (
      <div className="text-center py-16 bg-white rounded-xl shadow-sm border-2 border-dashed border-gray-200">
        <div className="text-6xl mb-4">🧠</div>
        <p className="text-gray-500 text-lg font-medium">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {bookmarks.map((bookmark) => (
        <BookmarkCard
          key={bookmark.id || bookmark.url}
          bookmark={bookmark}
          onEdit={onEdit}
          onDelete={onDelete}
          showActions={showActions}
        />
      ))}
    </div>
  );
};

export default BookmarkGrid;