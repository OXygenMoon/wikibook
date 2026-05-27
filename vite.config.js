import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  base: '/static/oj-vue/',
  plugins: [vue()],
  build: {
    modulePreload: false,
    outDir: 'static/oj-vue',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        'src/oj-admin.js': 'frontend/src/oj-admin.js',
        'src/oj-public.js': 'frontend/src/oj-public.js',
      },
    },
  },
});
