from pathlib import Path

plot_path = Path("tests/test_plot_engine.py")
plot_text = plot_path.read_text()
plot_marker = "def test_plot_accepts_direct_multiarg_response():"
if plot_marker not in plot_text:
    plot_text += '''\n\ndef test_plot_accepts_direct_multiarg_response():\n    engine = EngineeringEngine()\n    eval_cell(\n        engine,\n        "M(x, q, L) = q*x*(L-x)/2\\n"\n        "qD := 4*kN/m\\n"\n        "L := 5*m",\n    )\n\n    result = eval_cell(engine, "plot(M(x, qD, L), x, 0*m, L)")[-1]\n\n    assert isinstance(result, PlotResult)\n    assert len(result.x_values) == 201\n    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(12.5)\n\n\ndef test_specialized_multiarg_function_plots_normally():\n    engine = EngineeringEngine()\n    eval_cell(\n        engine,\n        "M(x, q, L) = q*x*(L-x)/2\\n"\n        "M_D(x) = M(x, qD, L)\\n"\n        "qD := 4*kN/m\\n"\n        "L := 5*m",\n    )\n\n    result = eval_cell(engine, "plot(M_D(x), x, 0*m, L)")[-1]\n\n    assert isinstance(result, PlotResult)\n    assert len(result.x_values) == 201\n    assert result.series[0].y_values[100].to("kN*m").magnitude == pytest.approx(12.5)\n'''
    plot_path.write_text(plot_text)

envelope_path = Path("tests/test_envelope_engine.py")
envelope_text = envelope_path.read_text()
envelope_marker = "def test_envelope_accepts_specialized_multiarg_sources():"
if envelope_marker not in envelope_text:
    envelope_text += '''\n\ndef test_envelope_accepts_specialized_multiarg_sources():\n    engine = EngineeringEngine()\n    eval_cell(\n        engine,\n        "M(x, q, L) = q*x*(L-x)/2\\n"\n        "M_D(x) = M(x, qD, L)\\n"\n        "M_U(x) = M(x, 1.2*qD + 1.6*qL, L)\\n"\n        "qD := 4*kN/m\\n"\n        "qL := 2*kN/m\\n"\n        "L := 5*m",\n    )\n\n    result = eval_cell(\n        engine,\n        "envelope(M_D(x), M_U(x), x, 0*m, L)",\n    )[-1]\n\n    assert isinstance(result, PlotResult)\n    assert result.kind == "envelope"\n    assert len(result.x_values) == 201\n    assert result.source_series[0].y_values[100].to("kN*m").magnitude == pytest.approx(12.5)\n    assert result.source_series[1].y_values[100].to("kN*m").magnitude == pytest.approx(25.0)\n'''
    envelope_path.write_text(envelope_text)
