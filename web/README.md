# Bifurcate — web

The browser build of the cipher: a TypeScript port of the Python reference in
[`../bifurcate/`](../bifurcate), cross-validated against the same known-answer
vectors in [`../shared/test_vectors.json`](../shared/test_vectors.json).

Everything runs client-side — nothing is uploaded.

```bash
pnpm install
pnpm --filter @bifurcate/cipher build   # build the cipher package once
pnpm --filter web dev                   # http://localhost:3000
```

Before deploying, both implementations must agree:

```bash
pytest -q                               # Python reference
pnpm --filter @bifurcate/cipher test    # TypeScript parity
```
