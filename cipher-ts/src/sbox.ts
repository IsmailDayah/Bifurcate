// Key-derived S-box via Fisher-Yates — bifurcate/sbox.py.
import { ChaosEngine } from "./chaos.js";

export function generateSbox(engine: ChaosEngine): Uint8Array {
  const box = new Uint8Array(256);
  for (let i = 0; i < 256; i++) box[i] = i;
  for (let i = 255; i > 0; i--) {
    const j = engine.byte() % (i + 1);
    const t = box[i]!; box[i] = box[j]!; box[j] = t;
  }
  return box;
}

export function differenceRatio(a: Uint8Array, b: Uint8Array): number {
  let d = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) d++;
  return d / a.length;
}
