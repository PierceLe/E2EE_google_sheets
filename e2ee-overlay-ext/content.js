// content.js (top)
(async () => {
   
  const aesModule = await import(chrome.runtime.getURL('crypto/aes.js'));
  const rsaModule = await import(chrome.runtime.getURL('crypto/rsa.js'));

  const {
    genAesKey, importAesKey, exportAesKey, aesEncrypt, aesDecrypt
  } = aesModule;
  
const DOC_ID_RE = /\/document\/d\/([a-zA-Z0-9-_]+)/;

let currentDocId = (location.pathname.match(DOC_ID_RE) || [])[1];

const urlObserver = new MutationObserver(() => {
  const m = location.pathname.match(DOC_ID_RE);
  const newId = m && m[1];
  if (newId && newId !== currentDocId) {
    currentDocId = newId;
    teardownOverlay();   // remove timers, listeners, DOM nodes
    bootForDoc(currentDocId); // re-run the init (ensureKeysAndFile, etc.)
  }
});
urlObserver.observe(document.documentElement, { childList: true, subtree: true });

// Implement teardownOverlay() to clear intervals/timeouts and remove e2ee-overlay-root

let docId = (location.pathname.match(DOC_ID_RE) || [])[1];
if (!docId) console.warn('E2EE overlay: could not detect Google Doc ID');

let driveFileId = null;
let aesKey = null;           // CryptoKey
let aesKeyRaw = null;        // Uint8Array raw
let state = { ops: [], snapshot: null, keyring: {} }; // decrypted local
let lastServerJSON = '';     // last ciphertext JSON string we pulled
let syncing = false;

// --- UI Mount -----------------------------------------------------
function mountOverlay() {
  // Don’t interfere with Docs toolbar clicks; only overlay the canvas region
  const root = document.createElement('div');
  root.id = 'e2ee-overlay-root';

  const page = document.createElement('div');
  page.id = 'e2ee-page';

  const editor = document.createElement('div');
  editor.id = 'e2ee-editor';
  editor.contentEditable = 'true';
  editor.spellcheck = false;
  editor.autocapitalize = 'off';
  editor.autocorrect = 'off';
  editor.addEventListener('beforeinput', onBeforeInput, { passive: false });
  editor.addEventListener('input', onInput);
  editor.addEventListener('keydown', onKeyDown);

  root.appendChild(page);
  root.appendChild(editor);
  document.documentElement.appendChild(root);
}

function getEditor() {
  return document.getElementById('e2ee-editor');
}

// --- Minimal CRDT/OT (index-based) --------------------------------
// For a robust app use ProseMirror steps or a proper CRDT (e.g., Yjs). Here we keep
// a simple op log: {t:'ins'|'del', at:number, text?:string, ver:number, ts:number, client:string}

let version = 0;
const clientId = crypto.randomUUID();

function recordInsert(at, text) {
  state.ops.push({ t: 'ins', at, text, ver: ++version, ts: Date.now(), client: clientId });
}
function recordDelete(at, count) {
  state.ops.push({ t: 'del', at, count, ver: ++version, ts: Date.now(), client: clientId });
}
function materializeSnapshot() {
  // Apply ops to produce plaintext
  let s = '';
  for (const op of state.ops) {
    if (op.t === 'ins') {
      s = s.slice(0, op.at) + op.text + s.slice(op.at);
    } else if (op.t === 'del') {
      s = s.slice(0, op.at) + s.slice(op.at + op.count);
    }
  }
  state.snapshot = { ver: version, text: s };
  return s;
}
function setEditorText(s) {
  const ed = getEditor();
  ed.textContent = s; // plaintext only
}

// --- Editor events -------------------------------------------------
function onBeforeInput(e) {
  // Keep it plaintext: cancel rich inserts
  if (e.inputType === 'insertFromPaste' || e.inputType === 'insertFromDrop') {
    e.preventDefault();
    const text = (e.dataTransfer && e.dataTransfer.getData('text')) ||
                 (e.clipboardData && e.clipboardData.getData('text')) || '';
    insertAtSelection(text);
  }
}
function onKeyDown(e) {
  // Example: block Ctrl+F leaking to page find; optional
  // if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') e.preventDefault();
}
function onInput(e) {
  // Compute a tiny delta from previous materialized text
  // For a robust editor, use a diff (e.g., fast-diff). Here we recompute index changes simply.
  scheduleSync();
}

function getSelectionIndex() {
  const sel = getSelection();
  const ed = getEditor();
  if (!sel || !sel.anchorNode) return { start: 0, end: 0 };
  const range = sel.getRangeAt(0).cloneRange();
  range.selectNodeContents(ed);
  range.setEnd(sel.anchorNode, sel.anchorOffset);
  const start = range.toString().length;
  let end = start;
  if (!sel.isCollapsed) {
    const r2 = sel.getRangeAt(0).cloneRange();
    r2.selectNodeContents(ed);
    r2.setEnd(sel.focusNode, sel.focusOffset);
    end = r2.toString().length;
  }
  return { start: Math.min(start, end), end: Math.max(start, end) };
}

function insertAtSelection(text) {
  const { start, end } = getSelectionIndex();
  if (end > start) recordDelete(start, end - start);
  recordInsert(start, text);
  const s = materializeSnapshot();
  setEditorText(s);
  placeCaret(start + text.length);
  scheduleSync();
}

function placeCaret(pos) {
  const ed = getEditor();
  ed.focus();
  const range = document.createRange();
  const sel = getSelection();
  // Walk text nodes to set caret; here we assume a single text node
  const tn = ed.firstChild || ed;
  range.setStart(tn, Math.min(pos, (tn.textContent || '').length));
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
}

// content.js
function sendMessageSafe(msg, { retries = 1, retryDelayMs = 250 } = {}) {
  return new Promise((resolve, reject) => {
    // If the extension was reloaded, chrome.runtime.id will be undefined.
    if (!chrome?.runtime?.id) {
      return reject(new Error('Extension was reloaded; refresh this tab.'));
    }

    chrome.runtime.sendMessage(msg, (resp) => {
      const err = chrome.runtime.lastError;
      if (err) {
        const m = String(err.message || err);
        // Common transient: "Extension context invalidated."
        if (/context invalidated/i.test(m) && retries > 0) {
          setTimeout(() => {
            sendMessageSafe(msg, { retries: retries - 1, retryDelayMs }).then(resolve, reject);
          }, retryDelayMs);
          return;
        }
        return reject(new Error(m));
      }
      resolve(resp);
    });
  });
}


// --- Crypto state --------------------------------------------------
async function ensureKeysAndFile() {
  // 1) Create/find Drive file
  const resp1 = await sendMessageSafe({ type: 'DRIVE_READ', fileId: driveFileId });
  if (!resp1.ok) throw new Error(resp1.error);
  driveFileId = resp1.file.id;

  // 2) Read existing ciphertext JSON
  const resp2 = await sendMessageSafe({ type: 'DRIVE_READ', fileId: driveFileId });
  if (!resp2.ok) throw new Error(resp2.error);
  lastServerJSON = resp2.text || '';

  // 3) If first time, generate AES key; else load from keyring
  const serverObj = lastServerJSON ? JSON.parse(lastServerJSON) : null;
  if (serverObj && serverObj.keyring && serverObj.keyring.self) {
    // In a real app, unwrap AES with your RSA private key.
    const raw = base64ToBytes(serverObj.keyring.self);
    aesKey = await importAesKey(raw);
    aesKeyRaw = raw;
    state = serverObj; // keep ciphertext fields? (we’ll reassign below)
  } else {
    aesKey = await genAesKey();
    aesKeyRaw = await exportAesKey(aesKey);
    // Store your wrapped key in keyring (for now self = raw base64 for demo ONLY)
  }

  // 4) Decrypt latest plaintext (if exists)
  if (serverObj && serverObj.cipher) {
    const iv = base64ToBytes(serverObj.cipher.iv);
    const ct = base64ToBytes(serverObj.cipher.ct);
    const pt = await aesDecrypt(aesKey, iv, ct);
    state = JSON.parse(new TextDecoder().decode(pt));
  } else if (!state.ops) {
    state = { ops: [], snapshot: null, keyring: {} };
  }

  // 5) Render
  const s = materializeSnapshot();
  setEditorText(s);
}

function bytesToBase64(u8) {
  let s = '';
  u8.forEach(b => s += String.fromCharCode(b));
  return btoa(s);
}
function base64ToBytes(b64) {
  const s = atob(b64);
  const u8 = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u8[i] = s.charCodeAt(i);
  return u8;
}



// --- Sync loop -----------------------------------------------------
let syncTimer = null;
let _unloading = false;
window.addEventListener('pagehide', () => { _unloading = true; }, { once: true });
window.addEventListener('beforeunload', () => { _unloading = true; }, { once: true });

function safeSchedule(fn, delay) {
  if (_unloading) return;
  return setTimeout(() => { if (!_unloading) fn(); }, delay);
}

// Use safeSchedule instead of setTimeout for debounced sync:
function scheduleSync() {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = safeSchedule(doSync, 600);
}


async function doSync() {
  if (syncing) return;
  syncing = true;
  try {
    // 1) Materialize + serialize plaintext state
    const s = materializeSnapshot();
    const payload = JSON.stringify({ ops: state.ops, snapshot: state.snapshot });

    // 2) Encrypt payload
    const { iv, ct } = await aesEncrypt(aesKey, new TextEncoder().encode(payload));

    // 3) Build server envelope
    const serverDoc = {
      version: 1,
      cipher: { iv: bytesToBase64(iv), ct: bytesToBase64(ct) },
      keyring: { self: bytesToBase64(aesKeyRaw) } // DEMO ONLY; replace with RSA-wrapped for each collaborator
    };
    const serverJSON = JSON.stringify(serverDoc);

    // 4) If unchanged, skip
    if (serverJSON === lastServerJSON) return;
    lastServerJSON = serverJSON;

    // 5) Upload
    const resp = await sendMessageSafe({ type: 'DRIVE_READ', fileId: driveFileId });
    if (!resp.ok) console.warn('Upload failed:', resp.error);
  } finally {
    syncing = false;
  }
}

// --- Boot ----------------------------------------------------------
(async function boot() {
  mountOverlay();

  // Prevent the native Docs editor from stealing focus
  // (We don’t type into it at all.)
  document.addEventListener('keydown', e => {
    // Optional additional guards
  }, true);

  await ensureKeysAndFile();

  // Polling for external updates (naive). Replace with Realtime API or push later.
  setInterval(async () => {
    if (!driveFileId || syncing) return;
    const resp = await sendMessageSafe({ type: 'DRIVE_READ', fileId: driveFileId });
    if (resp.ok && resp.text && resp.text !== lastServerJSON) {
      lastServerJSON = resp.text;
      const obj = JSON.parse(resp.text);
      if (obj.cipher) {
        const pt = await aesDecrypt(aesKey, base64ToBytes(obj.cipher.iv), base64ToBytes(obj.cipher.ct));
        state = JSON.parse(new TextDecoder().decode(pt));
        const s = materializeSnapshot();
        setEditorText(s);
      }
    }
  }, 2500);
})();




})();


