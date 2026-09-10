# Deploying Bifurcate (GitHub + Vercel)

The site is a **static** Next.js app (all routes prerender to static HTML/JS) that runs
the cipher in the browser. No server, no environment variables, no secrets.

## 1. Push to GitHub (use SSH — never a token in the URL)

```bash
cd Bifurcate
git init && git add -A && git commit -m "Bifurcate: cipher + cross-validated web app"
# create an EMPTY repo on github.com first, then:
git remote add origin git@github.com:<you>/bifurcate.git
git branch -M main
git push -u origin main
```

> Security: do NOT use an `https://<token>@github.com/...` remote — that writes the token into
> `.git/config` in plaintext. Use SSH (above) or `gh auth login`.

## 2. Deploy on Vercel

**Recommended — dashboard (zero tokens):**
1. vercel.com → Add New → Project → import your `bifurcate` repo.
2. Set **Root Directory = `web`** in the project settings (this is a pnpm
   monorepo; the cipher package is built first by the root `build` script).
3. Click Deploy.
4. Every `git push` afterwards auto-deploys; pull requests get preview URLs.

**Or CLI:**
```bash
npm i -g vercel
vercel            # links the project (first run)
vercel --prod     # ship
```

## 3. Local development

```bash
pnpm install
pnpm --filter @bifurcate/cipher build   # build the cipher once
pnpm --filter web dev                   # http://localhost:3000
```

## 4. The correctness gate (run before every deploy)

```bash
# Python reference
cd Bifurcate && pytest -q
# TypeScript parity — must match the same 36 known-answer vectors
pnpm --filter @bifurcate/cipher test
```

If either is red, do not deploy — the two implementations have diverged.
