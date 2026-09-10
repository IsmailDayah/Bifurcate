import { ImageResponse } from "next/og";

export const alt = "Bifurcate — a chaos-seeded cipher you can watch";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#0b1220",
          padding: 72,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 68,
              height: 68,
              borderRadius: 16,
              background: "#f59e0b",
              color: "#0b1220",
              fontSize: 40,
              fontWeight: 700,
            }}
          >
            B
          </div>
          <div style={{ color: "#f8fafc", fontSize: 44, fontWeight: 700 }}>Bifurcate</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ color: "#f8fafc", fontSize: 68, fontWeight: 700, lineHeight: 1.1 }}>
            A chaos-seeded cipher
          </div>
          <div style={{ color: "#f59e0b", fontSize: 68, fontWeight: 700, lineHeight: 1.1 }}>
            you can watch.
          </div>
          <div style={{ color: "#94a3b8", fontSize: 28, marginTop: 26, lineHeight: 1.4 }}>
            12-round Feistel · key-derived S-box · encrypt-then-MAC
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: 24 }}>
          <div style={{ display: "flex" }}>Runs entirely in your browser</div>
          <div style={{ display: "flex" }}>bifurcate.vercel.app</div>
        </div>
      </div>
    ),
    size,
  );
}
