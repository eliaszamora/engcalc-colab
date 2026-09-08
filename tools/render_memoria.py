"""Render a memoria the way a notebook would, so a person can look at it.

    python tools/render_memoria.py memoria-preview.html [una-hoja.eng]

The sheet defaults to `tools/memoria.eng`. It is an argument because the frame benchmark
was rendered by a copy of this file kept in a scratch directory, and a copy is a second
implementation free to drift from this one - which is close to how the defect below got
through in the first place.

Everything else in this repository checks that a LaTeX string contains a substring. A
string that renders as garbage contains all the same substrings, so that kind of check
cannot see a broken page. This drives the real %%eng magic, captures exactly the objects
it hands to IPython display(), in order, and renders them the way Colab renders each
kind.

The first time it was run it found three defects in merged releases: an inequality that
raised AttributeError and killed the cell, and `governing(...)` and `summary()` whose
finished HTML was embedded inside a LaTeX array, so the reader saw the markup as text.
All three had passing contracts, because those called the renderers directly and never
asked whether the magic would route anything to them.

**Then it missed one, and the way it missed it is the more useful lesson.** #96 put a
narrative's mathematics on the page with MathJax's parenthesis delimiters, and this file
configured MathJax with `inlineMath: [['\\(','\\)']]` - the delimiters the magic had just
been taught to emit. So the page rendered, the screenshot looked right, and in Colab the
relations came out as raw text across the one memoria whose whole subject is a matrix
formulation. The harness was not measuring the notebook; it was measuring itself.

What Colab actually does was then measured in Colab, and this file mirrors it rather than
accommodating the library:

  * an HTML output does not typeset. Not with `\\(...\\)`, not with `$...$`, not with
    `\\[...\\]`, not with an explicit `MathJax.typeset()` call in the payload - Colab
    isolates it. Here that is `ignoreHtmlClass`, so mathematics smuggled back into an
    HTML output shows up on this page as the raw text it will be in the notebook.
  * a Markdown output is converted to HTML and typeset with `$...$`, after the maths is
    lifted out so the markdown converter cannot touch it. Same order as the notebook.
  * a Math output is `$\\displaystyle ...$`, which is literally IPython's own
    `Math._repr_latex_`.

The delimiters below are Colab's, not EngCalc's. If a future change needs this file
adjusted to make its output render, that is the finding.

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

SHEET = (
    pathlib.Path(sys.argv[2])
    if len(sys.argv) > 2
    else pathlib.Path(__file__).with_name("memoria.eng")
)
MEMORIA = SHEET.read_text(encoding="utf-8")

magics = magic.EngMagics()
magics.eng("", MEMORIA)

parts = []
for obj in CAPTURED:
    name = type(obj).__name__
    if name == "Math":
        # IPython 7.34.0's own Math._repr_latex_, character for character.
        parts.append('<div class="eq">$\\displaystyle ' + obj.data.strip("$") + "$</div>")
    elif name == "Markdown":
        # Handed to the browser as bytes, converted there. Colab converts markdown in
        # the browser too, and doing it here in Python would be a second implementation
        # to be wrong in a different way from the notebook's.
        encoded = base64.b64encode(obj.data.encode("utf-8")).decode("ascii")
        parts.append(f'<div class="block md" data-src="{encoded}"></div>')
    elif name == "HTML":
        # `no-mathjax` is the ignore class configured below. An HTML output does not
        # typeset in Colab, so it does not typeset here.
        parts.append('<div class="block no-mathjax">' + obj.data + "</div>")
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

page = r"""<!doctype html>
<meta charset="utf-8">
<title>memoria</title>
<script>
// MathJax's own defaults, which is what a notebook leaves them at. Writing only
// `[['$$','$$']]` here would have hidden a defect this file was rewritten to catch:
// `\[` is a display delimiter whether or not anyone remembers it is.
window.MathJax = {
  tex: {inlineMath: [['$','$']], displayMath: [['$$','$$'], ['\\[','\\]']]},
  options: {ignoreHtmlClass: 'no-mathjax'},
  startup: {typeset: false}
};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
<style>
 body {font: 15px/1.5 -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px 32px;
       max-width: 900px; background: #fff; color: #111;}
 .eq {margin: 2px 0;}
 .block {margin: 8px 0;}
 .md p {margin: 0 0 0.5em 0;}
 .unknown {color: #b00; font-weight: 600; padding: 6px; border: 2px solid #b00;}
 img {max-width: 100%;}
</style>
""" + "\n".join(parts) + r"""
<script>
// The notebook's order, not the convenient one: every delimiter MathJax knows is lifted
// out before the markdown converter runs, and put back verbatim afterwards. That order
// is not a detail - it is why `$A_e = R_e\,L_e\,T$` keeps its underscores and its thin
// spaces, and equally why a `\[` that the prose never meant as mathematics still reaches
// MathJax as an opening delimiter. A harness that converted markdown first would eat the
// backslash and quietly report that the prose was fine.
//
// `\$` is protected first and restored as `\$`, so MathJax prints a literal dollar
// instead of pairing two prices into one formula.
for (const el of document.querySelectorAll('.md')) {
  const raw = new TextDecoder().decode(
    Uint8Array.from(atob(el.dataset.src), c => c.charCodeAt(0)));
  let text = raw.replace(/\\\$/g, '@@ESCDOLLAR@@');
  const maths = [];
  const stash = (m) => { maths.push(m); return '@@MATH' + (maths.length - 1) + '@@'; };
  text = text.replace(/\$\$[\s\S]+?\$\$/g, stash);
  text = text.replace(/\\\[[\s\S]+?\\\]/g, stash);
  text = text.replace(/\$[^$\n]+\$/g, stash);
  let out = marked.parse(text);
  out = out.replace(/@@MATH(\d+)@@/g, (m, i) => maths[Number(i)]);
  el.innerHTML = out.replace(/@@ESCDOLLAR@@/g, '\\$');
}
MathJax.startup.promise.then(() => MathJax.typesetPromise());
</script>
"""

out = pathlib.Path(sys.argv[1])
out.write_text(page, encoding="utf-8")
print(f"{len(CAPTURED)} objetos mostrados -> {out}")
for obj in CAPTURED:
    print("   ", type(obj).__name__)
