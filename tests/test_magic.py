from IPython.display import HTML, Math
from IPython.terminal.interactiveshell import TerminalInteractiveShell


def _fresh_shell():
    shell = TerminalInteractiveShell.instance()
    try:
        shell.extension_manager.unload_extension("engcalc_colab")
    except Exception:
        pass
    return shell


def _eng_magics_instance(shell):
    return shell.magics_manager.magics["cell"]["eng"].__self__


def test_extension_registers_eng_and_reset_magics():
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    assert "eng" in shell.magics_manager.magics["cell"]
    assert "eng_reset" in shell.magics_manager.magics["line"]


def test_magic_persists_state_and_reset_clears_it():
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    shell.run_cell_magic("eng", "", "M_0 = -q/2*(L-x)^2")
    magics = _eng_magics_instance(shell)
    assert "M_0" in magics.engine.namespace
    shell.run_cell_magic("eng", "", "Delta = integral(M_0, x, 0, L)")
    assert "Delta" in magics.engine.namespace
    shell.run_line_magic("eng_reset", "")
    assert magics.engine.namespace == {}


def test_reference_beam_runs_through_eng_magic():
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    shell.run_line_magic("eng_reset", "")
    shell.run_cell_magic("eng", "", """
M_0 = -q/2*(L-x)^2
m_B = L-x
Delta_B = integral(M_0*m_B/(E*I), x, 0, L)
f_BB = integral(m_B^2/(E*I), x, 0, L)
R_B = solve(Delta_B + R_B*f_BB = 0, R_B)
""")
    magics = _eng_magics_instance(shell)
    assert str(magics.engine.namespace["R_B"]) == "3*L*q/8"


def test_magic_prints_concise_user_errors_without_traceback(capsys):
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    for source in [
        'A = __import__("os")',
        "A = obj.attr",
        "R = solve(x^2 = 1, x)",
        "A = integral(x, x, 0)",
    ]:
        shell.run_cell_magic("eng", "", source)
    output = capsys.readouterr().out
    assert "engcalc:" in output
    assert "Traceback" not in output
    assert "unsupported function '__import__'" in output
    assert "unsupported syntax 'Attribute'" in output
    assert "solve returned 2 solutions for x; v0.1 requires one" in output
    assert "integral expects 4 arguments: expression, variable, lower, upper" in output


def test_eng_magic_returns_none_so_jupyter_does_not_echo_internal_results():
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    result = shell.run_cell_magic("eng", "", "A = x^2")
    assert result is None


def test_magic_renders_blank_lines_inside_one_math_group(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "A = 1\n\n\nB = 2")

    assert [type(item) for item in displayed] == [Math]
    assert r"\\[6pt]" in displayed[0].data
