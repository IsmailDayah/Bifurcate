// Modes + PKCS#7 — bifurcate/modes.py.
import { RoundKeys } from "./keyschedule.js";
import { decryptBlock, encryptBlock, BLOCK_BYTES } from "./cipher.js";
import { concat, xorBytes } from "./bytes.js";

export const MODE_CBC = 0;
export const MODE_ECB = 1;

export function pad(data: Uint8Array, bs = BLOCK_BYTES): Uint8Array {
  const n = bs - (data.length % bs);
  return concat(data, new Uint8Array(n).fill(n));
}
export function unpad(data: Uint8Array, bs = BLOCK_BYTES): Uint8Array {
  if (data.length === 0 || data.length % bs) throw new Error("invalid padded length");
  const n = data[data.length - 1]!;
  if (n < 1 || n > bs) throw new Error("invalid PKCS#7 padding");
  for (let i = data.length - n; i < data.length; i++) if (data[i] !== n) throw new Error("invalid PKCS#7 padding");
  return data.slice(0, data.length - n);
}

const blocks = function* (d: Uint8Array) { for (let i = 0; i < d.length; i += BLOCK_BYTES) yield d.slice(i, i + BLOCK_BYTES); };

export function cbcEncrypt(pt: Uint8Array, rk: RoundKeys, iv: Uint8Array): Uint8Array {
  let prev = iv; const parts: Uint8Array[] = [];
  for (const b of blocks(pad(pt))) { prev = encryptBlock(xorBytes(b, prev), rk); parts.push(prev); }
  return concat(...parts);
}
export function cbcDecrypt(ct: Uint8Array, rk: RoundKeys, iv: Uint8Array): Uint8Array {
  if (ct.length === 0 || ct.length % BLOCK_BYTES) throw new Error("bad ciphertext length");
  let prev = iv; const parts: Uint8Array[] = [];
  for (const b of blocks(ct)) { parts.push(xorBytes(decryptBlock(b, rk), prev)); prev = b; }
  return unpad(concat(...parts));
}
export function ecbEncrypt(pt: Uint8Array, rk: RoundKeys): Uint8Array {
  const parts: Uint8Array[] = []; for (const b of blocks(pad(pt))) parts.push(encryptBlock(b, rk)); return concat(...parts);
}
export function ecbDecrypt(ct: Uint8Array, rk: RoundKeys): Uint8Array {
  if (ct.length === 0 || ct.length % BLOCK_BYTES) throw new Error("bad ciphertext length");
  const parts: Uint8Array[] = []; for (const b of blocks(ct)) parts.push(decryptBlock(b, rk)); return unpad(concat(...parts));
}
