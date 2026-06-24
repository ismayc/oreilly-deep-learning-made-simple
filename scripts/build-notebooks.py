#!/usr/bin/env python3
"""Build Colab-ready .ipynb notebooks from the source .qmd files.

For each committed qmd we:
  1. `quarto convert` it to a notebook,
  2. drop the YAML front-matter cell and prepend a title (no "Open in Colab" badge --
     the notebooks open IN Colab, where that badge is redundant),
  2b. clean markdown cells: drop the HTML-only <style> block and rewrite Quarto
      ```{mermaid} fences to pre-rendered PNGs referenced from
      raw.githubusercontent.com, so the diagrams render in Google Colab (whose
      markdown engine has no mermaid support) as well as on GitHub/nbviewer,
  3. make the pip cell robust for a fresh Colab runtime,
  4. strip Quarto `#|` directive lines (noise in a plain notebook),
  5. clear outputs / execution counts and set a clean kernelspec.

Usage:  python scripts/build-notebooks.py
Requires: quarto on PATH. Diagrams are rendered with mermaid-cli (`mmdc`); a
diagram is only (re)rendered when its PNG is missing, so a plain rebuild that
doesn't change any diagram needs neither mmdc nor a browser. To render new or
changed diagrams, install mermaid-cli and point it at a Chrome/Chromium:
    npm install -g @mermaid-js/mermaid-cli       # provides `mmdc`
    npx puppeteer browsers install chrome        # or use a system Chrome
    export PUPPETEER_EXECUTABLE_PATH=/path/to/chrome   # if not auto-detected
Override the mmdc binary with the MMDC env var if it isn't on PATH.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = "ismayc/oreilly-deep-learning-made-simple"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = ROOT / "assets" / "diagrams"
PUPPETEER_CFG = ROOT / "scripts" / "puppeteer-config.json"

# (source qmd, output ipynb, add a Colab badge?) -- badge off: the notebooks are
# opened IN Colab, so an "Open in Colab" badge inside them is redundant.
TARGETS = [
    ("exercises.qmd", "exercises.ipynb", False),
    ("exercises_solutions.qmd", "exercises_solutions.ipynb", False),
]


def colab_url(nb_name):
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{nb_name}"


def diagram_name(code):
    """Content-addressed PNG name: identical diagrams share one file, and a
    rebuild produces the same name (no churn) unless the source changes."""
    return "diagram-" + hashlib.sha256(code.encode("utf-8")).hexdigest()[:12] + ".png"


def diagram_raw_url(name):
    return (f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
            f"/assets/diagrams/{name}")


def render_diagram(code, out_path):
    """Render mermaid source to a PNG with mermaid-cli. Only called when the
    target PNG is missing, so an unchanged rebuild needs no browser."""
    mmdc = os.environ.get("MMDC", "mmdc")
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    src = out_path.with_suffix(".mmd")
    src.write_text(code + "\n")
    cmd = [mmdc, "-i", str(src), "-o", str(out_path), "-b", "white", "-s", "2"]
    if PUPPETEER_CFG.exists():
        cmd += ["-p", str(PUPPETEER_CFG)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit(f"error: '{mmdc}' not found. Install mermaid-cli to render new "
                 f"diagrams (see this script's header), or set MMDC.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"error rendering {out_path.name}:\n{e.stderr or e.stdout}")
    finally:
        src.unlink(missing_ok=True)


def mermaid_to_image(code):
    """Render `code` if needed and return the markdown image referencing its
    committed PNG via raw.githubusercontent.com."""
    name = diagram_name(code)
    out_path = DIAGRAMS_DIR / name
    if not out_path.exists():
        render_diagram(code, out_path)
    return f"![Mermaid diagram]({diagram_raw_url(name)})"


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
        "We teach in **Keras 3** running on the **PyTorch** backend (the same code also runs\n",
        "on **TensorFlow** -- see the touchpoints throughout). Run the setup cell first, then\n",
        "work top to bottom. All data is fetched from the web (a GitHub URL for the hotel\n",
        "data; Hugging Face streaming for the image and text data), so there is **nothing to\n",
        "upload** -- each dataset loads itself when you run its cell.\n",
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

    # 1b) markdown cells: strip the HTML-only <style> block, and rewrite Quarto
    #     ```{mermaid} fences (dropping `%%|` cell-options) to a pre-rendered PNG
    #     referenced from raw.githubusercontent.com. Colab's markdown engine has
    #     no mermaid support, so a fenced block never renders there; an <img>
    #     does. GitHub/nbviewer show the same committed PNG.
    def _fix_mermaid(m):
        body = "\n".join(ln for ln in m.group(1).split("\n")
                         if not ln.lstrip().startswith("%%|")).strip("\n")
        return mermaid_to_image(body)
    kept = []
    for c in cells:
        if c["cell_type"] == "markdown":
            text = "".join(c["source"])
            text = re.sub(r'```\{=html\}\n<style>.*?</style>\n```\n*', '', text, flags=re.S)
            text = re.sub(r'```\{mermaid\}\n(.*?)\n```', _fix_mermaid, text, flags=re.S)
            if not text.strip():
                continue  # drop a now-empty cell (e.g. the CSS-only block)
            c["source"] = text.splitlines(keepends=True)
        kept.append(c)
    cells = kept

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
