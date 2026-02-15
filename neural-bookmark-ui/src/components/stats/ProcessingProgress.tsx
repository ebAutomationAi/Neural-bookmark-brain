// ProcessingProgress.tsx - Barra de progreso de procesamiento
import React from 'react';
import type { ProcessingStats } from '../../types';

interface ProcessingProgressProps {
  stats: ProcessingStats;
  showDetails?: boolean;
}

const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ 
  stats, 
  showDetails = true 
}) => {
  const total = stats.total_bookmarks;
  const completedPercent = total > 0 ? (stats.completed / total) * 100 : 0;
  const pendingPercent = total > 0 ? (stats.pending / total) * 100 : 0;
  const processingPercent = total > 0 ? (stats.processing / total) * 100 : 0;
  const failedPercent = total > 0 ? (stats.failed / total) * 100 : 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-bold text-gray-900">Progreso de Procesamiento</h3>
          <span className="text-sm font-medium text-gray-600">
            {stats.completed}/{total} completados
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500"
            style={{ width: `${completedPercent}%` }}
            title={`${stats.completed} completados`}
          ></div>
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500"
            style={{ 
              width: `${processingPercent}%`, 
              marginLeft: `${completedPercent}%` 
            }}
            title={`${stats.processing} procesando`}
          ></div>
          <div 
            className="h-full bg-gradient-to-r from-yellow-500 to-orange-500 transition-all duration-500"
            style={{ 
              width: `${pendingPercent}%`, 
              marginLeft: `${completedPercent + processingPercent}%` 
            }}
            title={`${stats.pending} pendientes`}
          ></div>
          <div 
            className="h-full bg-gradient-to-r from-red-500 to-pink-600 transition-all duration-500"
            style={{ 
              width: `${failedPercent}%`, 
              marginLeft: `${completedPercent + processingPercent + pendingPercent}%` 
            }}
            title={`${stats.failed} fallidos`}
          ></div>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-700">{stats.completed}</div>
            <div className="text-xs text-green-600 mt-1 flex items-center justify-center gap-1">
              <span>✅</span>
              <span>Completados</span>
            </div>
          </div>
          
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-700">{stats.processing}</div>
            <div className="text-xs text-blue-600 mt-1 flex items-center justify-center gap-1">
              <span>⚙️</span>
              <span>Procesando</span>
            </div>
          </div>
          
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-700">{stats.pending}</div>
            <div className="text-xs text-yellow-600 mt-1 flex items-center justify-center gap-1">
              <span>⏳</span>
              <span>Pendientes</span>
            </div>
          </div>
          
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-700">{stats.failed}</div>
            <div className="text-xs text-red-600 mt-1 flex items-center justify-center gap-1">
              <span>❌</span>
              <span>Fallidos</span>
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Tasa de éxito:</span>
          <span className="font-bold text-gray-900">
            {total > 0 ? ((stats.completed / total) * 100).toFixed(1) : 0}%
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProcessingProgress;