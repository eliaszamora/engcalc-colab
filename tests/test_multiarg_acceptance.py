from IPython.display import Math


def test_magic_renders_multiarg_numeric_and_partial(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "M(x, q, L) = q*x*(L-x)/2\n"
        "qD := 10*kN/m\n"
        "L := 4*m\n"
        "numeric(M(2*m, qD, L), kN*m)\n"
        "numeric(M(x, qD, L))",
    )

    assert capsys.readouterr().out == ""
    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert r"M\left(x, q, L\right)" in latex
    assert latex.count(r"M\left(") >= 3
    assert "20.00" in latex
    assert "x" in latex


def test_magic_renders_nonpolynomial_multiarg_partial(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "v(x, A, L) = A*sin(pi*x/L)\n"
        "A := 20*mm\n"
        "L := 4*m\n"
        "numeric(v(x, A, L))",
    )

    assert capsys.readouterr().out == ""
    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert r"v\left(x, A, L\right)" in latex
    assert latex.count(r"v\left(") >= 2
    assert "20.00" in latex
    assert "mm" in latex
    assert "x" in latex


def test_result_multiarg_call_stays_compact(monkeypatch, capsys):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "M(x, q, L) = q*x*(L-x)/2\n"
        "qD := 10*kN/m\n"
        "L := 4*m",
    )
    displayed.clear()
    capsys.readouterr()

    magics.eng("", "result(M(2*m, qD, L), kN*m)")

    assert capsys.readouterr().out == ""
    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert latex.count(r"M\left(") == 1
    assert "20.00" in latex
    assert "10.00" not in latex
