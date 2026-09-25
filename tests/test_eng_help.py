"""`%eng_help` — what each call takes, and an example of it.

A notebook gives no help for a cell magic's own language. `Shift+Tab` reads a Python
object's signature, and `integrate` inside `%%eng` is a name in a restricted grammar,
not a function object. So the help is a line magic, beside `%eng_reset` and
`%eng_config`.

The whole risk of a hand-written catalogue is that it drifts from the code, in two
directions: a call with no entry cannot be looked up, and an entry can describe a form
the language refuses. Both are closed here, and the second by running every example
rather than reading it. A help text that does not run is worse than none - it teaches a
form that fails, and the reader blames their own typing.
"""

import pytest
from IPython.display import HTML

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import _ALLOWED_CALLS, _DECLARATIONS, PLACING_CALLS, parse_cell
from engcalc_colab.reference import CATALOGUE


def run_cell(source: str):
    engine = EngineeringEngine()
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def run_help(monkeypatch, line: str):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magic_module.EngMagics(shell=None).eng_help(line)
    return displayed


# Everything a sheet can write that has a name of its own: the calls, the calls that
# place something on the page, and the statement forms `keep`, `case`, `combo` and `:=`.
# He asked on 2026-09-24 what `keep` was for: it was the one thing on the frame's sheet
# the help had no entry for, and neither had `member`, `frame_plot` or `image`.
DOCUMENTED = _ALLOWED_CALLS | PLACING_CALLS | set(_DECLARATIONS) | {":="}


def test_every_call_the_language_accepts_can_be_looked_up():
    missing = sorted(DOCUMENTED - set(CATALOGUE))
    assert not missing, f"calls with no help entry: {missing}"


def test_the_catalogue_describes_nothing_the_language_refuses():
    """The other direction, and the one that rots quietly.

    An entry for a removed call teaches a form that no longer exists, and nothing else
    would notice: the help still renders, still reads well, and is wrong.
    """
    unknown = sorted(set(CATALOGUE) - DOCUMENTED)
    assert not unknown, f"help entries for calls that do not exist: {unknown}"


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_the_example_runs(name, tmp_path, monkeypatch):
    """Every example, executed rather than read.

    This is the contract that makes the catalogue trustworthy. Checking that an example
    merely mentions the call it documents would pass for a form the parser rejects.
    `image` reads a file, so its example runs where one is.
    """
    import base64

    (tmp_path / "portico.png").write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    ))
    monkeypatch.chdir(tmp_path)
    entry = CATALOGUE[name]
    try:
        results = run_cell(entry.example)
    except Exception as exc:  # noqa: BLE001 - any failure is the finding
        pytest.fail(f"help example for {name} does not run: {exc}\n{entry.example}")
    assert results, f"help example for {name} produced nothing"


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_the_example_uses_the_call_it_documents(name):
    """An example that runs but never calls the function teaches nothing.

    `test_the_example_runs` alone would accept `a = 1` for every entry.
    """
    entry = CATALOGUE[name]
    if name == "macaulay":
        # The bracket notation is how it is written; the call form exists because that
        # is what the notation is rewritten to, so the example shows the notation.
        assert "<x-a>^1" in entry.example, entry.example
        return
    if entry.kind == "statement":
        written = f" {name} " if name == ":=" else f"{name} "
        assert any(line.startswith(written.lstrip()) or written in line for line in entry.example.splitlines()), (
            f"the example for {name} never writes it:\n{entry.example}"
        )
        return
    assert f"{name}(" in entry.example, (
        f"the example for {name} never calls it:\n{entry.example}"
    )


def test_help_for_one_call_shows_its_forms_and_its_example(monkeypatch):
    displayed = run_help(monkeypatch, "integrate")

    assert len(displayed) == 1 and isinstance(displayed[0], HTML)
    html = displayed[0].data
    assert "integrate(expresión, variable, inferior, superior)" in html
    assert "la variable de integración" in html
    # The example is shown, not merely stored.
    assert "V(x) = q*L/2 - q*x" in html


def test_help_with_no_name_lists_every_call(monkeypatch):
    displayed = run_help(monkeypatch, "")

    assert len(displayed) == 1
    html = displayed[0].data
    for name in ("integrate", "solve", "numeric", "governing", "eigenvects"):
        assert name in html, name


def test_an_unknown_name_suggests_rather_than_raising(monkeypatch, capsys):
    """A notebook cell that raises on a typo in a help request is its own small defect."""
    displayed = run_help(monkeypatch, "integrat")

    assert displayed == []
    printed = capsys.readouterr().out
    assert "no hay ayuda para 'integrat'" in printed
    assert "integrate" in printed


def test_a_name_with_no_near_match_still_explains_how_to_list(monkeypatch, capsys):
    run_help(monkeypatch, "zzz")
    printed = capsys.readouterr().out
    assert "%eng_help sin nombre lista todo" in printed


def test_an_entry_that_takes_arguments_documents_them():
    """A form with slots and no explanation of them is the defect this feature exists to fix."""
    for name, entry in sorted(CATALOGUE.items()):
        if entry.kind == "statement":
            # A statement's slots are names in its form, not parentheses.
            assert entry.arguments, f"{name} is a statement and explains none of its parts"
            continue
        has_slots = any(
            form.partition("(")[2].rstrip(")").strip() for form in entry.forms
        )
        if has_slots:
            assert entry.arguments, f"{name} shows slots but explains none"
        else:
            # `summary()` takes nothing, and inventing an argument for it would be worse
            # than saying nothing. The rule cuts both ways.
            assert not entry.arguments, f"{name} takes nothing but explains arguments"


def test_help_for_keep_says_what_it_is_for(monkeypatch):
    """He asked what `keep` is for. The entry answers with the page, before and after."""
    (html,) = [item.data for item in run_help(monkeypatch, "keep")]
    assert "keep nombre = expresión" in html
    assert "C = 0.85 b d fc" in html and "C = f_cw b d" in html, html


def test_help_explains_how_a_frame_is_drawn(monkeypatch):
    (html,) = [item.data for item in run_help(monkeypatch, "member")]
    assert "N_i; V_i; M_i; N_j; V_j; M_j" in html
    assert "equilibrio" in html, html


def test_the_list_shows_the_statements_apart(monkeypatch):
    (html,) = [item.data for item in run_help(monkeypatch, "")]
    assert "Sentencias" in html and "keep nombre = expresión" in html
    assert html.index("Sentencias") < html.index("Funciones"), html


def test_the_help_is_written_in_spanish(monkeypatch):
    """He asked for it in Spanish (2026-09-25): *"Tradúcela al español"*. The names of the
    calls and the examples stay as the language writes them."""
    (html,) = [item.data for item in run_help(monkeypatch, "numeric")]
    assert "Argumentos" in html and "Ejemplo" in html, html
    assert "Evalúa" in html, html
    assert "numeric(expresión, unidad)" in html, html
    for entry in CATALOGUE.values():
        assert not entry.summary.startswith(("The ", "A ", "An ", "Draw", "Show")), entry.summary


def test_the_help_for_table_counts_what_table_counts(monkeypatch):
    """The last argument of `table` is the number of rows, both ends included - the beam
    sheet's `table(..., 11)` is "Once estaciones". The help said "how many intervals",
    which gives one row more than the table draws. Found translating the help."""
    import contextlib
    import io

    import engcalc_colab.magic as magic_module
    from IPython.display import Math

    (html,) = [item.data for item in run_help(monkeypatch, "table")]
    assert "estaciones" in html and "ambos extremos" in html, html
    shown = []
    monkeypatch.setattr(magic_module, "display", shown.append)
    with contextlib.redirect_stdout(io.StringIO()):
        magic_module.EngMagics(shell=None).eng(
            "", "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\ntable(M(x), x, 0, L, 4)\n"
        )
    table = [item.data for item in shown if isinstance(item, Math)][-1]
    assert table.split(r"\hline", 1)[1].count("&") == 4, table
