import { computed, ref } from 'vue';
import { resolveInviteUrl } from './syncUrls.js';

const ADMIN_PRESENCE_TOPIC = 'oj-sync:presence:admins';
const STUDENT_PRESENCE_TOPIC = 'oj-sync:presence:students';
const ADMIN_INVITE_TOPIC = 'oj-sync:invites:admins';
const PRESENCE_INTERVAL_MS = 10000;
const PRESENCE_TTL_MS = 30000;
const INVITE_TTL_MS = 90000;
const wsConnecting = 0;
const wsOpen = 1;

function now() {
  return Date.now();
}

function createId(prefix = 'sync') {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${now()}-${Math.random().toString(16).slice(2)}`;
}

function userTopic(userId) {
  return `oj-sync:user:${userId}`;
}

function normalizeUser(user = {}) {
  return {
    id: user.id,
    name: user.name || user.realName || user.username || '匿名用户',
    username: user.username || '',
    isAdmin: Boolean(user.isAdmin || user.isSuperAdmin),
    isSuperAdmin: Boolean(user.isSuperAdmin || user.isAdmin),
  };
}

function normalizeProblem(problem = {}, codeUrl = '') {
  return {
    id: problem.id,
    slug: problem.slug,
    code: problem.code || '',
    title: problem.title || '题目',
    codeUrl: codeUrl || problem.codeUrl || problem.url || '',
  };
}

export function useCodeSyncInvites({ currentUser, inviteUrl, serverUrl }) {
  const user = normalizeUser(currentUser);
  const endpoint = resolveInviteUrl(inviteUrl, serverUrl);
  const socketState = ref('idle');
  const admins = ref([]);
  const codingStudents = ref([]);
  const incomingInvites = ref([]);
  const outgoingInvite = ref(null);
  const activeSession = ref(null);
  const pickerOpen = ref(false);
  const pickerProblem = ref(null);
  const notice = ref('');

  let socket = null;
  let presenceTimer = 0;
  let pruneTimer = 0;
  let currentCodeContext = null;
  const adminPresence = new Map();
  const studentPresence = new Map();

  const isAdmin = computed(() => user.isAdmin);
  const hasAdminsOnline = computed(() => admins.value.length > 0);

  function publish(topic, data) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ type: 'publish', topic, data }));
    return true;
  }

  function subscribe(topics) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'subscribe', topics }));
  }

  function setNotice(message) {
    notice.value = message;
    window.setTimeout(() => {
      if (notice.value === message) notice.value = '';
    }, 3200);
  }

  function inviteChannelUnavailableMessage() {
    return `同步邀请服务未连接，请确认 ${endpoint} 已启动。`;
  }

  function prunePresence() {
    const cutoff = now() - PRESENCE_TTL_MS;
    for (const [key, value] of adminPresence.entries()) {
      if (value.seenAt < cutoff) adminPresence.delete(key);
    }
    for (const [key, value] of studentPresence.entries()) {
      if (value.seenAt < cutoff) studentPresence.delete(key);
    }
    admins.value = Array.from(adminPresence.values()).sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    codingStudents.value = Array.from(studentPresence.values()).sort((a, b) => b.seenAt - a.seenAt);
    incomingInvites.value = incomingInvites.value.filter((invite) => invite.expiresAt > now());
    if (outgoingInvite.value?.expiresAt <= now()) outgoingInvite.value = null;
  }

  function publishPresence() {
    if (!user.id) return;
    if (user.isAdmin) {
      publish(ADMIN_PRESENCE_TOPIC, {
        kind: 'admin-presence',
        user,
        seenAt: now(),
      });
      return;
    }
    if (currentCodeContext?.problem?.id) {
      publish(STUDENT_PRESENCE_TOPIC, {
        kind: 'student-code-presence',
        user,
        problem: currentCodeContext.problem,
        seenAt: now(),
      });
    }
  }

  function connect({ force = false } = {}) {
    if (!user.id) return;
    if (socket && !force && [wsConnecting, wsOpen].includes(socket.readyState)) return;
    if (socket) {
      try {
        socket.close();
      } catch (error) {
        // Ignore stale sockets while retrying the invite channel.
      }
      socket = null;
    }
    socketState.value = 'connecting';
    const nextSocket = new WebSocket(endpoint);
    socket = nextSocket;
    nextSocket.addEventListener('open', () => {
      if (socket !== nextSocket) return;
      socketState.value = 'connected';
      const topics = [userTopic(user.id)];
      if (user.isAdmin) topics.push(ADMIN_INVITE_TOPIC, STUDENT_PRESENCE_TOPIC);
      else topics.push(ADMIN_PRESENCE_TOPIC);
      subscribe(topics);
      publishPresence();
      presenceTimer = window.setInterval(publishPresence, PRESENCE_INTERVAL_MS);
      pruneTimer = window.setInterval(prunePresence, 4000);
    });
    nextSocket.addEventListener('message', (event) => {
      if (socket !== nextSocket) return;
      let message = {};
      try {
        message = JSON.parse(event.data || '{}');
      } catch (error) {
        return;
      }
      if (message.type !== 'publish' || !message.data) return;
      handleMessage(message.topic, message.data);
    });
    nextSocket.addEventListener('close', () => {
      if (socket !== nextSocket) return;
      if (socketState.value === 'connecting' || socketState.value === 'error') {
        socketState.value = 'error';
        setNotice(inviteChannelUnavailableMessage());
      } else {
        socketState.value = 'closed';
      }
      socket = null;
      window.clearInterval(presenceTimer);
      window.clearInterval(pruneTimer);
    });
    nextSocket.addEventListener('error', () => {
      if (socket !== nextSocket) return;
      socketState.value = 'error';
      setNotice(inviteChannelUnavailableMessage());
    });
  }

  function disconnect() {
    window.clearInterval(presenceTimer);
    window.clearInterval(pruneTimer);
    if (socket) socket.close();
    socket = null;
    socketState.value = 'closed';
  }

  function upsertIncomingInvite(invite) {
    if (invite.fromUser?.id === user.id) return;
    if (invite.targetUserId && invite.targetUserId !== user.id) return;
    const index = incomingInvites.value.findIndex((item) => item.id === invite.id);
    if (index >= 0) incomingInvites.value.splice(index, 1, invite);
    else incomingInvites.value.unshift(invite);
  }

  function handleMessage(topic, data) {
    if (data.kind === 'admin-presence' && !user.isAdmin && data.user?.id !== user.id) {
      adminPresence.set(data.user.id, { ...data.user, seenAt: data.seenAt || now() });
      prunePresence();
      return;
    }
    if (data.kind === 'student-code-presence' && user.isAdmin && data.user?.id !== user.id) {
      studentPresence.set(data.user.id, {
        ...data.user,
        problem: data.problem,
        seenAt: data.seenAt || now(),
      });
      prunePresence();
      return;
    }
    if (data.kind === 'sync-invite') {
      if (topic === ADMIN_INVITE_TOPIC && !user.isAdmin) return;
      upsertIncomingInvite(data.invite);
      return;
    }
    if (data.kind === 'sync-accepted' && data.targetUserId === user.id) {
      if (outgoingInvite.value?.id === data.session?.inviteId) outgoingInvite.value = null;
      activeSession.value = data.session;
      setNotice(`${data.fromUser?.name || '对方'} 已接受同步邀请。`);
      return;
    }
    if (data.kind === 'sync-declined' && data.targetUserId === user.id) {
      if (outgoingInvite.value?.id === data.inviteId) outgoingInvite.value = null;
      setNotice(data.reason || `${data.fromUser?.name || '对方'} 暂时无法同步。`);
    }
  }

  function createSession(problem, studentUser, adminUser, inviteId) {
    return {
      id: inviteId,
      inviteId,
      room: `problem-${problem.id}-session-${inviteId}`,
      problem,
      studentUser,
      adminUser,
      ownerUserId: studentUser.id,
    };
  }

  function createInvite({ problem, toUser = null, fromProblem = null }) {
    const inviteId = createId('invite');
    const normalizedProblem = normalizeProblem(problem || fromProblem);
    const studentUser = user.isAdmin ? toUser : user;
    const adminUser = user.isAdmin ? user : null;
    return {
      id: inviteId,
      fromUser: user,
      targetUserId: toUser?.id || null,
      targetRole: user.isAdmin ? 'student' : 'admin',
      problem: normalizedProblem,
      studentUser,
      adminUser,
      session: createSession(normalizedProblem, studentUser, adminUser || { id: null, name: '超管' }, inviteId),
      createdAt: now(),
      expiresAt: now() + INVITE_TTL_MS,
    };
  }

  function requestAdminSync(problem) {
    if (socketState.value !== 'connected') {
      if (!socket || socket.readyState > wsOpen) connect({ force: true });
      const message = inviteChannelUnavailableMessage();
      setNotice(message);
      return { ok: false, message };
    }
    if (user.isAdmin) {
      pickerProblem.value = normalizeProblem(problem);
      pickerOpen.value = true;
      return { ok: true };
    }
    const invite = createInvite({ problem });
    outgoingInvite.value = { ...invite, status: 'pending' };
    publish(ADMIN_INVITE_TOPIC, { kind: 'sync-invite', invite });
    setNotice(hasAdminsOnline.value ? '已向在线超管发送同步邀请。' : '已发送邀请，正在等待超管在线响应。');
    return { ok: true, invite };
  }

  function inviteStudent(student) {
    if (!user.isAdmin || !student?.id) return;
    const problem = student.problem || pickerProblem.value;
    const invite = createInvite({ problem, toUser: student });
    outgoingInvite.value = { ...invite, status: 'pending' };
    publish(userTopic(student.id), { kind: 'sync-invite', invite });
    pickerOpen.value = false;
    setNotice(`已邀请 ${student.name} 同步。`);
  }

  function acceptInvite(invite) {
    const adminUser = user.isAdmin ? user : invite.adminUser;
    const studentUser = user.isAdmin ? invite.studentUser : user;
    const session = {
      ...invite.session,
      adminUser,
      studentUser,
      ownerUserId: studentUser.id,
    };
    incomingInvites.value = incomingInvites.value.filter((item) => item.id !== invite.id);
    activeSession.value = session;
    publish(userTopic(invite.fromUser.id), {
      kind: 'sync-accepted',
      targetUserId: invite.fromUser.id,
      fromUser: user,
      session,
    });
  }

  function declineInvite(invite) {
    incomingInvites.value = incomingInvites.value.filter((item) => item.id !== invite.id);
    publish(userTopic(invite.fromUser.id), {
      kind: 'sync-declined',
      targetUserId: invite.fromUser.id,
      fromUser: user,
      inviteId: invite.id,
      reason: invite.reason,
    });
  }

  function setCodeContext(context) {
    currentCodeContext = context?.problem?.id ? {
      ...context,
      problem: normalizeProblem(context.problem, context.codeUrl),
    } : null;
    publishPresence();
  }

  function clearActiveSession() {
    activeSession.value = null;
  }

  function closePicker() {
    pickerOpen.value = false;
  }

  function outgoingForProblem(problemId) {
    const invite = outgoingInvite.value;
    if (!invite || invite.problem?.id !== problemId) return null;
    return invite;
  }

  return {
    socketState,
    admins,
    codingStudents,
    incomingInvites,
    outgoingInvite,
    activeSession,
    pickerOpen,
    pickerProblem,
    notice,
    isAdmin,
    hasAdminsOnline,
    connect,
    disconnect,
    setCodeContext,
    requestAdminSync,
    inviteStudent,
    acceptInvite,
    declineInvite,
    clearActiveSession,
    closePicker,
    outgoingForProblem,
  };
}
