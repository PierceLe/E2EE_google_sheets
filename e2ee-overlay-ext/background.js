// background.js
const GAPI_ORIGIN = 'https://www.googleapis.com';
let cachedToken = null; // store short-lived access token

async function getAccessTokenInteractive() {
  // Uses chrome.identity API to do OAuth in extension
  return new Promise((resolve, reject) => {
    chrome.identity.getAuthToken({ interactive: true }, token => {
      if (chrome.runtime.lastError || !token) {
        reject(chrome.runtime.lastError || new Error('No token'));
      } else {
        resolve(token);
      }
    });
  });
}

async function gapiFetch(path, { method = 'GET', headers = {}, body } = {}) {
  if (!cachedToken) cachedToken = await getAccessTokenInteractive();
  const res = await fetch(`${GAPI_ORIGIN}${path}`, {
    method,
    headers: { 'Authorization': `Bearer ${cachedToken}`, ...headers },
    body
  });
  if (res.status === 401) {
    // Token may be revoked; try once more
    cachedToken = null;
    return gapiFetch(path, { method, headers, body });
  }
  return res;
}

// --- Drive helpers -------------------------------------------------

async function findOrCreateDocFile(docId) {
  // Look for E2EE_Doc_<docId>.json
  const q = encodeURIComponent(`name = 'E2EE_Doc_${docId}.json' and trashed = false`);
  const resp = await gapiFetch(`/drive/v3/files?q=${q}&spaces=drive&fields=files(id,name,modifiedTime)`);
  const data = await resp.json();
  if (data.files && data.files.length) {
    return data.files[0]; // { id, name, modifiedTime }
  }
  // Create it
  const metadata = {
    name: `E2EE_Doc_${docId}.json`,
    mimeType: 'application/json'
  };
  const boundary = '-------e2ee-' + Math.random().toString(36).slice(2);
  const body =
    `--${boundary}\r\n` +
    'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
    JSON.stringify(metadata) + '\r\n' +
    `--${boundary}\r\n` +
    'Content-Type: application/json\r\n\r\n' +
    JSON.stringify({ version: 1, ops: [], snapshot: null, keyring: {} }) + '\r\n' +
    `--${boundary}--`;

  const create = await gapiFetch('/upload/drive/v3/files?uploadType=multipart&fields=id,name,modifiedTime', {
    method: 'POST',
    headers: { 'Content-Type': `multipart/related; boundary=${boundary}` },
    body
  });
  return create.json(); // { id, name, modifiedTime }
}

async function readDocFile(fileId) {
  const metaResp = await gapiFetch(`/drive/v3/files/${fileId}?fields=id,name,modifiedTime,etag`);
  const meta = await metaResp.json();
  const mediaResp = await gapiFetch(`/drive/v3/files/${fileId}?alt=media`);
  const text = await mediaResp.text();
  return { meta, text };
}

async function updateDocFile(fileId, jsonString) {
  // Use media upload
  const resp = await gapiFetch(`/upload/drive/v3/files/${fileId}?uploadType=media`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: jsonString
  });
  return resp.json();
}

// --- Messaging -----------------------------------------------------
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.type === 'DRIVE_FIND_OR_CREATE') {
        const f = await findOrCreateDocFile(msg.docId);
        sendResponse({ ok: true, file: f });
      } else if (msg.type === 'DRIVE_READ') {
        const { meta, text } = await readDocFile(msg.fileId);
        sendResponse({ ok: true, meta, text });
      } else if (msg.type === 'DRIVE_UPDATE') {
        const upd = await updateDocFile(msg.fileId, msg.json);
        sendResponse({ ok: true, file: upd });
      } else {
        sendResponse({ ok: false, error: 'Unknown message' });
      }
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  // Keep channel open for async response
  return true;
});
