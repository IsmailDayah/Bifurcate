// The Feistel network — bifurcate/cipher.py.
// Encryption and decryption are the SAME routine; only the key order flips.
import { RoundKeys, ROUNDS, expand } from "./keyschedule.js";
import { F, HALF_BYTES } from "./round.js";
import { concat, xorBytes } from "./bytes.js";

export const BLOCK_BYTES = 16;

function feistel(block: Uint8Array, rk: RoundKeys, reverse: boolean): Uint8Array {
  if (block.length !== BLOCK_BYTES) throw new Error("block must be 16 bytes");
  let left = block.slice(0, HALF_BYTES);
  let right = block.slice(HALF_BYTES);
  const order = reverse ? [...Array(ROUNDS).keys()].reverse() : [...Array(ROUNDS).keys()];
  for (const i of order) {
    const f = F(right, rk.keys[i]!, rk.rots[i]!, rk.sbox);
    const nr = xorBytes(left, f);
    left = right; right = nr;
  }
  return concat(right, left); // final swap: R || L
}

export const encryptBlock = (block: Uint8Array, rk: RoundKeys) => feistel(block, rk, false);
export const decryptBlock = (block: Uint8Array, rk: RoundKeys) => feistel(block, rk, true);

export class Bifurcate {
  rk: RoundKeys;
  constructor(encSeed: Uint8Array) { this.rk = expand(encSeed); }
  encryptBlock = (b: Uint8Array) => encryptBlock(b, this.rk);
  decryptBlock = (b: Uint8Array) => decryptBlock(b, this.rk);
}
