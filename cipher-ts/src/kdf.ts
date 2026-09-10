// Key hierarchy — mirrors bifurcate/kdf.py exactly.
// HKDF is hand-rolled (not noble's) so its salt handling matches the Python
// reference byte-for-byte: empty salt -> 32 zero bytes (RFC 5869).
import { hmac } from "@noble/hashes/hmac";
import { sha256 } from "@noble/hashes/sha256";
import { pbkdf2 } from "@noble/hashes/pbkdf2";
import { concat, utf8 } from "./bytes.js";

const HASH_LEN = 32;

export function hkdfExtract(salt: Uint8Array, ikm: Uint8Array): Uint8Array {
  if (salt.length === 0) salt = new Uint8Array(HASH_LEN);
  return hmac(sha256, salt, ikm);
}

export function hkdfExpand(prk: Uint8Array, info: Uint8Array, length = HASH_LEN): Uint8Array {
  let out = new Uint8Array(0);
  let block = new Uint8Array(0);
  let counter = 1;
  while (out.length < length) {
    block = hmac(sha256, prk, concat(block, info, Uint8Array.of(counter)));
    out = concat(out, block);
    counter++;
  }
  return out.slice(0, length);
}

export const hkdf = (ikm: Uint8Array, info: Uint8Array, length = HASH_LEN, salt = new Uint8Array(0)) =>
  hkdfExpand(hkdfExtract(salt, ikm), info, length);

export const INFO_CHAOS = utf8("BIFURCATE-CHAOS-v1");
export const INFO_MAC = utf8("BIFURCATE-MAC-v1");

export function deriveSubkeys(rootKey: Uint8Array): { encSeed: Uint8Array; macKey: Uint8Array } {
  if (rootKey.length !== 32) throw new Error("root_key must be 32 bytes");
  return { encSeed: hkdf(rootKey, INFO_CHAOS), macKey: hkdf(rootKey, INFO_MAC) };
}

// PBKDF2-HMAC-SHA256 — identical to Python hashlib.pbkdf2_hmac.
export const rootKeyFromPassphrase = (passphrase: string, salt: Uint8Array, iterations = 200_000) =>
  pbkdf2(sha256, utf8(passphrase), salt, { c: iterations, dkLen: 32 });
