# Project notes for Claude

Course materials for the O'Reilly course "Deep Learning for Business Made Simple"
(Keras 3 on the PyTorch backend, run in Google Colab).

## Source of truth: edit the `.qmd`, never the `.ipynb`

- `exercises.qmd` / `exercises_solutions.qmd` are the **sources**.
- `exercises.ipynb` / `exercises_solutions.ipynb` are **generated** by
  `scripts/build-notebooks.py` (`quarto convert` + cleanup). Do not hand-edit them;
  changes get overwritten on the next build.
- The `.qmd` also feeds the HTML site (`exercises_solutions.html`), which Quarto
  renders with **native, live mermaid** (vector, centered via `%%| fig-align: center`,
  captioned via `%%| fig-cap`). Keep the `.qmd` on native ```{mermaid}``` fences — do
  not switch the HTML to static images (decided 2026-06; native fidelity preferred).

## Diagrams: how they render in Colab

Colab's markdown engine has **no mermaid support**, so fenced ```mermaid``` blocks
show as raw text there. The build pipeline therefore converts each `.qmd` `{mermaid}`
block into a **pre-rendered PNG** for the notebooks:

- PNGs live in `assets/diagrams/`, named by content hash
  (`diagram-<sha256[:12]>.png`) so identical diagrams dedupe and rebuilds are stable.
- Notebooks reference them via `raw.githubusercontent.com/.../main/assets/diagrams/...`
  (works in Colab, GitHub, nbviewer — no third-party service).
- Each is wrapped as `<div align="center"><img ... width="N"></div>`, where `N` is
  **60%** of the PNG's natural width (`DIAGRAM_DISPLAY_SCALE = 0.6`). Diagrams render
  at 2x for crisp text, then display at 60% so they aren't oversized.
- A diagram is only re-rendered when its PNG is **missing**, so a routine rebuild needs
  no browser. Rendering a *new/changed* diagram needs mermaid-cli (`mmdc`) + a
  Chrome/Chromium (see the `build-notebooks.py` header and README). Headless flags are
  in `scripts/puppeteer-config.json`.

## Rebuilding

```bash
python scripts/build-notebooks.py     # requires Quarto; needs mmdc only for new diagrams
```

The image links point at the **`main`** branch, matching how Colab opens the notebooks,
so diagrams resolve once changes are on `main`.
