// tests/ui/search.spec.ts - Tests para búsqueda
import { test, expect } from '../setup';

test.describe('Búsqueda', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('debería mostrar la barra de búsqueda', async ({ page }) => {
    // Verificar que la barra de búsqueda esté visible
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    await expect(searchInput).toBeVisible();
    
    // Verificar que el botón de búsqueda esté visible
    const searchButton = page.locator('button:has-text("Buscar")');
    await expect(searchButton).toBeVisible();
  });

  test('debería permitir ingresar texto en la búsqueda', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    
    // Escribir en el input
    await searchInput.fill('react');
    
    // Verificar que el texto se ingresó correctamente
    await expect(searchInput).toHaveValue('react');
  });

  test('debería navegar a la página de búsqueda al hacer clic en buscar', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    const searchButton = page.locator('button:has-text("Buscar")');
    
    // Ingresar texto y buscar
    await searchInput.fill('react');
    await searchButton.click();
    
    // Verificar que navegamos a la página de búsqueda
    await expect(page).toHaveURL(/\/search\?q=/);
  });

  test('debería limpiar la búsqueda', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    const clearButton = page.locator('button[aria-label="Limpiar búsqueda"]');
    
    // Ingresar texto
    await searchInput.fill('test');
    
    // Verificar que el botón de limpiar aparece
    await expect(clearButton).toBeVisible();
    
    // Limpiar
    await clearButton.click();
    
    // Verificar que el input está vacío
    await expect(searchInput).toHaveValue('');
  });

  test('debería mostrar resultados de búsqueda', async ({ page }) => {
    // Navegar directamente a la página de búsqueda
    await page.goto('/search?q=react');
    
    // Esperar a que carguen los resultados
    await page.waitForTimeout(1500);
    
    // Verificar que la página de búsqueda cargó
    await expect(page.locator('text="🔍 Búsqueda Avanzada"')).toBeVisible();
    
    // Verificar que hay resultados o mensaje apropiado
    const results = page.locator('[class*="BookmarkCard"]');
    const noResults = page.locator('text="No se encontraron resultados"');
    
    // Debería haber al menos uno de los dos
    expect(await results.count() > 0 || await noResults.isVisible()).toBe(true);
  });
});