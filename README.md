# The Hedge

Weekly essay-zine. Web archive lives at **hedge.fogletter.com**; quarterly riso prints are the artifact that travels.

## Stack

- Astro 5 + MDX + Tailwind 4
- Cloudflare Pages deploy target
- pnpm

## Local

```bash
pnpm install
pnpm dev
```

Dev server runs at `http://localhost:4321`.

## Content

Issues live in `src/content/issues/`. Schema in `src/content.config.ts`.

Required frontmatter:

```yaml
---
number: 37
title: The Hedge
cluster: Hedge Season
month: October
status: scaffold  # scaffold | draft | published
# optional:
subtitle: ...
published: 2026-10-01
illustration: /illustrations/37.png
---
```

Only `status: published` issues appear on the home page, in the archive, in the RSS feed, and at indexed URLs. `scaffold` and `draft` issues are listed at `/issues/` for tracking but do not render their own page.

## Editorial source

The 48-piece scaffold and per-issue outlines live in the reliquary repo at
`creative/zine/the-hedge/`. This site is the publishing surface; the reliquary
is the workshop.

## Deferred (don't add yet)

- Buttondown email signup — wait until first reader correspondence
- Stripe / print store — wait until first riso compilation
- Comments, letters, search, dark mode
- Analytics of any kind — never
