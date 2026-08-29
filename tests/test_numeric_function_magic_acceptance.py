from IPython.display import Math


def test_eng_magic_accepts_direct_unit_function_argument_without_auxiliary_symbol(
    monkeypatch,
    capsys,
):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "M_UU(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2\n"
        "q := 2.8*tonf/m\n"
        "L := 4*m\n"
        "numeric(M_UU(0*m), kN*m)\n"
        "result(M_UU(0*m), kN*m)",
    )

    assert capsys.readouterr().out == ""
    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert latex.count("54.92") >= 2
