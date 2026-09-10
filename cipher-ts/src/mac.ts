// Encrypt-then-MAC — bifurcate/mac.py.
import { hmac } from "@noble/hashes/hmac";
import { sha256 } from "@noble/hashes/sha256";

export const TAG_BYTES = 32;
export class IntegrityError extends Error {}

export const computeTag = (macKey: Uint8Array, authed: Uint8Array): Uint8Array => hmac(sha256, macKey, authed);

export function verifyTag(macKey: Uint8Array, authed: Uint8Array, tag: Uint8Array): void {
  const expected = computeTag(macKey, authed);
  let diff = expected.length ^ tag.length;
  for (let i = 0; i < expected.length; i++) diff |= expected[i]! ^ (tag[i] ?? 0);
  if (diff !== 0) throw new IntegrityError("INTEGRITY FAIL — HMAC mismatch (wrong key or tampered data)");
}
