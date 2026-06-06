# Materials for the course "Deep Learning for Business Made Simple" for O'Reilly by Dr. Chester Ismay

This course teaches deep learning with **Keras 3 running on the PyTorch backend** --
friendly, high-level code on top of a production-grade engine. The solutions also show
each model written in **idiomatic PyTorch** for learners who want the lower-level view.

## Run it in Google Colab (recommended — nothing to install)

The fastest way to follow along is Google Colab. Open the student notebook directly:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ismayc/oreilly-deep-learning-made-simple/blob/main/exercises.ipynb)

https://colab.research.google.com/github/ismayc/oreilly-deep-learning-made-simple/blob/main/exercises.ipynb

**There is nothing to upload.** Every dataset is fetched over the network when its
cell runs, so the notebook is fully self-contained:

| Module | Data | How it loads |
|---|---|---|
| 1 — Neural networks (tabular) | Hotel bookings | `pd.read_csv("https://raw.githubusercontent.com/...hotels.csv")` |
| 2 — Images | Food-101 | `load_dataset("ethz/food101", streaming=True)` (Hugging Face) |
| 3 — Text | Yelp reviews | `load_dataset("fancyzhx/yelp_polarity", streaming=True)` (Hugging Face) |

In Colab:

1. Run the first cell (`pip install`). If Colab asks to **restart the runtime**, do it,
   then run from the top — the `KERAS_BACKEND=torch` line must run before `import keras`.
2. For Module 2 (image transfer learning), switch to a GPU via
   **Runtime → Change runtime type → GPU**. CPU works too, just slower.

## Course content

- `exercises.ipynb` — the **student** notebook: walkthroughs are worked examples to run
  and discuss; the exercises leave the instructive choices open for live coding.
- `exercises_solutions.ipynb` — full solutions, with Keras **and** idiomatic PyTorch for
  every example. A rendered HTML version is the recommended way to read the solutions:
  **https://ismay-oreilly-dlms.netlify.app/exercises_solutions.html**
- `exercises.qmd` / `exercises_solutions.qmd` — the Quarto sources the notebooks are
  built from.
- `slides.pdf` — the slide deck used to motivate the code.
- `index.html` — landing page (served at the site root): https://ismay-oreilly-dlms.netlify.app
- `requirements.txt` — packages for running locally (Colab already has most of these).

> The annotated instructor edition (`exercises_solutions_with_notes.qmd`) is a local
> working file and is intentionally not committed (see `.gitignore`).

### Rebuilding the notebooks from source

The `.ipynb` files are generated from the `.qmd` sources. To regenerate them (requires
[Quarto](https://quarto.org)):

```bash
python scripts/build-notebooks.py
```

## Running locally instead of Colab

If you aren't able to use Colab, you can run the notebooks on your own machine. We
recommend Python 3.10–3.12.

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook                  # then open exercises.ipynb
```

Note: the deep learning stack (Keras/PyTorch) cannot run in browser-only environments
such as JupyterLite/Pyodide, which is why this course uses Colab or a local install
rather than an in-browser app.

## A note on the datasets

All three datasets were chosen to be fresh, business-relevant, and hosted (no local
files): hotel-booking cancellations (revenue management), Food-101 (product/menu image
tagging), and Yelp reviews (customer sentiment). They stream on demand, so the only
file a learner needs is the notebook itself.
