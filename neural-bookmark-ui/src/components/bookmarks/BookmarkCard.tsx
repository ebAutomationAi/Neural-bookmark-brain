// BookmarkCard.tsx - Tarjeta individual de bookmark
import React, { useState } from 'react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import type { Bookmark } from '../../types';

interface BookmarkCardProps {
  bookmark: Bookmark;
  onEdit?: (bookmark: Bookmark) => void;
  onDelete?: (id: number) => void;
  showActions?: boolean;
}

const BookmarkCard: React.FC<BookmarkCardProps> = ({ 
  bookmark, 
  onEdit, 
  onDelete, 
  showActions = true 
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showFullSummary, setShowFullSummary] = useState(false);

  const getCategoryVariant = (category: string | undefined): 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' => {
    switch (category?.toLowerCase()) {
      case 'tecnología':
      case 'technology':
        return 'primary';
      case 'educación':
      case 'education':
        return 'success';
      case 'noticias':
      case 'news':
        return 'info';
      case 'entretenimiento':
      case 'entertainment':
        return 'warning';
      case 'negocios':
      case 'business':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300 overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-gray-100">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-2 hover:text-indigo-600 transition-colors">
              <a 
                href={bookmark.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {bookmark.clean_title || bookmark.original_title || 'Sin título'}
              </a>
            </h3>
            <a 
              href={bookmark.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 text-sm break-all line-clamp-1 block"
            >
              {bookmark.url}
            </a>
          </div>
          
          {bookmark.category && (
            <Badge 
              variant={getCategoryVariant(bookmark.category)} 
              size="md"
              className="ml-3 flex-shrink-0"
            >
              {bookmark.category}
            </Badge>
          )}
        </div>
      </div>

      {/* Content */}
      {(bookmark.summary || bookmark.tags) && (
        <div className="p-5">
          {/* Summary */}
          {bookmark.summary && (
            <div className="mb-4">
              <p 
                className={`text-gray-700 text-sm leading-relaxed transition-all duration-300 ${
                  showFullSummary || bookmark.summary.length < 250 
                    ? '' 
                    : 'line-clamp-3'
                }`}
              >
                {bookmark.summary}
              </p>
              {bookmark.summary.length >= 250 && (
                <button
                  onClick={() => setShowFullSummary(!showFullSummary)}
                  className="mt-2 text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors"
                >
                  {showFullSummary ? 'Ver menos' : 'Ver más...'}
                </button>
              )}
            </div>
          )}

          {/* Tags */}
          {bookmark.tags && bookmark.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {bookmark.tags.slice(0, 10).map((tag, index) => (
                <Badge key={index} variant="info" size="sm">
                  #{tag}
                </Badge>
              ))}
              {bookmark.tags.length > 10 && (
                <Badge variant="secondary" size="sm">
                  +{bookmark.tags.length - 10} más
                </Badge>
              )}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span>🔗 {bookmark.domain}</span>
          </span>
          <span className="flex items-center gap-1">
            <span>📝 {bookmark.word_count || 0} palabras</span>
          </span>
          {bookmark.updated_at && (
            <span className="flex items-center gap-1">
              <span>📅 {new Date(bookmark.updated_at).toLocaleDateString('es-ES')}</span>
            </span>
          )}
        </div>

        {/* Actions */}
        {showActions && (onEdit || onDelete) && (
          <div className="mt-3 flex gap-2">
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
          </div>
        )}
      </div>
    </div>
  );
};

export default BookmarkCard;