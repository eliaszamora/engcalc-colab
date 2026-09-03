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
from engcalc_colab.parser import _ALLOWED_CALLS, parse_cell
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


def test_every_call_the_language_accepts_can_be_looked_up():
    missing = sorted(_ALLOWED_CALLS - set(CATALOGUE))
    assert not missing, f"calls with no help entry: {missing}"


def test_the_catalogue_describes_nothing_the_language_refuses():
    """The other direction, and the one that rots quietly.

    An entry for a removed call teaches a form that no longer exists, and nothing else
    would notice: the help still renders, still reads well, and is wrong.
    """
    unknown = sorted(set(CATALOGUE) - _ALLOWED_CALLS)
    assert not unknown, f"help entries for calls that do not exist: {unknown}"


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_the_example_runs(name):
    """Every example, executed rather than read.

    This is the contract that makes the catalogue trustworthy. Checking that an example
    merely mentions the call it documents would pass for a form the parser rejects.
    """
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
    assert f"{name}(" in entry.example, (
        f"the example for {name} never calls it:\n{entry.example}"
    )


def test_help_for_one_call_shows_its_forms_and_its_example(monkeypatch):
    displayed = run_help(monkeypatch, "integrate")

    assert len(displayed) == 1 and isinstance(displayed[0], HTML)
    html = displayed[0].data
    assert "integrate(expression, variable, lower, upper)" in html
    assert "the variable of integration" in html
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
    assert "no help for 'integrat'" in printed
    assert "integrate" in printed


def test_a_name_with_no_near_match_still_explains_how_to_list(monkeypatch, capsys):
    run_help(monkeypatch, "zzz")
    printed = capsys.readouterr().out
    assert "%eng_help with no name lists every call" in printed


def test_an_entry_that_takes_arguments_documents_them():
    """A form with slots and no explanation of them is the defect this feature exists to fix."""
    for name, entry in sorted(CATALOGUE.items()):
        has_slots = any(
            form.partition("(")[2].rstrip(")").strip() for form in entry.forms
        )
        if has_slots:
            assert entry.arguments, f"{name} shows slots but explains none"
        else:
            # `summary()` takes nothing, and inventing an argument for it would be worse
            # than saying nothing. The rule cuts both ways.
            assert not entry.arguments, f"{name} takes nothing but explains arguments"
