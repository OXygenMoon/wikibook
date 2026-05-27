const EVENTS_PATH = '/events';
const COLLABORATION_PATH = '/collaboration';

function trimTrailingSlash(url = '') {
  return url.replace(/\/+$/, '');
}

function stripKnownSuffix(url = '') {
  const normalized = trimTrailingSlash(url);
  if (normalized.endsWith(EVENTS_PATH)) return normalized.slice(0, -EVENTS_PATH.length);
  if (normalized.endsWith(COLLABORATION_PATH)) return normalized.slice(0, -COLLABORATION_PATH.length);
  return normalized;
}

export function fallbackSyncServerUrl() {
  if (typeof window === 'undefined') return 'ws://localhost:4444';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.hostname}:4444`;
}

export function resolveSyncServerUrl(serverUrl = '') {
  return stripKnownSuffix(serverUrl) || fallbackSyncServerUrl();
}

export function resolveInviteUrl(inviteUrl = '', serverUrl = '') {
  return trimTrailingSlash(inviteUrl) || `${resolveSyncServerUrl(serverUrl)}${EVENTS_PATH}`;
}

export function resolveCollaborationUrl(collaborationUrl = '', serverUrl = '') {
  return trimTrailingSlash(collaborationUrl) || `${resolveSyncServerUrl(serverUrl)}${COLLABORATION_PATH}`;
}
