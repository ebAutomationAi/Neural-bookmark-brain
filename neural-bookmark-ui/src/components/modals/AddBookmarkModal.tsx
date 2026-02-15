// AddBookmarkModal.tsx - Modal para agregar nuevo bookmark
import React, { useState } from 'react';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface AddBookmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (url: string) => Promise<void>;
}

const AddBookmarkModal: React.FC<AddBookmarkModalProps> = ({ 
  isOpen, 
  onClose, 
  onAdd 
}) => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Por favor ingresa una URL válida');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      await onAdd(url.trim());
      setUrl('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al agregar el bookmark');
    } finally {
      setIsLoading(false);
    }
  };

  const isValidUrl = (urlString: string) => {
    try {
      new URL(urlString);
      return true;
    } catch {
      return false;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">➕ Agregar Bookmark</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Cerrar"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-gray-500 text-sm mt-1">
            Ingresa la URL que quieres guardar y procesar
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <Input
              type="url"
              label="URL del sitio web"
              placeholder="https://ejemplo.com/articulo"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setError('');
              }}
              error={error}
              size="lg"
              iconLeft={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              }
            />

            {/* URL Preview */}
            {url && isValidUrl(url) && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-700 font-medium mb-1">URL detectada:</p>
                <p className="text-sm text-blue-900 break-all">{url}</p>
              </div>
            )}

            {/* Help Text */}
            <div className="text-sm text-gray-500 space-y-2">
              <p>💡 <span className="font-medium">Tips:</span></p>
              <ul className="list-disc list-inside space-y-1">
                <li>Asegúrate de que la URL sea accesible públicamente</li>
                <li>El procesamiento puede tardar unos segundos</li>
                <li>Se extraerá el contenido, título y se generará un resumen</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="secondary"
                size="lg"
                className="flex-1"
                onClick={onClose}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="flex-1"
                isLoading={isLoading}
                disabled={!url.trim() || (url.trim() && !isValidUrl(url.trim()))}
              >
                🧠 Procesar Bookmark
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddBookmarkModal;