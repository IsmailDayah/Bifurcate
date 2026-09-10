// Byte/BigInt helpers — big-endian, matching Python int.to_bytes/from_bytes.
export const toHex = (b: Uint8Array): string =>
  Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");

export const fromHex = (h: string): Uint8Array => {
  const out = new Uint8Array(h.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(h.slice(i * 2, i * 2 + 2), 16);
  return out;
};

export const concat = (...arrs: Uint8Array[]): Uint8Array => {
  const n = arrs.reduce((s, a) => s + a.length, 0);
  const out = new Uint8Array(n);
  let o = 0;
  for (const a of arrs) { out.set(a, o); o += a.length; }
  return out;
};

export const xorBytes = (a: Uint8Array, b: Uint8Array): Uint8Array => {
  const out = new Uint8Array(a.length);
  for (let i = 0; i < a.length; i++) out[i] = a[i]! ^ b[i]!;
  return out;
};

// big-endian BigInt <-> fixed-width bytes (matches Python int.to_bytes(_, 'big'))
export const bytesToBig = (b: Uint8Array): bigint => {
  let v = 0n;
  for (const x of b) v = (v << 8n) | BigInt(x);
  return v;
};

export const bigToBytes = (v: bigint, len: number): Uint8Array => {
  const out = new Uint8Array(len);
  for (let i = len - 1; i >= 0; i--) { out[i] = Number(v & 0xffn); v >>= 8n; }
  return out;
};

export const utf8 = (s: string): Uint8Array => new TextEncoder().encode(s);
