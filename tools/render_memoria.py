"""Render a memoria the way a notebook would, so a person can look at it.

    python tools/render_memoria.py memoria-preview.html

Everything else in this repository checks that a LaTeX string contains a substring. A
string that renders as garbage contains all the same substrings, so that kind of check
cannot see a broken page. This drives the real %%eng magic, captures exactly the objects
it hands to IPython display(), in order, and wraps them in MathJax.

The first time it was run it found three defects in merged releases: an inequality that
raised AttributeError and killed the cell, and `governing(...)` and `summary()` whose
finished HTML was embedded inside a LaTeX array, so the reader saw the markup as text.
All three had passing contracts, because those called the renderers directly and never
asked whether the magic would route anything to them.

Run it and look at the result. That is the whole point.
"""
import base64
import html
import io
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")

import engcalc_colab.magic as magic  # noqa: E402

CAPTURED = []


def fake_display(obj):
    CAPTURED.append(obj)


magic.display = fake_display

MEMORIA = pathlib.Path(__file__).with_name("memoria.eng").read_text(encoding="utf-8")

magics = magic.EngMagics()
magics.eng("", MEMORIA)

parts = []
for obj in CAPTURED:
    name = type(obj).__name__
    if name == "Math":
        parts.append('<div class="eq">\\[' + obj.data + "\\]</div>")
    elif name == "HTML":
        parts.append('<div class="block">' + obj.data + "</div>")
    elif hasattr(obj, "savefig"):
        buffer = io.BytesIO()
        obj.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        parts.append(f'<div class="block"><img src="data:image/png;base64,{encoded}"></div>')
    else:
        parts.append(
            '<div class="unknown">unrecognised display object: '
            + html.escape(name)
            + "</div>"
        )

page = """<!doctype html>
<meta charset="utf-8">
<title>memoria</title>
<script>
window.MathJax = {tex: {inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']]}};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
<style>
 body {font: 15px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px 32px;
       max-width: 900px; background: #fff; color: #111;}
 .eq {margin: 2px 0;}
 .block {margin: 8px 0;}
 .unknown {color: #b00; font-weight: 600; padding: 6px; border: 2px solid #b00;}
 img {max-width: 100%;}
</style>
""" + "\n".join(parts)

out = pathlib.Path(sys.argv[1])
out.write_text(page, encoding="utf-8")
print(f"{len(CAPTURED)} objetos mostrados -> {out}")
for obj in CAPTURED:
    print("   ", type(obj).__name__)
