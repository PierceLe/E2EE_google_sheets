// AES-GCM helpers
export async function genAesKey() {
  return crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']
  );
}

export async function importAesKey(raw) {
  return crypto.subtle.importKey('raw', raw, { name: 'AES-GCM' }, true, ['encrypt', 'decrypt']);
}

export async function exportAesKey(key) {
  return new Uint8Array(await crypto.subtle.exportKey('raw', key));
}

export async function aesEncrypt(key, bytes) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, bytes));
  return { iv, ct };
}

export async function aesDecrypt(key, iv, ct) {
  const pt = new Uint8Array(await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ct));
  return pt;
}
