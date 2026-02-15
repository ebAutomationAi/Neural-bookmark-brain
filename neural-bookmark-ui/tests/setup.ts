// tests/setup.ts - Configuración inicial para tests
import { test as base } from '@playwright/test';

// Extender test con fixtures personalizados
export const test = base.extend({
  // Fixture para la API
  apiContext: async ({ playwright }, use) => {
    const apiContext = await playwright.request.newContext({
      baseURL: 'http://192.168.1.40:8090',
    });
    await use(apiContext);
    await apiContext.dispose();
  },
  
  // Fixture para datos de prueba
  testData: async ({}, use) => {
    const testData = {
      testUrls: [
        'https://react.dev',
        'https://vitejs.dev',
        'https://tailwindcss.com',
        'https://www.typescriptlang.org',
      ],
      validUrl: 'https://developer.mozilla.org',
      invalidUrl: 'not-a-valid-url',
    };
    await use(testData);
  },
});

export { expect } from '@playwright/test';