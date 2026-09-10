// @ts-nocheck  (vitest it.each typings; the canonical gate is test/parity.ts)
// THE PARITY GATE.
// Loads the SAME shared/test_vectors.json that Python froze, and asserts the
// TypeScript port reproduces every value byte-for-byte. If this is green, the
// website runs a cipher provably identical to the Python reference.
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { fromHex, toHex } from "../src/bytes.js";
import { deriveSubkeys, rootKeyFromPassphrase } from "../src/kdf.js";
import { ChaosEngine } from "../src/chaos.js";
import { generateSbox } from "../src/sbox.js";
import { expand } from "../src/keyschedule.js";
import { encryptBlock, decryptBlock } from "../src/cipher.js";
import { cbcEncrypt } from "../src/modes.js";
import { computeTag } from "../src/mac.js";

const here = dirname(fileURLToPath(import.meta.url));
const vectors = JSON.parse(readFileSync(join(here, "../../shared/test_vectors.json"), "utf-8"));
const c = vectors.cases;

describe("PBKDF2 (matches Python hashlib.pbkdf2_hmac)", () => {
  it.each(c.pbkdf2)("%#", (t: any) => {
    expect(toHex(rootKeyFromPassphrase(t.passphrase, fromHex(t.salt), vectors.pbkdf2_iterations))).toBe(t.root_key);
  });
});

describe("HKDF key hierarchy", () => {
  it.each(c.hkdf)("%#", (t: any) => {
    const { encSeed, macKey } = deriveSubkeys(fromHex(t.root_key));
    expect(toHex(encSeed)).toBe(t.enc_seed);
    expect(toHex(macKey)).toBe(t.mac_key);
  });
});

describe("Chaos keystream (integer logistic map + sponge)", () => {
  it.each(c.chaos)("%#", (t: any) => {
    expect(toHex(new ChaosEngine(fromHex(t.enc_seed)).stream(64))).toBe(t.stream64);
  });
});

describe("Key-derived S-box", () => {
  it.each(c.sbox)("%#", (t: any) => {
    expect(toHex(generateSbox(new ChaosEngine(fromHex(t.enc_seed))))).toBe(t.sbox);
  });
});

describe("Round schedule", () => {
  it.each(c.keyschedule)("%#", (t: any) => {
    const ks = expand(fromHex(t.enc_seed));
    expect(ks.keys.map(toHex)).toEqual(t.keys);
    expect(ks.rots).toEqual(t.rots);
  });
});

describe("Single-block Feistel encryption (+ round-trip)", () => {
  it.each(c.block)("%#", (t: any) => {
    const ks = expand(fromHex(t.enc_seed));
    const ct = encryptBlock(fromHex(t.plaintext), ks);
    expect(toHex(ct)).toBe(t.ciphertext);
    expect(toHex(decryptBlock(ct, ks))).toBe(t.plaintext);
  });
});

describe("CBC mode (fixed IV)", () => {
  it.each(c.cbc)("%#", (t: any) => {
    const ks = expand(fromHex(t.enc_seed));
    expect(toHex(cbcEncrypt(fromHex(t.plaintext), ks, fromHex(t.iv)))).toBe(t.ciphertext);
  });
});

describe("HMAC tag", () => {
  it.each(c.mac)("%#", (t: any) => {
    expect(toHex(computeTag(fromHex(t.mac_key), fromHex(t.message)))).toBe(t.tag);
  });
});
