import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  build: {
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
