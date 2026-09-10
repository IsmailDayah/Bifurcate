// The chaotic engine — bifurcate/chaos.py, ported with BigInt.
//
// CRITICAL: the map computes R_FIXED * X * (S - X) which reaches ~2^64,
// far beyond Number.MAX_SAFE_INTEGER (2^53). BigInt is mandatory or the
// keystream silently diverges from Python. This is THE reason a naive port fails.
import { sha256 } from "@noble/hashes/sha256";
import { bigToBytes, concat } from "./bytes.js";

export const SCALE = 1n << 32n;
const R_SHIFT = 20n;
export const R_FIXED = BigInt(Math.round(3.99 * 2 ** 20)); // r = 3.99, fixed-point
const ITERS_PER_SQUEEZE = 8;

export const step = (x: bigint): bigint => (R_FIXED * x * (SCALE - x)) / (SCALE << R_SHIFT);

export class ChaosEngine {
  private x: bigint;
  private ctr = 0;
  private buf: number[] = [];
  private reinject = 0;
  constructor(private encSeed: Uint8Array) {
    if (encSeed.length !== 32) throw new Error("enc_seed must be 32 bytes");
    let seed = 0n;
    for (let i = 0; i < 4; i++) seed = (seed << 8n) | BigInt(encSeed[i]!);
    this.x = (seed % (SCALE - 2n)) + 1n;
  }
  private guard(prev: bigint): void {
    if (this.x === 0n || this.x === prev) {
      this.reinject++;
      const d = sha256(concat(new TextEncoder().encode("BIFURCATE-REINJECT"),
        bigToBytes(BigInt(this.reinject), 8), this.encSeed));
      let v = 0n;
      for (let i = 0; i < 4; i++) v = (v << 8n) | BigInt(d[i]!);
      this.x = ((this.x ^ v) % (SCALE - 2n)) + 1n;
    }
  }
  private iterate(n: number): void {
    for (let i = 0; i < n; i++) { const prev = this.x; this.x = step(this.x); this.guard(prev); }
  }
  private squeeze(): Uint8Array {
    this.iterate(ITERS_PER_SQUEEZE);
    const block = sha256(concat(bigToBytes(this.x, 4), bigToBytes(BigInt(this.ctr), 8), this.encSeed));
    this.ctr++;
    return block;
  }
  stream(n: number): Uint8Array {
    while (this.buf.length < n) this.buf.push(...this.squeeze());
    return Uint8Array.from(this.buf.splice(0, n));
  }
  byte(): number { return this.stream(1)[0]!; }
}
