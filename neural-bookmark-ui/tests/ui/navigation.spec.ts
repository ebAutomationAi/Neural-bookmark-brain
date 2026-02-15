// tests/ui/navigation.spec.ts - Tests para navegación
import { test, expect } from '../setup';

test.describe('Navegación', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('debería navegar al Dashboard', async ({ page }) => {
    // Verificar que ya estamos en el dashboard
    await expect(page).toHaveURL(/\/$/);
    
    // Verificar elementos del dashboard
    await expect(page.locator('text="📊 Dashboard"')).toBeVisible();
  });

  test('debería navegar a Bookmarks', async ({ page }) => {
    // Abrir sidebar si es mobile
    const sidebarToggle = page.locator('button:has-text("Abrir menú")');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
    
    // Navegar a Bookmarks
    const bookmarksLink = page.locator('a:has-text("📚 Todos los Bookmarks")');
    await bookmarksLink.click();
    
    // Verificar URL
    await expect(page).toHaveURL(/\/bookmarks$/);
    
    // Verificar que la página de bookmarks cargó
    await expect(page.locator('text="📚 Todos los Bookmarks"')).toBeVisible();
  });

  test('debería navegar a Estadísticas', async ({ page }) => {
    // Abrir sidebar
    const sidebarToggle = page.locator('button:has-text("Abrir menú")');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
    
    // Navegar a Estadísticas
    const statsLink = page.locator('a:has-text("📊 Estadísticas")');
    await statsLink.click();
    
    // Verificar URL
    await expect(page).toHaveURL(/\/stats$/);
    
    // Verificar que la página de estadísticas cargó
    await expect(page.locator('text="📊 Estadísticas Detalladas"')).toBeVisible();
  });

  test('debería navegar a Categorías', async ({ page }) => {
    // Abrir sidebar
    const sidebarToggle = page.locator('button:has-text("Abrir menú")');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
    
    // Navegar a Categorías
    const categoriesLink = page.locator('a:has-text("📂 Categorías")');
    await categoriesLink.click();
    
    // Verificar URL
    await expect(page).toHaveURL(/\/categories$/);
    
    // Verificar mensaje de próximamente
    await expect(page.locator('text="Próximamente"')).toBeVisible();
  });

  test('debería navegar a Tags', async ({ page }) => {
    // Abrir sidebar
    const sidebarToggle = page.locator('button:has-text("Abrir menú")');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
    
    // Navegar a Tags
    const tagsLink = page.locator('a:has-text("🏷️ Tags")');
    await tagsLink.click();
    
    // Verificar URL
    await expect(page).toHaveURL(/\/tags$/);
    
    // Verificar mensaje de próximamente
    await expect(page.locator('text="Próximamente"')).toBeVisible();
  });

  test('debería navegar a Configuración', async ({ page }) => {
    // Abrir sidebar
    const sidebarToggle = page.locator('button:has-text("Abrir menú")');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
    
    // Navegar a Configuración
    const settingsLink = page.locator('a:has-text("⚙️ Configuración")');
    await settingsLink.click();
    
    // Verificar URL
    await expect(page).toHaveURL(/\/settings$/);
    
    // Verificar mensaje de próximamente
    await expect(page.locator('text="Próximamente"')).toBeVisible();
  });

  test('debería mostrar/ocultar el sidebar en mobile', async ({ page }) => {
    // Forzar viewport mobile
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Recargar para aplicar el cambio
    await page.goto('/');
    
    // Verificar que el botón de toggle esté visible
    const toggleButton = page.locator('button:has(svg)');
    await expect(toggleButton).toBeVisible();
    
    // Verificar que el sidebar esté oculto inicialmente
    const sidebar = page.locator('[class*="Sidebar"]');
    await expect(sidebar).not.toBeVisible();
    
    // Abrir sidebar
    await toggleButton.click();
    await expect(sidebar).toBeVisible();
    
    // Cerrar sidebar
    await toggleButton.click();
    await expect(sidebar).not.toBeVisible();
  });
});