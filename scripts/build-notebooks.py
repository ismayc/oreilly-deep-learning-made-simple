#!/usr/bin/env python3
"""Build Colab-ready .ipynb notebooks from the source .qmd files.

For each committed qmd we:
  1. `quarto convert` it to a notebook,
  2. drop the YAML front-matter cell and prepend a title (+ "Open in Colab" badge),
  3. make the pip cell robust for a fresh Colab runtime,
  4. strip Quarto `#|` directive lines (noise in a plain notebook),
  5. clear outputs / execution counts and set a clean kernelspec.

Usage:  python scripts/build-notebooks.py
Requires: quarto on PATH.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = "ismayc/oreilly-deep-learning-made-simple"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent.parent

# (source qmd, output ipynb, add a Colab badge?)
TARGETS = [
    ("exercises.qmd", "exercises.ipynb", True),
    ("exercises_solutions.qmd", "exercises_solutions.ipynb", False),
]


def colab_url(nb_name):
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{nb_name}"


def title_cell(nb_name, badge):
    lines = [
        "# Walkthroughs and Exercises for Deep Learning for Business Made Simple\n",
        "\n",
        "**Dr. Chester Ismay**\n",
        "\n",
    ]
    if badge:
        lines += [
            f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(nb_name)})\n",
            "\n",
        ]
    lines += [
        "We teach in **Keras 3** running on the **PyTorch** backend. Run the setup cell\n",
        "first, then work top to bottom. All data is fetched from the web (a GitHub URL\n",
        "for the hotel data; Hugging Face streaming for the image and text data), so there\n",
        "is **nothing to upload** -- each dataset loads itself when you run its cell.\n",
    ]
    return {"cell_type": "markdown", "metadata": {}, "source": lines}


PIP_CELL = [
    "# Run this once per session, then RESTART the runtime if Colab prompts you to.\n",
    "# Colab already ships torch; we add/upgrade Keras 3 and the datasets library.\n",
    "!pip install -q -U keras datasets\n",
    "!pip install -q scikit-learn matplotlib pillow\n",
]


def is_yaml_cell(cell):
    src = "".join(cell["source"]).strip()
    return cell["cell_type"] == "markdown" and src.startswith("---") and "title:" in src


def clean(nb_name, badge):
    nb = json.loads(Path(nb_name).read_text())
    cells = nb["cells"]

    # 1) drop the YAML front-matter cell if present
    cells = [c for c in cells if not is_yaml_cell(c)]

    # 2) strip Quarto directive lines from code cells; clear outputs
    for c in cells:
        if c["cell_type"] == "code":
            c["source"] = [ln for ln in c["source"] if not ln.lstrip().startswith("#|")]
            while c["source"] and c["source"][0].strip() == "":
                c["source"].pop(0)
            c["outputs"] = []
            c["execution_count"] = None

    # 3) robustify the pip cell (first code cell that pip-installs)
    for c in cells:
        if c["cell_type"] == "code" and any("pip install" in ln for ln in c["source"]):
            c["source"] = list(PIP_CELL)
            break

    # 4) drop a leading badge-only markdown cell if the qmd already carried one
    #    (we re-add a canonical title cell next)
    cells = [c for c in cells
             if not (c["cell_type"] == "markdown"
                     and "colab-badge.svg" in "".join(c["source"])
                     and "# " not in "".join(c["source"]))]

    # 5) prepend the canonical title cell
    cells.insert(0, title_cell(nb_name, badge))

    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
    nb["metadata"]["language_info"] = {"name": "python"}
    Path(nb_name).write_text(json.dumps(nb, indent=1))


def main():
    import os
    os.chdir(ROOT)
    for qmd, nb_name, badge in TARGETS:
        if not Path(qmd).exists():
            print(f"skip (missing): {qmd}")
            continue
        subprocess.run(["quarto", "convert", qmd, "--output", nb_name], check=True)
        clean(nb_name, badge)
        n = len(json.loads(Path(nb_name).read_text())["cells"])
        print(f"built {nb_name}  ({n} cells)  ->  {colab_url(nb_name)}")


if __name__ == "__main__":
    sys.exit(main())
