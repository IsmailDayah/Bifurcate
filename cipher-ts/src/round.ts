// The round function F — bifurcate/round.py.
import { bytesToBig, bigToBytes } from "./bytes.js";

export const HALF_BYTES = 8;
const MASK64 = (1n << 64n) - 1n;
// single 8-cycle derangement: 0->5->3->7->4->1->2->6->0
export const PERM = [5, 2, 6, 7, 1, 3, 0, 4] as const;

export function rotateLeftBits(block: Uint8Array, n: number): Uint8Array {
  n %= 64;
  if (n === 0) return block;
  const v = bytesToBig(block);
  const bn = BigInt(n);
  const r = ((v << bn) | (v >> (64n - bn))) & MASK64;
  return bigToBytes(r, HALF_BYTES);
}

export function bytePermute(block: Uint8Array): Uint8Array {
  const out = new Uint8Array(HALF_BYTES);
  for (let i = 0; i < HALF_BYTES; i++) out[PERM[i]!] = block[i]!;
  return out;
}

export function F(half: Uint8Array, roundKey: Uint8Array, rot: number, sbox: Uint8Array): Uint8Array {
  const t = new Uint8Array(HALF_BYTES);
  for (let i = 0; i < HALF_BYTES; i++) t[i] = sbox[half[i]! ^ roundKey[i]!]!; // XOR key + substitute
  return bytePermute(rotateLeftBits(t, rot));                                  // rotate + permute
}
