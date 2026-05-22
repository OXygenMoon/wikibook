import { createApp } from 'vue';
import OjPublicShell from './oj/public/OjPublicShell.vue';
import './oj/public/oj-public.css';

function readPayload(id) {
  const node = document.getElementById(id);
  if (!node) return {};
  try {
    return JSON.parse(node.textContent || '{}');
  } catch (error) {
    console.error(`Unable to parse ${id}`, error);
    return {};
  }
}

const root = document.getElementById('oj-public-shell-app');
if (root) {
  createApp(OjPublicShell, readPayload('oj-public-shell-payload')).mount(root);
}
