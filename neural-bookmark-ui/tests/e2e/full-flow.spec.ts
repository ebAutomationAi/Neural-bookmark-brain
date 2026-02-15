// tests/e2e/full-flow.spec.ts - Tests de flujo completo
import { test, expect } from '../setup';

test.describe('Flujo Completo de Usuario', () => {
  
  test('flujo completo: navegar, buscar y agregar bookmark', async ({ page, testData }) => {
    // Paso 1: Cargar la página principal
    await test.step('Cargar página principal', async () => {
      await page.goto('/');
      await expect(page.locator('text="Neural Bookmark Brain"')).toBeVisible();
    });

    // Paso 2: Verificar estadísticas
    await test.step('Verificar estadísticas', async () => {
      await page.waitForTimeout(1000);
      await expect(page.locator('text="Total Bookmarks"')).toBeVisible();
    });

    // Paso 3: Navegar a Bookmarks
    await test.step('Navegar a Bookmarks', async () => {
      const sidebarToggle = page.locator('button:has-text("Abrir menú")');
      if (await sidebarToggle.isVisible()) {
        await sidebarToggle.click();
      }
      
      const bookmarksLink = page.locator('a:has-text("📚 Todos los Bookmarks")');
      await bookmarksLink.click();
      
      await expect(page).toHaveURL(/\/bookmarks$/);
      await expect(page.locator('text="📚 Todos los Bookmarks"')).toBeVisible();
    });

    // Paso 4: Buscar un bookmark
    await test.step('Buscar bookmark', async () => {
      const searchInput = page.locator('input[placeholder*="Buscar"]');
      await searchInput.fill('react');
      await searchInput.press('Enter');
      
      await page.waitForTimeout(1000);
      await expect(page).toHaveURL(/q=react/);
    });

    // Paso 5: Abrir modal para agregar nuevo bookmark
    await test.step('Abrir modal de agregar bookmark', async () => {
      await page.goto('/bookmarks');
      const addButton = page.locator('button:has-text("➕ Agregar Bookmark")');
      await addButton.click();
      
      await expect(page.locator('text="➕ Agregar Bookmark"')).toBeVisible();
    });

    // Paso 6: Ingresar URL y enviar
    await test.step('Agregar nuevo bookmark', async () => {
      const urlInput = page.locator('input[placeholder*="https://"]');
      await urlInput.fill(testData.validUrl);
      
      const submitButton = page.locator('button:has-text("🧠 Procesar Bookmark")');
      await submitButton.click();
      
      // Esperar a que se procese
      await page.waitForTimeout(2000);
    });

    // Paso 7: Verificar que el bookmark fue agregado
    await test.step('Verificar bookmark agregado', async () => {
      await page.reload();
      await page.waitForTimeout(1500);
      
      const bookmarkCards = page.locator('[class*="BookmarkCard"]');
      await expect(bookmarkCards).toHaveCount({ min: 1 });
    });

    // Paso 8: Navegar a Estadísticas
    await test.step('Navegar a Estadísticas', async () => {
      const sidebarToggle = page.locator('button:has-text("Abrir menú")');
      if (await sidebarToggle.isVisible()) {
        await sidebarToggle.click();
      }
      
      const statsLink = page.locator('a:has-text("📊 Estadísticas")');
      await statsLink.click();
      
      await expect(page).toHaveURL(/\/stats$/);
      await expect(page.locator('text="📊 Estadísticas Detalladas"')).toBeVisible();
    });

    // Paso 9: Verificar sección de categorías
    await test.step('Verificar categorías', async () => {
      await expect(page.locator('text="📂 Categorías"')).toBeVisible();
    });

    // Paso 10: Verificar sección de tags
    await test.step('Verificar tags', async () => {
      await expect(page.locator('text="🏷️ Tags Populares"')).toBeVisible();
    });
  });
});