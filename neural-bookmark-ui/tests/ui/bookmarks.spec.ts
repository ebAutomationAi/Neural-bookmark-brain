x// tests/ui/bookmarks.spec.ts - Tests para gestión de bookmarks
import { test, expect } from '../setup';

test.describe('Gestión de Bookmarks', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/bookmarks');
  });

  test('debería mostrar la página de bookmarks', async ({ page }) => {
    // Verificar que la página cargó
    await expect(page.locator('text="📚 Todos los Bookmarks"')).toBeVisible();
    
    // Verificar que el botón "Agregar Bookmark" esté visible
    const addButton = page.locator('button:has-text("➕ Agregar Bookmark")');
    await expect(addButton).toBeVisible();
  });

  test('debería abrir el modal de agregar bookmark', async ({ page }) => {
    const addButton = page.locator('button:has-text("➕ Agregar Bookmark")');
    await addButton.click();
    
    // Verificar que el modal está visible
    const modal = page.locator('text="➕ Agregar Bookmark"');
    await expect(modal).toBeVisible();
    
    // Verificar que el input del modal está visible
    const urlInput = page.locator('input[placeholder*="https://"]');
    await expect(urlInput).toBeVisible();
  });

  test('debería cerrar el modal de agregar bookmark', async ({ page }) => {
    const addButton = page.locator('button:has-text("➕ Agregar Bookmark")');
    await addButton.click();
    
    // Verificar que el modal está visible
    await expect(page.locator('text="➕ Agregar Bookmark"')).toBeVisible();
    
    // Cerrar el modal
    const closeButton = page.locator('button[aria-label="Cerrar"]');
    await closeButton.click();
    
    // Verificar que el modal se cerró
    await expect(page.locator('text="➕ Agregar Bookmark"')).not.toBeVisible();
  });

  test('debería mostrar tarjetas de bookmarks', async ({ page }) => {
    // Esperar a que carguen los bookmarks
    await page.waitForTimeout(1500);
    
    // Verificar que hay tarjetas de bookmarks
    const bookmarkCards = page.locator('[class*="BookmarkCard"]');
    await expect(bookmarkCards).toHaveCount({ min: 1 });
    
    // Verificar que cada tarjeta tiene título y URL
    const firstCard = bookmarkCards.first();
    await expect(firstCard.locator('h3')).toBeVisible();
    await expect(firstCard.locator('a[href]')).toBeVisible();
  });

  test('debería mostrar tags en las tarjetas', async ({ page }) => {
    // Esperar a que carguen los bookmarks
    await page.waitForTimeout(1500);
    
    // Verificar que al menos una tarjeta tiene tags
    const tags = page.locator('[class*="Badge"]:has-text("#")');
    await expect(tags).toHaveCount({ min: 1 });
  });

  test('debería permitir buscar bookmarks', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    
    // Ingresar texto de búsqueda
    await searchInput.fill('react');
    
    // Presionar Enter
    await searchInput.press('Enter');
    
    // Verificar que la URL incluye el parámetro de búsqueda
    await expect(page).toHaveURL(/q=react/);
  });

  test('debería mostrar mensaje cuando no hay bookmarks', async ({ page }) => {
    // Forzar una búsqueda que no devuelva resultados
    await page.goto('/bookmarks');
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    await searchInput.fill('thisisnotarealbookmark12345');
    await searchInput.press('Enter');
    
    // Esperar a que carguen los resultados
    await page.waitForTimeout(1000);
    
    // Verificar mensaje de no resultados
    const noResultsMessage = page.locator('text="No se encontraron resultados"');
    await expect(noResultsMessage).toBeVisible();
  });
});