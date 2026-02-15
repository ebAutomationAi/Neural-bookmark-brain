// Sidebar.tsx - Componente Sidebar
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import Badge from '../ui/Badge';
import type { ProcessingStats } from '../../types';

interface SidebarProps {
  stats?: ProcessingStats | null;
  isOpen?: boolean;
  onClose?: () => void;
}

const menuItems = [
  { path: '/', icon: '🏠', label: 'Dashboard' },
  { path: '/bookmarks', icon: '📚', label: 'Todos los Bookmarks' },
  { path: '/categories', icon: '📂', label: 'Categorías' },
  { path: '/tags', icon: '🏷️', label: 'Tags' },
  { path: '/stats', icon: '📊', label: 'Estadísticas' },
  { path: '/settings', icon: '⚙️', label: 'Configuración' }
];

const Sidebar: React.FC<SidebarProps> = ({ stats, isOpen = true, onClose }) => {
  const navigate = useNavigate();

  return (
    <aside 
      className={`bg-gradient-to-b from-indigo-900 to-purple-900 text-white h-full ${
        isOpen ? 'block' : 'hidden'
      } md:block md:w-64 flex flex-col`}
    >
      {/* Logo */}
      <div className="p-6 border-b border-indigo-800">
        <div 
          className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mb-3 cursor-pointer"
          onClick={() => navigate('/')}
        >
          <span className="text-white text-2xl font-bold">🧠</span>
        </div>
        <h2 className="text-xl font-bold cursor-pointer" onClick={() => navigate('/')}>
          Neural Brain
        </h2>
        <p className="text-indigo-200 text-sm mt-1">Bookmarks Inteligentes</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="p-4 bg-indigo-800/30 border-b border-indigo-700">
          <p className="text-xs text-indigo-200 mb-2">ESTADÍSTICAS</p>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Total:</span>
                <span className="font-bold">{stats.total_bookmarks}</span>
              </div>
              <div className="w-full bg-indigo-700 rounded-full h-1.5">
                <div 
                  className="bg-white h-1.5 rounded-full" 
                  style={{ width: `${(stats.completed / stats.total_bookmarks) * 100 || 0}%` }}
                ></div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <Badge variant="success" size="sm">✅ {stats.completed}</Badge>
                <p className="text-indigo-200 mt-1">Procesados</p>
              </div>
              <div>
                <Badge variant="warning" size="sm">⏳ {stats.pending}</Badge>
                <p className="text-indigo-200 mt-1">Pendientes</p>
              </div>
              <div>
                <Badge variant="danger" size="sm">❌ {stats.failed}</Badge>
                <p className="text-indigo-200 mt-1">Fallidos</p>
              </div>
              <div>
                <Badge variant="info" size="sm">⚙️ {stats.processing}</Badge>
                <p className="text-indigo-200 mt-1">Procesando</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-4">
          {menuItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-white text-indigo-900 shadow-lg'
                      : 'text-indigo-100 hover:bg-indigo-800/50'
                  }`
                }
                onClick={onClose}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-indigo-800">
        <div className="text-center">
          <p className="text-xs text-indigo-300">Neural Bookmark Brain</p>
          <p className="text-xs text-indigo-200 mt-1">v1.0.0</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;