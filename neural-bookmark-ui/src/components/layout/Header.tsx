// Header.tsx - Componente Header
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import Input from '../ui/Input';
import type { ProcessingStats } from '../../types';

interface HeaderProps {
  stats?: ProcessingStats | null;
  onSearch?: (query: string) => void;
  onAddBookmark?: () => void;
}

const Header: React.FC<HeaderProps> = ({ stats, onSearch, onAddBookmark }) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = React.useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchQuery);
    }
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center cursor-pointer"
              onClick={() => navigate('/')}
            >
              <span className="text-white font-bold text-xl">🧠</span>
            </div>
            <div>
              <h1 
                className="text-xl font-bold text-gray-900 cursor-pointer"
                onClick={() => navigate('/')}
              >
                Neural Bookmark Brain
              </h1>
              <p className="text-xs text-gray-500">Tu biblioteca inteligente</p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-2xl mx-8">
            <form onSubmit={handleSearch}>
              <div className="relative">
                <Input
                  type="text"
                  placeholder="🔍 Buscar en tus bookmarks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  size="md"
                  className="pr-24"
                />
                <button
                  type="submit"
                  className="absolute right-1 top-1 bottom-1 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Buscar
                </button>
              </div>
            </form>
          </div>

          {/* Actions & Stats */}
          <div className="flex items-center gap-4">
            {stats && (
              <div className="hidden md:flex items-center gap-4 text-sm">
                <div className="text-center">
                  <p className="text-xs text-gray-500">Total</p>
                  <p className="font-bold text-gray-900">{stats.total_bookmarks}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">✅ Procesados</p>
                  <p className="font-bold text-green-600">{stats.completed}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500">⏳ Pendientes</p>
                  <p className="font-bold text-yellow-600">{stats.pending}</p>
                </div>
              </div>
            )}

            <Button
              onClick={onAddBookmark || (() => navigate('/add'))}
              variant="primary"
              size="md"
              className="whitespace-nowrap"
            >
              ➕ Nuevo Bookmark
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;