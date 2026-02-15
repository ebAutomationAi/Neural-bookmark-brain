// tests/api/bookmarks-api.spec.ts - Tests para la API
import { test, expect } from '../setup';

test.describe('API de Bookmarks', () => {
  
  test('debería obtener estadísticas', async ({ apiContext }) => {
    const response = await apiContext.get('/stats/processing');
    expect(response.ok()).toBe(true);
    const data = await response.json();
    
    // FIX: El backend usa 'total', no 'total_bookmarks'
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('completed');
    expect(data).toHaveProperty('pending');
    expect(data).toHaveProperty('failed');
  });

  test('debería obtener categorías', async ({ apiContext }) => {
    const response = await apiContext.get('/stats/categories');
    expect(response.ok()).toBe(true);
    const data = await response.json();
    
    // FIX: El backend devuelve un objeto con la llave 'categories'
    expect(Array.isArray(data.categories)).toBe(true);
    if (data.categories.length > 0) {
      expect(data.categories[0]).toHaveProperty('category');
      expect(data.categories[0]).toHaveProperty('count');
    }
  });

  test('debería obtener tags', async ({ apiContext }) => {
    const response = await apiContext.get('/stats/tags');
    expect(response.ok()).toBe(true);
    const data = await response.json();
    
    // FIX: El backend devuelve un objeto con la llave 'tags'
    expect(Array.isArray(data.tags)).toBe(true);
    if (data.tags.length > 0) {
      expect(data.tags[0]).toHaveProperty('tag');
      expect(data.tags[0]).toHaveProperty('count');
    }
  });

  test('debería obtener bookmarks', async ({ apiContext }) => {
    const response = await apiContext.get('/bookmarks?limit=5');
    expect(response.ok()).toBe(true);
    const data = await response.json();
    
    expect(Array.isArray(data)).toBe(true);
    if (data.length > 0) {
      expect(data[0]).toHaveProperty('id');
      expect(data[0]).toHaveProperty('url');
      // FIX: El backend usa 'original_title'
      expect(data[0]).toHaveProperty('original_title');
      expect(data[0]).toHaveProperty('status');
    }
  });

  test('debería buscar bookmarks', async ({ apiContext }) => {
    // FIX: Asegurar que el payload coincida con SearchRequest schema
    const response = await apiContext.post('/search', {
      data: {
        query: 'tecnología',
        limit: 5,
        include_nsfw: true
      }
    });
    
    expect(response.ok()).toBe(true);
    const data = await response.json();
    expect(data).toHaveProperty('results');
    expect(data).toHaveProperty('total');
  });
});