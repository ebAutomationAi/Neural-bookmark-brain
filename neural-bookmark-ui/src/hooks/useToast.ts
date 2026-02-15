// useToast.ts - Hook personalizado para gestionar toasts
import { useState } from 'react';
import { ToastMessage } from '../types';
import { v4 as uuidv4 } from 'uuid';

interface UseToastReturn {
  toasts: ToastMessage[];
  showToast: (message: Omit<ToastMessage, 'id'>) => void;
  hideToast: (id: string) => void;
}

const useToast = (): UseToastReturn => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (toast: Omit<ToastMessage, 'id'>) => {
    const newToast: ToastMessage = {
      id: uuidv4(),
      ...toast
    };
    setToasts((prev) => [...prev, newToast]);
  };

  const hideToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return {
    toasts,
    showToast,
    hideToast
  };
};

export default useToast;