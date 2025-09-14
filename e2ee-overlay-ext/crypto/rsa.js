export async function importRsaPublicKey(spkiBytes) {
  return crypto.subtle.importKey(
    'spki', spkiBytes,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    true, ['encrypt']
  );
}

export async function importRsaPrivateKey(pkcs8Bytes) {
  return crypto.subtle.importKey(
    'pkcs8', pkcs8Bytes,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    true, ['decrypt']
  );
}

export async function wrapAesKey(aesKeyRaw, rsaPubKey) {
  // Encrypt AES raw key under RSA-OAEP
  return new Uint8Array(await crypto.subtle.encrypt(
    { name: 'RSA-OAEP' }, rsaPubKey, aesKeyRaw
  ));
}

export async function unwrapAesKey(wrapped, rsaPrivKey) {
  return new Uint8Array(await crypto.subtle.decrypt(
    { name: 'RSA-OAEP' }, rsaPrivKey, wrapped
  ));
}
