from IPython.display import Math
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


def test_extension_registers_eng_reset_and_config_magics():
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    assert "eng" in shell.magics_manager.magics["cell"]
    assert "eng_reset" in shell.magics_manager.magics["line"]
    assert "eng_config" in shell.magics_manager.magics["line"]


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
    assert r"\\[8pt]" in displayed[0].data


def test_eng_reset_reports_general_state_clear(capsys):
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")

    shell.run_line_magic("eng_reset", "")

    assert capsys.readouterr().out.strip() == "engcalc state cleared"


def test_magic_uses_mathjax_when_group_contains_numeric_evaluation(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "V_B = 3*q*L/8\nq := 2.8*tonf/m\nL := 4*m\nnumeric(V_B)",
    )

    assert [type(item) for item in displayed] == [Math]
    latex = displayed[0].data
    assert r"\begin{array}{lcl}" in latex
    assert "4.20" in latex


def test_eng_config_updates_and_reports_render_settings(capsys):
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")
    magics = _eng_magics_instance(shell)

    shell.run_line_magic("eng_config", "precision=4 zero_tolerance=1e-6")

    assert magics.render_settings.precision == 4
    assert magics.render_settings.zero_tolerance == 1e-6
    assert "precision=4" in capsys.readouterr().out

    shell.run_line_magic("eng_config", "")
    output = capsys.readouterr().out
    assert "precision=4" in output
    assert "zero_tolerance=1e-06" in output


def test_eng_config_rejects_unknown_or_invalid_options_without_traceback(capsys):
    shell = _fresh_shell()
    shell.extension_manager.load_extension("engcalc_colab")

    shell.run_line_magic("eng_config", "unknown=3")
    shell.run_line_magic("eng_config", "precision=-1")

    output = capsys.readouterr().out
    assert "engcalc:" in output
    assert "unknown option 'unknown'" in output
    assert "precision must be an integer from 0 to 10" in output
    assert "Traceback" not in output


def test_eng_magic_flushes_math_before_plot_and_resumes_after(monkeypatch):
    import engcalc_colab.magic as magic_module
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\nq := 2.8*tonf/m\nL := 4*m\n"
        "plot(A*x, x, 0, L)\nB = 2*A",
    )
    assert [type(item) for item in displayed] == [Math, Figure, Math]


def test_eng_magic_displays_one_figure_for_parameter_sweep_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\n"
        "M(x) = q*x*(L-x)/2\n"
        "L := 6*m\n"
        "plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])\n"
        "B = 2*A",
    )

    assert [type(item) for item in displayed] == [Math, Figure, Math]


def test_eng_magic_displays_one_envelope_figure_in_source_order(monkeypatch):
    import engcalc_colab.magic as magic_module
    from matplotlib.figure import Figure

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng(
        "",
        "A = q*L\n"
        "M(x) = q*x*(L-x)/2\n"
        "L := 6*m\n"
        "envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])\n"
        "B = 2*A",
    )

    assert [type(item) for item in displayed] == [Math, Figure, Math]
