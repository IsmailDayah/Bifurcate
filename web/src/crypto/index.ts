// The web's single crypto surface. Re-exports the tested cipher-ts port
// (proven byte-identical to Python) plus small browser helpers.
export * from "@bifurcate/cipher";

export function downloadBytes(data: Uint8Array, filename: string, mime = "application/octet-stream") {
  const view = new Uint8Array(data); // ensure a plain ArrayBuffer-backed copy
  const blob = new Blob([view.buffer as ArrayBuffer], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function shannonEntropy(data: Uint8Array): number {
  if (data.length === 0) return 0;
  const counts = new Array(256).fill(0);
  for (const b of data) counts[b]++;
  let h = 0;
  for (const c of counts) if (c) { const p = c / data.length; h -= p * Math.log2(p); }
  return h;
}

export function histogram(data: Uint8Array): number[] {
  const counts = new Array(256).fill(0);
  for (const b of data) counts[b]++;
  return counts;
}
