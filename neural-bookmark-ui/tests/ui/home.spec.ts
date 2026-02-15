// tests/ui/home.spec.ts - Tests para la página principal
import { test, expect } from '../setup';

test.describe('Página Principal - Dashboard', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('debería cargar la página principal correctamente', async ({ page }) => {
    // Verificar que el título esté presente
    await expect(page).toHaveTitle(/Neural Bookmark Brain/);
    
    // Verificar que el header esté visible
    const header = page.locator('h1:has-text("Neural Bookmark Brain")');
    await expect(header).toBeVisible();
    
    // Verificar que el logo esté visible
    const logo = page.locator('text=🧠');
    await expect(logo).toBeVisible();
  });

  test('debería mostrar las tarjetas de estadísticas', async ({ page }) => {
    // Esperar a que carguen las estadísticas
    await page.waitForTimeout(1000);
    
    // Verificar que las tarjetas de stats estén visibles
    const statCards = page.locator('[class*="StatCard"]');
    await expect(statCards).toHaveCount(4);
    
    // Verificar contenido específico
    await expect(page.locator('text="Total Bookmarks"')).toBeVisible();
    await expect(page.locator('text="Procesados"')).toBeVisible();
    await expect(page.locator('text="Pendientes"')).toBeVisible();
    await expect(page.locator('text="Fallidos"')).toBeVisible();
  });

  test('debería mostrar la barra de progreso de procesamiento', async ({ page }) => {
    // Verificar que la barra de progreso esté visible
    const progressBar = page.locator('text="Progreso de Procesamiento"');
    await expect(progressBar).toBeVisible();
    
    // Verificar que los estados estén presentes
    await expect(page.locator('text="✅ Completados"')).toBeVisible();
    await expect(page.locator('text="⚙️ Procesando"')).toBeVisible();
  });

  test('debería navegar al hacer clic en el logo', async ({ page }) => {
    const logo = page.locator('text=🧠').first();
    await logo.click();
    
    // Verificar que seguimos en la página principal
    await expect(page).toHaveURL(/\/$/);
  });

  test('debería mostrar los bookmarks recientes', async ({ page }) => {
    // Esperar a que carguen los bookmarks
    await page.waitForTimeout(1500);
    
    // Verificar que la sección de bookmarks esté visible
    const bookmarksSection = page.locator('text="📚 Últimos Bookmarks"');
    await expect(bookmarksSection).toBeVisible();
    
    // Verificar que haya al menos una tarjeta de bookmark
    const bookmarkCards = page.locator('[class*="BookmarkCard"]');
    await expect(bookmarkCards).toHaveCount({ min: 1 });
  });
});