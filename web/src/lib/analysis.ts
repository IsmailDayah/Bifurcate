// Live security metrics for /analysis — uses the tested cipher-ts primitives.
import { encryptBlock, F, type RoundKeys } from "@bifurcate/cipher";

const BLOCK = 16;
const bitDiff = (a: Uint8Array, b: Uint8Array) => {
  let d = 0;
  for (let i = 0; i < a.length; i++) { let x = a[i]! ^ b[i]!; while (x) { d += x & 1; x >>= 1; } }
  return d;
};
const rand = (n: number) => crypto.getRandomValues(new Uint8Array(n));
const flip = (data: Uint8Array, bit: number) => { const o = data.slice(); o[bit >> 3]! ^= 1 << (bit & 7); return o; };

export function plaintextAvalanche(rk: RoundKeys, trials = 300): number {
  let total = 0;
  for (let i = 0; i < trials; i++) {
    const b = rand(BLOCK), idx = Math.floor(Math.random() * 128);
    total += bitDiff(encryptBlock(b, rk), encryptBlock(flip(b, idx), rk));
  }
  return (total / (trials * 128)) * 100;
}

export function keyAvalanche(rkA: RoundKeys, rkB: RoundKeys, trials = 300): number {
  let total = 0;
  for (let i = 0; i < trials; i++) { const b = rand(BLOCK); total += bitDiff(encryptBlock(b, rkA), encryptBlock(b, rkB)); }
  return (total / (trials * 128)) * 100;
}

function feistelN(block: Uint8Array, rk: RoundKeys, n: number): Uint8Array {
  let left = block.slice(0, 8), right = block.slice(8);
  for (let i = 0; i < n; i++) {
    const f = F(right, rk.keys[i]!, rk.rots[i]!, rk.sbox);
    const nr = new Uint8Array(8);
    for (let j = 0; j < 8; j++) nr[j] = left[j]! ^ f[j]!;
    left = right; right = nr;
  }
  const out = new Uint8Array(16); out.set(right); out.set(left, 8); return out;
}

export function roundsCurve(rk: RoundKeys, trials = 120): number[] {
  const out: number[] = [];
  for (let n = 1; n <= 12; n++) {
    let total = 0;
    for (let i = 0; i < trials; i++) {
      const b = rand(BLOCK), idx = Math.floor(Math.random() * 128);
      total += bitDiff(feistelN(b, rk, n), feistelN(flip(b, idx), rk, n));
    }
    out.push((total / (trials * 128)) * 100);
  }
  return out;
}

export function avalancheGrid(rk: RoundKeys, block: Uint8Array, bit: number): number[] {
  const a = encryptBlock(block, rk), b = encryptBlock(flip(block, bit), rk);
  const grid: number[] = [];
  for (let i = 0; i < 128; i++) grid.push((a[i >> 3]! ^ b[i >> 3]!) >> (i & 7) & 1);
  return grid;
}
