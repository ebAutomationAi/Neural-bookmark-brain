// App.tsx - Componente principal de la aplicación
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Bookmarks from './pages/Bookmarks';
import SearchPage from './pages/Search';
import Statistics from './pages/Statistics';
import { api } from './services/api';
import useToast from './hooks/useToast';
import Toast from './components/ui/Toast';
import type { ProcessingStats } from './types';

const App: React.FC = () => {
  const [stats, setStats] = useState<ProcessingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, hideToast } = useToast();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const statsData = await api.getStats();
      setStats(statsData);
    } catch (error: any) {
      console.error('Error loading stats:', error);
      showToast({
        type: 'error',
        message: 'Error al cargar las estadísticas: ' + error.message
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse">🧠</div>
          <div className="text-white text-2xl font-bold mb-2">Neural Bookmark Brain</div>
          <div className="text-indigo-200">Cargando...</div>
          <div className="mt-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-4 border-white mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen">
        <Routes>
          {/* Rutas con Layout */}
          <Route
            path="/"
            element={
              <Layout stats={stats}>
                <Dashboard stats={stats} />
              </Layout>
            }
          />
          
          <Route
            path="/bookmarks"
            element={
              <Layout stats={stats}>
                <Bookmarks />
              </Layout>
            }
          />
          
          <Route
            path="/search"
            element={
              <Layout stats={stats}>
                <SearchPage />
              </Layout>
            }
          />
          
          <Route
            path="/stats"
            element={
              <Layout stats={stats}>
                <Statistics />
              </Layout>
            }
          />
          
          {/* Rutas adicionales */}
          <Route
            path="/categories"
            element={
              <Layout stats={stats}>
                <div className="text-center py-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">📂 Categorías</h2>
                  <p className="text-gray-500">Próximamente...</p>
                </div>
              </Layout>
            }
          />
          
          <Route
            path="/tags"
            element={
              <Layout stats={stats}>
                <div className="text-center py-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">🏷️ Tags</h2>
                  <p className="text-gray-500">Próximamente...</p>
                </div>
              </Layout>
            }
          />
          
          <Route
            path="/settings"
            element={
              <Layout stats={stats}>
                <div className="text-center py-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">⚙️ Configuración</h2>
                  <p className="text-gray-500">Próximamente...</p>
                </div>
              </Layout>
            }
          />

          {/* Redirección para rutas no encontradas */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Toast Notifications */}
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
          {toasts.map((toast) => (
            <Toast key={toast.id} message={toast} onClose={hideToast} />
          ))}
        </div>
      </div>
    </Router>
  );
};

export default App;