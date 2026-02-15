// Statistics.tsx - Página de estadísticas detalladas
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import StatCard from '../components/stats/StatCard';
import ProcessingProgress from '../components/stats/ProcessingProgress';
import Badge from '../components/ui/Badge';
import type { ProcessingStats, CategoryStats, TagStats } from '../types';

const Statistics: React.FC = () => {
  const [stats, setStats] = useState<ProcessingStats | null>(null);
  const [categories, setCategories] = useState<CategoryStats[]>([]);
  const [tags, setTags] = useState<TagStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const [statsData, categoriesData, tagsData] = await Promise.all([
        api.getStats(),
        api.getCategories(),
        api.getTags(50)
      ]);
      setStats(statsData);
      setCategories(categoriesData);
      setTags(tagsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (index: number): string => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
      'bg-orange-500',
      'bg-cyan-500'
    ];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando estadísticas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">📊 Estadísticas Detalladas</h1>
        <p className="text-gray-500 mt-1">Análisis completo de tu biblioteca</p>
      </div>

      {/* Processing Progress */}
      {stats && <ProcessingProgress stats={stats} showDetails={true} />}

      {/* Categories Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">📂 Categorías</h2>
          <p className="text-gray-500 text-sm mt-1">
            Distribución de tus bookmarks por categorías
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((category, index) => (
            <div 
              key={category.category} 
              className="bg-white rounded-lg p-4 border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg ${getCategoryColor(index)} flex items-center justify-center`}>
                    <span className="text-white font-bold text-lg">
                      {category.category.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <p className="font-bold text-gray-900">{category.category}</p>
                    <p className="text-sm text-gray-500">{category.count} bookmarks</p>
                  </div>
                </div>
                <Badge variant="info" size="sm">
                  {category.percentage.toFixed(1)}%
                </Badge>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-full rounded-full ${getCategoryColor(index)}`}
                  style={{ width: `${category.percentage}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tags Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">🏷️ Tags Populares</h2>
          <p className="text-gray-500 text-sm mt-1">
            Los tags más frecuentes en tus bookmarks
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <div
                key={tag.tag}
                className="group relative"
              >
                <Badge 
                  variant="info" 
                  size="lg"
                  className="px-4 py-2 text-base cursor-pointer hover:bg-blue-200 transition-colors"
                >
                  #{tag.tag} <span className="ml-1 text-xs opacity-75">({tag.count})</span>
                </Badge>
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1">
                  {tag.percentage.toFixed(1)}% de tus bookmarks
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm font-medium">Tasa de Éxito</p>
                <p className="text-4xl font-bold mt-1">
                  {stats.total_bookmarks > 0 
                    ? ((stats.completed / stats.total_bookmarks) * 100).toFixed(1) 
                    : 0}%
                </p>
                <p className="text-blue-100 text-sm mt-1">
                  {stats.completed} de {stats.total_bookmarks} procesados correctamente
                </p>
              </div>
              <div className="text-5xl">🎯</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm font-medium">Total de Tags</p>
                <p className="text-4xl font-bold mt-1">{tags.length}</p>
                <p className="text-green-100 text-sm mt-1">
                  Tags únicos identificados
                </p>
              </div>
              <div className="text-5xl">🏷️</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm font-medium">Categorías</p>
                <p className="text-4xl font-bold mt-1">{categories.length}</p>
                <p className="text-purple-100 text-sm mt-1">
                  Categorías diferentes
                </p>
              </div>
              <div className="text-5xl">📂</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Statistics;