// neural-bookmark-ui/playwright.config.ts

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    timeout: 30 * 1000,
    expect: { timeout: 5000 },
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: 1, // Añadimos un reintento por inestabilidad de red WSL2
    workers: 1, 
    reporter: 'html',
    use: {
        // URL del Frontend (Vite)
        baseURL: 'http://192.168.1.40:5173', 
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
      },
    
      projects: [
        {
          name: 'chromium',
          use: { ...devices['Desktop Chrome'] }, 
        }
      ],
    
      // IMPORTANTE: Levantar el frontend automáticamente si no está corriendo
      webServer: {
        command: 'npm run dev -- --host',
        url: 'http://192.168.1.40:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
      },
    });