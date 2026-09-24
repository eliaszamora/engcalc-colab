r"""`image("portico.png", "Geometría y cargas", width=12*cm)`: a figure in the memoria.

Asked for on 2026-09-24 - *"la capacidad de colocar figuras o imágenes ... para que la
memoria de cálculo o los ejercicios que realice tengan su respectiva figuras"* - with the
numbering automatic. The file is read when the line runs and embedded in the output, so
the figure stays in the notebook, in a shared copy and in a PDF, whatever happens to the
file afterwards. A path is read from where the notebook runs (in Colab, `/content`, or
`/content/drive/MyDrive/...` once Drive is mounted); a URL is fetched.

The number belongs to the figure, not to the run: running the cell again keeps `Figura 1`
as `Figura 1`, a new figure takes the next number, and `%eng_reset` starts again at 1. The
caption is Markdown, so `$...$` in it is typeset as it is in a narrative. The label reads
"Figura", in Spanish: he chose it over the English of the block names ("déjalo como Figura").
"""

import base64
import contextlib
import io
import urllib.request

import pytest
from IPython.display import HTML, Markdown

import engcalc_colab.magic as magic
from engcalc_colab.errors import EngCalcError

# The smallest PNG there is: one transparent pixel.
PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@pytest.fixture
def images(tmp_path, monkeypatch):
    (tmp_path / "portico.png").write_bytes(PIXEL)
    (tmp_path / "viga.png").write_bytes(PIXEL)
    monkeypatch.chdir(tmp_path)
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str):
        captured.clear()
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magics.eng("", source)
        return captured[:], console.getvalue()

    run.magics = magics
    return run


def html_of(outputs) -> list[str]:
    return [o.data for o in outputs if isinstance(o, HTML)]


def captions(outputs) -> list[str]:
    return [o.data for o in outputs if isinstance(o, Markdown) and "Figura" in o.data]


def test_an_image_is_embedded_with_its_caption(images):
    outputs, console = images('image("portico.png", "Geometría y cargas")\n')
    assert not console, console
    (figure,) = html_of(outputs)
    assert "data:image/png;base64," + base64.b64encode(PIXEL).decode() in figure
    assert captions(outputs) == ["**Figura 1.** Geometría y cargas"]


def test_figures_are_numbered_in_order(images):
    outputs, _ = images('image("portico.png", "Pórtico")\nimage("viga.png", "Viga")\n')
    assert captions(outputs) == ["**Figura 1.** Pórtico", "**Figura 2.** Viga"]


def test_running_the_cell_again_keeps_the_numbers(images):
    source = 'image("portico.png", "Pórtico")\nimage("viga.png", "Viga")\n'
    images(source)
    outputs, _ = images(source)
    assert captions(outputs) == ["**Figura 1.** Pórtico", "**Figura 2.** Viga"]


def test_a_reset_starts_again_at_one(images):
    images('image("portico.png", "Pórtico")\nimage("viga.png", "Viga")\n')
    with contextlib.redirect_stdout(io.StringIO()):
        images.magics.eng_reset("")
    outputs, _ = images('image("viga.png", "Viga")\n')
    assert captions(outputs) == ["**Figura 1.** Viga"]


def test_the_caption_may_hold_mathematics(images):
    outputs, _ = images('image("portico.png", "Carga $w = 2000$ kgf/m")\n')
    assert captions(outputs) == ["**Figura 1.** Carga $w = 2000$ kgf/m"]


def test_an_image_without_a_caption_is_still_numbered(images):
    outputs, _ = images('image("portico.png")\n')
    assert captions(outputs) == ["**Figura 1.**"]


@pytest.mark.parametrize("width, css", [("12*cm", "width:12.00cm"), ("80*mm", "width:8.00cm")])
def test_a_width_is_given_in_length(images, width, css):
    outputs, _ = images(f'image("portico.png", "Pórtico", width={width})\n')
    (figure,) = html_of(outputs)
    assert css in figure.replace(" ", ""), figure


def test_a_width_that_is_not_a_length_says_so(images):
    _outputs, console = images('image("portico.png", "Pórtico", width=12*kgf)\n')
    assert "width" in console and "length" in console, console


def test_a_missing_file_says_where_it_looked(images):
    _outputs, console = images('image("no_esta.png", "Nada")\n')
    assert "no_esta.png" in console and "not found" in console, console


def test_an_image_can_come_from_a_url(images, monkeypatch):
    class Response(io.BytesIO):
        headers = {"Content-Type": "image/png"}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=30: Response(PIXEL))
    outputs, console = images('image("https://example.com/portico.png", "Desde la web")\n')
    assert not console, console
    assert "data:image/png;base64," in html_of(outputs)[0]


def test_an_image_stands_on_its_own_line(images):
    _outputs, console = images('f = image("portico.png")\n')
    assert "image" in console and "own line" in console, console


def test_only_a_width_may_be_named(images):
    _outputs, console = images('image("portico.png", height=3*cm)\n')
    assert "width" in console, console
