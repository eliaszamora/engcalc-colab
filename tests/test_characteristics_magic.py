import pytest
from IPython.display import HTML, Math


def test_eng_magic_flushes_equations_before_characteristic_block_and_resumes(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

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

    assert [type(item) for item in displayed] == [Math, HTML, Math]
    assert "engcalc-characteristics" in displayed[1].data
    assert "Roots" in displayed[1].data


def test_eng_magic_displays_consecutive_characteristic_results_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

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

    assert [type(item) for item in displayed] == [Math, HTML, HTML]
    assert "Roots" in displayed[1].data
    assert "Intersections" in displayed[2].data
