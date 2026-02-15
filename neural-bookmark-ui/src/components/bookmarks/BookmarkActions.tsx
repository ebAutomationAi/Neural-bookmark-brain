// BookmarkActions.tsx - Componente de acciones para bookmarks
import React from 'react';
import Button from '../ui/Button';
import type { Bookmark } from '../../types';

interface BookmarkActionsProps {
  bookmark: Bookmark;
  onRefresh?: () => void;
  onEdit?: (bookmark: Bookmark) => void;
  onDelete?: (id: number) => void;
}

const BookmarkActions: React.FC<BookmarkActionsProps> = ({ 
  bookmark, 
  onRefresh,
  onEdit, 
  onDelete 
}) => {
  const getStatusColor = () => {
    switch (bookmark.status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'processing':
        return 'text-yellow-600 bg-yellow-50';
      case 'pending':
        return 'text-blue-600 bg-blue-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {/* Status Badge */}
      <div 
        className={`px-3 py-1.5 rounded-lg font-medium text-sm flex items-center gap-1.5 ${getStatusColor()}`}
      >
        {bookmark.status === 'completed' && '✅'}
        {bookmark.status === 'processing' && '⚙️'}
        {bookmark.status === 'pending' && '⏳'}
        {bookmark.status === 'failed' && '❌'}
        {bookmark.status.charAt(0).toUpperCase() + bookmark.status.slice(1)}
      </div>

      {/* Actions */}
      {onEdit && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onEdit(bookmark)}
        >
          ✏️ Editar
        </Button>
      )}

      {onDelete && (
        <Button
          variant="danger"
          size="sm"
          onClick={() => onDelete(bookmark.id)}
        >
          🗑️ Eliminar
        </Button>
      )}

      {onRefresh && bookmark.status === 'failed' && (
        <Button
          variant="success"
          size="sm"
          onClick={onRefresh}
        >
          🔄 Reintentar
        </Button>
      )}

      {/* Open Link */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => window.open(bookmark.url, '_blank')}
      >
        🔗 Abrir
      </Button>
    </div>
  );
};

export default BookmarkActions;