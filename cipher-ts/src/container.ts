// The .bfc container — bifurcate/container.py. Byte-compatible layout.
import { deriveSubkeys, rootKeyFromPassphrase } from "./kdf.js";
import { expand } from "./keyschedule.js";
import { cbcEncrypt, cbcDecrypt, ecbEncrypt, ecbDecrypt, MODE_CBC, MODE_ECB } from "./modes.js";
import { computeTag, verifyTag, TAG_BYTES, IntegrityError } from "./mac.js";
import { concat } from "./bytes.js";

const MAGIC = new Uint8Array([0x42, 0x46, 0x43, 0x31]); // "BFC1"
const VERSION = 1;
const HEADER_LEN = 40;
export const FLAG_ECB = 0b01;
export const FLAG_HYBRID = 0b10;
export const PBKDF2_ITERATIONS = 200_000;

export class FormatError extends Error {}
export { IntegrityError };

export interface Parsed {
  version: number; flags: number; salt: Uint8Array; iv: Uint8Array;
  wrappedKey: Uint8Array; ciphertext: Uint8Array; tag: Uint8Array;
  mode: number; modeName: string; isHybrid: boolean;
}

const rand = (n: number): Uint8Array => crypto.getRandomValues(new Uint8Array(n));

function pack(flags: number, salt: Uint8Array, iv: Uint8Array, wrapped: Uint8Array, ct: Uint8Array): Uint8Array {
  const wl = new Uint8Array([(wrapped.length >> 8) & 0xff, wrapped.length & 0xff]);
  return concat(MAGIC, new Uint8Array([VERSION, flags]), salt, iv, wl, wrapped, ct);
}

export interface EncryptOpts { passphrase?: string; publicKey?: CryptoKey; mode?: number; }

export async function encrypt(plaintext: Uint8Array, opts: EncryptOpts): Promise<Uint8Array> {
  const mode = opts.mode ?? MODE_CBC;
  if (!!opts.passphrase === !!opts.publicKey) throw new Error("provide exactly one of passphrase or publicKey");
  const salt = rand(16), iv = rand(16);
  let flags = mode === MODE_ECB ? FLAG_ECB : 0;
  let rootKey: Uint8Array, wrapped = new Uint8Array(0);
  if (opts.publicKey) {
    rootKey = rand(32);
    wrapped = new Uint8Array(await crypto.subtle.encrypt({ name: "RSA-OAEP" }, opts.publicKey, rootKey));
    flags |= FLAG_HYBRID;
  } else {
    rootKey = rootKeyFromPassphrase(opts.passphrase!, salt, PBKDF2_ITERATIONS);
  }
  const { encSeed, macKey } = deriveSubkeys(rootKey);
  const rk = expand(encSeed);
  const ct = mode === MODE_ECB ? ecbEncrypt(plaintext, rk) : cbcEncrypt(plaintext, rk, iv);
  const body = pack(flags, salt, iv, wrapped, ct);
  return concat(body, computeTag(macKey, body));
}

export function parse(blob: Uint8Array): Parsed {
  if (blob.length < HEADER_LEN + TAG_BYTES) throw new FormatError("file too short");
  for (let i = 0; i < 4; i++) if (blob[i] !== MAGIC[i]) throw new FormatError("bad magic — not a .bfc container");
  const version = blob[4]!;
  if (version !== VERSION) throw new FormatError(`unsupported version ${version}`);
  const flags = blob[5]!;
  const salt = blob.slice(6, 22), iv = blob.slice(22, 38);
  const wl = (blob[38]! << 8) | blob[39]!;
  const wrappedKey = blob.slice(HEADER_LEN, HEADER_LEN + wl);
  if (wrappedKey.length !== wl) throw new FormatError("truncated wrapped key");
  const ciphertext = blob.slice(HEADER_LEN + wl, blob.length - TAG_BYTES);
  const tag = blob.slice(blob.length - TAG_BYTES);
  const isHybrid = !!(flags & FLAG_HYBRID);
  const mode = flags & FLAG_ECB ? MODE_ECB : MODE_CBC;
  return { version, flags, salt, iv, wrappedKey, ciphertext, tag, mode,
           modeName: mode === MODE_ECB ? "ECB" : "CBC", isHybrid };
}

export interface DecryptOpts { passphrase?: string; privateKey?: CryptoKey; }

export async function decrypt(blob: Uint8Array, opts: DecryptOpts): Promise<Uint8Array> {
  const c = parse(blob);
  let rootKey: Uint8Array;
  if (c.isHybrid) {
    if (!opts.privateKey) throw new Error("this container is hybrid — an RSA private key is required");
    try {
      rootKey = new Uint8Array(await crypto.subtle.decrypt({ name: "RSA-OAEP" }, opts.privateKey, c.wrappedKey));
    } catch (e) { throw new IntegrityError("RSA unwrap failed — wrong private key"); }
  } else {
    if (opts.passphrase == null) throw new Error("this container needs a passphrase");
    rootKey = rootKeyFromPassphrase(opts.passphrase, c.salt, PBKDF2_ITERATIONS);
  }
  const { encSeed, macKey } = deriveSubkeys(rootKey);
  verifyTag(macKey, blob.slice(0, blob.length - TAG_BYTES), c.tag); // authenticate BEFORE decrypting
  const rk = expand(encSeed);
  return c.mode === MODE_ECB ? ecbDecrypt(c.ciphertext, rk) : cbcDecrypt(c.ciphertext, rk, c.iv);
}
