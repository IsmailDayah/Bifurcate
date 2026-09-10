// Standalone parity gate (no test-runner dependency).
// Compiles with tsc, runs on plain Node. Asserts the TypeScript port reproduces
// every value in the SAME shared/test_vectors.json that Python froze.
import { strict as assert } from "node:assert";
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
const V = JSON.parse(readFileSync(join(here, "../../../shared/test_vectors.json"), "utf-8"));
const c = V.cases;

let pass = 0;
const groups: Record<string, number> = {};
function check(group: string, cond: boolean, detail = "") {
  groups[group] = (groups[group] ?? 0) + 1;
  assert.ok(cond, `${group} mismatch ${detail}`);
  pass++;
}

for (const t of c.pbkdf2)
  check("pbkdf2", toHex(rootKeyFromPassphrase(t.passphrase, fromHex(t.salt), V.pbkdf2_iterations)) === t.root_key);

for (const t of c.hkdf) {
  const { encSeed, macKey } = deriveSubkeys(fromHex(t.root_key));
  check("hkdf", toHex(encSeed) === t.enc_seed && toHex(macKey) === t.mac_key);
}

for (const t of c.chaos)
  check("chaos", toHex(new ChaosEngine(fromHex(t.enc_seed)).stream(64)) === t.stream64);

for (const t of c.sbox)
  check("sbox", toHex(generateSbox(new ChaosEngine(fromHex(t.enc_seed)))) === t.sbox);

for (const t of c.keyschedule) {
  const ks = expand(fromHex(t.enc_seed));
  check("keyschedule",
    JSON.stringify(ks.keys.map(toHex)) === JSON.stringify(t.keys) &&
    JSON.stringify(ks.rots) === JSON.stringify(t.rots));
}

for (const t of c.block) {
  const ks = expand(fromHex(t.enc_seed));
  const ct = encryptBlock(fromHex(t.plaintext), ks);
  check("block", toHex(ct) === t.ciphertext && toHex(decryptBlock(ct, ks)) === t.plaintext);
}

for (const t of c.cbc) {
  const ks = expand(fromHex(t.enc_seed));
  check("cbc", toHex(cbcEncrypt(fromHex(t.plaintext), ks, fromHex(t.iv))) === t.ciphertext);
}

for (const t of c.mac)
  check("mac", toHex(computeTag(fromHex(t.mac_key), fromHex(t.message))) === t.tag);

console.log("Bifurcate parity — TypeScript vs Python");
for (const [g, n] of Object.entries(groups)) console.log(`  OK  ${g.padEnd(12)} ${n} vectors`);
console.log(`\nALL ${pass} KNOWN-ANSWER VECTORS MATCH — the port is byte-identical to the Python reference.`);
