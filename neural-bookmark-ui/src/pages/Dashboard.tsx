// Dashboard.tsx - Página principal del dashboard
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StatCard from '../components/stats/StatCard';
import ProcessingProgress from '../components/stats/ProcessingProgress';
import BookmarkGrid from '../components/bookmarks/BookmarkGrid';
import SearchBar from '../components/search/SearchBar';
import useBookmarks from '../hooks/useBookmarks';
import type { ProcessingStats } from '../types';

interface DashboardProps {
  stats: ProcessingStats | null;
}

const Dashboard: React.FC<DashboardProps> = ({ stats }) => {
  const navigate = useNavigate();
  const { bookmarks, loading, search, refetch } = useBookmarks({
    status_filter: 'completed',
    limit: 12
  });

  useEffect(() => {
    refetch();
  }, []);

  const handleSearch = async (query: string) => {
    await search(query);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">📊 Dashboard</h1>
        <p className="text-gray-500 mt-1">Resumen de tu biblioteca de bookmarks</p>
      </div>

      {/* Search Bar */}
      <SearchBar 
        onSearch={handleSearch}
        placeholder="🔍 Buscar en tus bookmarks..."
      />

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Bookmarks"
            value={stats.total_bookmarks}
            icon="📚"
            variant="primary"
            subtitle="En tu biblioteca"
          />
          <StatCard
            title="Procesados"
            value={stats.completed}
            icon="✅"
            variant="success"
            subtitle="Listos para usar"
            trend="up"
            trendValue={`${stats.completed}`}
          />
          <StatCard
            title="Pendientes"
            value={stats.pending}
            icon="⏳"
            variant="warning"
            subtitle="Esperando procesamiento"
          />
          <StatCard
            title="Fallidos"
            value={stats.failed}
            icon="❌"
            variant="danger"
            subtitle="Requieren atención"
          />
        </div>
      )}

      {/* Processing Progress */}
      {stats && (
        <ProcessingProgress stats={stats} />
      )}

      {/* Recent Bookmarks */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">📚 Últimos Bookmarks</h2>
            <p className="text-gray-500 text-sm mt-1">
              Los bookmarks más recientes en tu biblioteca
            </p>
          </div>
          <button
            onClick={() => navigate('/bookmarks')}
            className="text-indigo-600 hover:text-indigo-800 font-medium text-sm"
          >
            Ver todos →
          </button>
        </div>
        
        <BookmarkGrid
          bookmarks={bookmarks}
          isLoading={loading}
          showActions={false}
          emptyMessage="No hay bookmarks recientes"
        />
      </div>
    </div>
  );
};

export default Dashboard;