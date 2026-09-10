// Image helpers for the encrypt/decrypt visuals.
export async function fileToBytes(file: File): Promise<Uint8Array> {
  return new Uint8Array(await file.arrayBuffer());
}

export async function loadImage(bytes: Uint8Array, mime: string): Promise<HTMLImageElement> {
  const view = new Uint8Array(bytes);
  const url = URL.createObjectURL(new Blob([view.buffer as ArrayBuffer], { type: mime }));
  const img = new Image();
  await new Promise<void>((res, rej) => {
    img.onload = () => res();
    img.onerror = () => rej(new Error("image load failed"));
    img.src = url;
  });
  return img;
}

// Render arbitrary bytes as an RGB "noise" image of given dimensions.
export function bytesToNoiseCanvas(bytes: Uint8Array, w: number, h: number): string {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const imgData = ctx.createImageData(w, h);
  for (let i = 0; i < w * h; i++) {
    imgData.data[i * 4] = bytes[(i * 3) % bytes.length] ?? 0;
    imgData.data[i * 4 + 1] = bytes[(i * 3 + 1) % bytes.length] ?? 0;
    imgData.data[i * 4 + 2] = bytes[(i * 3 + 2) % bytes.length] ?? 0;
    imgData.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(imgData, 0, 0);
  return canvas.toDataURL("image/png");
}

export function sniffImageMime(bytes: Uint8Array): string | null {
  if (bytes[0] === 0x89 && bytes[1] === 0x50) return "image/png";
  if (bytes[0] === 0xff && bytes[1] === 0xd8) return "image/jpeg";
  if (bytes[0] === 0x47 && bytes[1] === 0x49) return "image/gif";
  if (bytes[0] === 0x42 && bytes[1] === 0x4d) return "image/bmp";
  // WebP: "RIFF"????"WEBP"
  if (
    bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46 &&
    bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50
  )
    return "image/webp";
  return null;
}

// Best-guess file extension from magic bytes — used only to name the recovered
// download (the .bfc container does not store the original filename).
export function sniffExtension(bytes: Uint8Array): string {
  const mime = sniffImageMime(bytes);
  if (mime) return mime.split("/")[1]!.replace("jpeg", "jpg");
  if (bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46) return "pdf"; // %PDF
  if (bytes[0] === 0x50 && bytes[1] === 0x4b && bytes[2] === 0x03 && bytes[3] === 0x04) return "zip"; // PK..
  return "bin";
}
