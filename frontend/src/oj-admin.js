import { createApp } from 'vue';
import AdminOjShell from './oj/admin/AdminOjShell.vue';
import AdminProblemManager from './oj/admin/AdminProblemManager.vue';
import ProblemFilesWorkspace from './oj/admin/ProblemFilesWorkspace.vue';
import './oj/admin/oj-admin.css';

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

const shellRoot = document.getElementById('oj-admin-shell-app');
if (shellRoot) {
  createApp(AdminOjShell, readPayload('oj-admin-shell-payload')).mount(shellRoot);
}

const problemsRoot = document.getElementById('oj-admin-problems-app');
if (problemsRoot) {
  createApp(AdminProblemManager, readPayload('oj-admin-problems-payload')).mount(problemsRoot);
}

const filesRoot = document.getElementById('oj-problem-files-app');
if (filesRoot) {
  createApp(ProblemFilesWorkspace, readPayload('oj-problem-files-payload')).mount(filesRoot);
}
