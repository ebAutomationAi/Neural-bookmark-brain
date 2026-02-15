// Input.tsx - Componente Input reutilizable
import React from 'react';

type InputSize = 'sm' | 'md' | 'lg';
type InputVariant = 'default' | 'flushed';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  size?: InputSize;
  variant?: InputVariant;
  label?: string;
  error?: string;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ 
    size = 'md', 
    variant = 'default', 
    label, 
    error, 
    iconLeft, 
    iconRight, 
    className = '', 
    ...props 
  }, ref) => {
    const baseStyles = 'w-full font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all';
    
    const sizeStyles = {
      sm: 'px-2 py-1 text-sm',
      md: 'px-3 py-2 text-base',
      lg: 'px-4 py-3 text-lg'
    };
    
    const variantStyles = {
      default: 'border border-gray-300 rounded-lg',
      flushed: 'border-b-2 border-gray-300 rounded-none bg-transparent'
    };

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        
        <div className="relative">
          {iconLeft && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {iconLeft}
            </div>
          )}
          
          <input
            ref={ref}
            className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className} ${
              iconLeft ? 'pl-10' : ''
            } ${iconRight ? 'pr-10' : ''} ${error ? 'border-red-500 focus:ring-red-500' : ''}`}
            {...props}
          />
          
          {iconRight && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {iconRight}
            </div>
          )}
        </div>
        
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;