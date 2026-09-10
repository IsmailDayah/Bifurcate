// Round-key schedule — bifurcate/keyschedule.py.
import { ChaosEngine } from "./chaos.js";
import { generateSbox } from "./sbox.js";

export const ROUNDS = 12;
export interface RoundKeys { sbox: Uint8Array; keys: Uint8Array[]; rots: number[]; }

export function expand(encSeed: Uint8Array): RoundKeys {
  const engine = new ChaosEngine(encSeed);
  const sbox = generateSbox(engine);
  const keys: Uint8Array[] = [];
  const rots: number[] = [];
  for (let i = 0; i < ROUNDS; i++) {
    keys.push(engine.stream(8));
    rots.push(1 + (engine.byte() % 7)); // 1..7, never 0
  }
  return { sbox, keys, rots };
}
