# E_visualization/

## `index.html` — start here

Self-contained, zero dependencies. **Just double-click it** (or open
it in any browser directly, `file://` works fine — no server, no
`npm install`, no build step). Real Estonia 2019 hourly data (Elering
archive) is embedded directly in the file.

Self-contained, zero dependencies. **Download `index.html` and open it
directly in any browser** — no server, no `npm install`, and no build 
step required.
The dashboard includes real Estonia 2019 hourly electricity data from 
the Elering archive, embedded directly in the file.

Also works via GitHub Pages if you want to host it: enable Pages on
this repo, point it at this folder, and this file becomes the site's
homepage automatically.

## `grid_dashboard.jsx` — same tool, React version

Functionally identical (same `simulate()` logic, same real data) but
requires a React build pipeline (Vite/Next.js/Create React App +
`recharts`) to actually run — kept for anyone who wants to embed this
inside a larger React app rather than open it standalone. If you just
want to see the dashboard, use `index.html` instead.

## Both were validated the same way

Not just visually — both versions' `simulate()` function was checked
against the real known 2024/2019 figures (e.g. total demand comes out
to 8,230 GWh/yr, matching Elering's own reported number) before being
delivered. `index.html` was additionally rendered in a real headless
DOM (jsdom) with a slider interaction simulated, not just syntax-checked.
