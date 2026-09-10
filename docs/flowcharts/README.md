# Flowcharts

Regenerate all six with:

    python docs/flowcharts/build_flowcharts.py

| File | Figure |
|---|---|
| `fig1_master`  | The complete system (key hierarchy → chaos → cipher → container) |
| `fig2_chaos`   | The chaotic engine (integer map + sponge + guard) |
| `fig3_sbox`    | Key-derived S-box generation |
| `fig4_encrypt` | Feistel network — encryption |
| `fig5_decrypt` | Feistel network — decryption (same structure, keys reversed) |
| `fig6_roundf`  | The round function F (confusion + diffusion) |

Each is emitted as `.svg` (vector) and `.png` (2× raster).
Palette matches the app; every box carries a stated *purpose*.
