import http from 'http';
import { WebSocketServer } from 'ws';
import * as Y from 'yjs';
import * as syncProtocol from 'y-protocols/sync';
import * as awarenessProtocol from 'y-protocols/awareness';
import * as encoding from 'lib0/encoding';
import * as decoding from 'lib0/decoding';

const EVENTS_PATH = '/events';
const COLLABORATION_PATH = '/collaboration';
const messageSync = 0;
const messageAwareness = 1;
const wsReadyStateConnecting = 0;
const wsReadyStateOpen = 1;
const pingTimeout = 30000;
const port = process.env.SYNC_SERVER_PORT || process.env.SIGNALING_PORT || process.env.PORT || 4444;

const setIfUndefined = (map, key, createValue) => {
  let value = map.get(key);
  if (value === undefined) {
    value = createValue();
    map.set(key, value);
  }
  return value;
};

const eventWss = new WebSocketServer({ noServer: true });
const collaborationWss = new WebSocketServer({ noServer: true });
const topics = new Map();
const collaborationDocs = new Map();

const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify({
    ok: true,
    eventsPath: EVENTS_PATH,
    collaborationPath: COLLABORATION_PATH,
  }));
});

const send = (conn, message) => {
  if (conn.readyState !== wsReadyStateConnecting && conn.readyState !== wsReadyStateOpen) {
    conn.close();
    return;
  }
  try {
    conn.send(JSON.stringify(message));
  } catch (error) {
    conn.close();
  }
};

class CollaborationDoc extends Y.Doc {
  constructor(name) {
    super({ gc: true });
    this.name = name;
    this.conns = new Map();
    this.awareness = new awarenessProtocol.Awareness(this);
    this.awareness.setLocalState(null);
    this.awareness.on('update', ({ added, updated, removed }, conn) => {
      const changedClients = added.concat(updated, removed);
      if (conn) {
        const controlledIds = this.conns.get(conn);
        if (controlledIds) {
          added.forEach((clientId) => controlledIds.add(clientId));
          removed.forEach((clientId) => controlledIds.delete(clientId));
        }
      }
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, messageAwareness);
      encoding.writeVarUint8Array(
        encoder,
        awarenessProtocol.encodeAwarenessUpdate(this.awareness, changedClients),
      );
      const payload = encoding.toUint8Array(encoder);
      this.conns.forEach((_, connection) => {
        sendCollaboration(this, connection, payload);
      });
    });
    this.on('update', (update) => {
      const encoder = encoding.createEncoder();
      encoding.writeVarUint(encoder, messageSync);
      syncProtocol.writeUpdate(encoder, update);
      const payload = encoding.toUint8Array(encoder);
      this.conns.forEach((_, connection) => {
        sendCollaboration(this, connection, payload);
      });
    });
  }
}

function getCollaborationDoc(docName) {
  return setIfUndefined(collaborationDocs, docName, () => new CollaborationDoc(docName));
}

function closeCollaborationConnection(doc, conn) {
  if (doc.conns.has(conn)) {
    const controlledIds = doc.conns.get(conn) || new Set();
    doc.conns.delete(conn);
    awarenessProtocol.removeAwarenessStates(doc.awareness, Array.from(controlledIds), null);
    if (doc.conns.size === 0) {
      collaborationDocs.delete(doc.name);
      doc.destroy();
    }
  }
  if (conn.readyState === wsReadyStateConnecting || conn.readyState === wsReadyStateOpen) {
    conn.close();
  }
}

function sendCollaboration(doc, conn, payload) {
  if (conn.readyState !== wsReadyStateConnecting && conn.readyState !== wsReadyStateOpen) {
    closeCollaborationConnection(doc, conn);
    return;
  }
  try {
    conn.send(payload, {}, (error) => {
      if (error) closeCollaborationConnection(doc, conn);
    });
  } catch (error) {
    closeCollaborationConnection(doc, conn);
  }
}

function handleCollaborationMessage(conn, doc, payload) {
  try {
    const encoder = encoding.createEncoder();
    const decoder = decoding.createDecoder(new Uint8Array(payload));
    const messageType = decoding.readVarUint(decoder);
    switch (messageType) {
      case messageSync:
        encoding.writeVarUint(encoder, messageSync);
        syncProtocol.readSyncMessage(decoder, encoder, doc, conn);
        if (encoding.length(encoder) > 1) {
          sendCollaboration(doc, conn, encoding.toUint8Array(encoder));
        }
        break;
      case messageAwareness:
        awarenessProtocol.applyAwarenessUpdate(
          doc.awareness,
          decoding.readVarUint8Array(decoder),
          conn,
        );
        break;
      default:
        break;
    }
  } catch (error) {
    console.error('[oj-sync] collaboration message failed', error);
  }
}

function setupCollaborationConnection(conn, request, docName) {
  conn.binaryType = 'arraybuffer';
  const doc = getCollaborationDoc(docName);
  doc.conns.set(conn, new Set());

  conn.on('message', (payload) => {
    handleCollaborationMessage(conn, doc, payload);
  });

  let pongReceived = true;
  const pingInterval = setInterval(() => {
    if (!pongReceived) {
      closeCollaborationConnection(doc, conn);
      clearInterval(pingInterval);
      return;
    }
    if (!doc.conns.has(conn)) {
      clearInterval(pingInterval);
      return;
    }
    pongReceived = false;
    try {
      conn.ping();
    } catch (error) {
      closeCollaborationConnection(doc, conn);
      clearInterval(pingInterval);
    }
  }, pingTimeout);

  conn.on('close', () => {
    closeCollaborationConnection(doc, conn);
    clearInterval(pingInterval);
  });
  conn.on('pong', () => {
    pongReceived = true;
  });

  const syncEncoder = encoding.createEncoder();
  encoding.writeVarUint(syncEncoder, messageSync);
  syncProtocol.writeSyncStep1(syncEncoder, doc);
  sendCollaboration(doc, conn, encoding.toUint8Array(syncEncoder));

  const awarenessStates = doc.awareness.getStates();
  if (awarenessStates.size > 0) {
    const awarenessEncoder = encoding.createEncoder();
    encoding.writeVarUint(awarenessEncoder, messageAwareness);
    encoding.writeVarUint8Array(
      awarenessEncoder,
      awarenessProtocol.encodeAwarenessUpdate(doc.awareness, Array.from(awarenessStates.keys())),
    );
    sendCollaboration(doc, conn, encoding.toUint8Array(awarenessEncoder));
  }
}

const onEventConnection = (conn) => {
  const subscribedTopics = new Set();
  let closed = false;
  let pongReceived = true;

  const pingInterval = setInterval(() => {
    if (!pongReceived) {
      conn.close();
      clearInterval(pingInterval);
      return;
    }
    pongReceived = false;
    try {
      conn.ping();
    } catch (error) {
      conn.close();
    }
  }, pingTimeout);

  conn.on('pong', () => {
    pongReceived = true;
  });

  conn.on('close', () => {
    subscribedTopics.forEach((topicName) => {
      const subscribers = topics.get(topicName) || new Set();
      subscribers.delete(conn);
      if (subscribers.size === 0) topics.delete(topicName);
    });
    subscribedTopics.clear();
    closed = true;
    clearInterval(pingInterval);
  });

  conn.on('message', (message) => {
    if (typeof message === 'string' || message instanceof Buffer) {
      message = JSON.parse(message);
    }
    if (!message?.type || closed) return;

    switch (message.type) {
      case 'subscribe':
        (message.topics || []).forEach((topicName) => {
          if (typeof topicName !== 'string') return;
          const topic = setIfUndefined(topics, topicName, () => new Set());
          topic.add(conn);
          subscribedTopics.add(topicName);
        });
        break;
      case 'unsubscribe':
        (message.topics || []).forEach((topicName) => {
          const subscribers = topics.get(topicName);
          if (subscribers) subscribers.delete(conn);
          subscribedTopics.delete(topicName);
        });
        break;
      case 'publish':
        if (!message.topic) return;
        {
          const receivers = topics.get(message.topic);
          if (!receivers) return;
          message.clients = receivers.size;
          receivers.forEach((receiver) => send(receiver, message));
        }
        break;
      case 'ping':
        send(conn, { type: 'pong' });
        break;
      default:
        break;
    }
  });
};

eventWss.on('connection', onEventConnection);
collaborationWss.on('connection', (conn, request, docName) => {
  setupCollaborationConnection(conn, request, docName);
});

server.on('upgrade', (request, socket, head) => {
  const requestUrl = new URL(request.url || '/', `http://${request.headers.host || 'localhost'}`);
  const pathname = requestUrl.pathname.replace(/\/+$/, '') || '/';

  if (pathname === EVENTS_PATH) {
    eventWss.handleUpgrade(request, socket, head, (ws) => {
      eventWss.emit('connection', ws, request);
    });
    return;
  }

  if (pathname.startsWith(COLLABORATION_PATH + '/')) {
    const docName = decodeURIComponent(pathname.slice(COLLABORATION_PATH.length + 1));
    collaborationWss.handleUpgrade(request, socket, head, (ws) => {
      collaborationWss.emit('connection', ws, request, docName);
    });
    return;
  }

  socket.write('HTTP/1.1 404 Not Found\r\n\r\n');
  socket.destroy();
});

server.listen(port, () => {
  console.log(`OJ sync server running on localhost:${port}`);
});
