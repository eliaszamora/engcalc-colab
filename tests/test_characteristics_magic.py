import pytest
from IPython.display import Math
from conftest import blocks_into


def test_eng_magic_flushes_equations_before_characteristic_block_and_resumes(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", blocks_into(displayed))

    magics = magic_module.EngMagics(shell=None)
    try:
        magics.eng(
            "",
            "A = 1\n"
            "f(x) = x - 1\n"
            "roots(f(x), x, 0, 2)\n"
            "B = 2",
        )
    except Exception as exc:  # RED should report missing routing as a test failure, not an error.
        pytest.fail(f"characteristic magic routing is missing or broken: {exc}")

    assert [type(item) for item in displayed] == [Math, Math, Math]
    # Its own output, and a computed block rather than equation rows: it opens as one. Its
    # room from the rows around it is the magic's, one rule for every block since
    # 2026-09-25 - see test_one_spacing_rule.
    assert r"\hspace{0.2em}\begin{array}{l} " in displayed[1].data
    assert "Roots" in displayed[1].data


def test_eng_magic_displays_consecutive_characteristic_results_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", blocks_into(displayed))

    magics = magic_module.EngMagics(shell=None)
    try:
        magics.eng(
            "",
            "f(x) = x - 1\n"
            "g(x) = 2 - x\n"
            "roots(f(x), x, 0, 2)\n"
            "intersections(f(x), g(x), x, 0, 2)",
        )
    except Exception as exc:
        pytest.fail(f"characteristic magic routing is missing or broken: {exc}")

    assert [type(item) for item in displayed] == [Math, Math, Math]
    assert "Roots" in displayed[1].data
    assert "Intersections" in displayed[2].data
