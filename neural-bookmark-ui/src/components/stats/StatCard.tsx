// StatCard.tsx - Tarjeta de estadísticas
import React from 'react';

type StatVariant = 'primary' | 'success' | 'warning' | 'danger' | 'info';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  variant?: StatVariant;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  icon, 
  variant = 'primary', 
  subtitle, 
  trend, 
  trendValue 
}) => {
  const variantStyles = {
    primary: 'bg-gradient-to-br from-indigo-500 to-purple-600',
    success: 'bg-gradient-to-br from-green-500 to-emerald-600',
    warning: 'bg-gradient-to-br from-yellow-500 to-orange-600',
    danger: 'bg-gradient-to-br from-red-500 to-pink-600',
    info: 'bg-gradient-to-br from-blue-500 to-cyan-600'
  };

  const getTrendIcon = () => {
    if (trend === 'up') return '📈';
    if (trend === 'down') return '📉';
    return '➡️';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${variantStyles[variant]}`}>
          <div className="text-2xl">{icon}</div>
        </div>
      </div>

      {trend && trendValue && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-lg">{getTrendIcon()}</span>
            <span className={`font-medium ${
              trend === 'up' ? 'text-green-600' : 
              trend === 'down' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {trendValue}
            </span>
            <span className="text-sm text-gray-500">
              {trend === 'up' ? 'aumento' : trend === 'down' ? 'disminución' : 'estable'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatCard;