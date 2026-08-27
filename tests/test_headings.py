from IPython.display import HTML, Math

from engcalc_colab.models import ParsedStatement
from engcalc_colab.parser import parse_cell


def test_parser_preserves_double_and_triple_hash_headings():
    items = parse_cell("## Cálculo de reacciones\n\nA = 1\n### Equilibrio vertical\nB = 2\n# invisible")
    assert len(items) == 4
    assert items[0].text == "Cálculo de reacciones"
    assert items[0].level == 2
    assert isinstance(items[1], ParsedStatement)
    assert items[2].text == "Equilibrio vertical"
    assert items[2].level == 3
    assert isinstance(items[3], ParsedStatement)


def test_blank_line_after_heading_does_not_add_extra_group_gap():
    items = parse_cell("## Reacciones\n\nA = 1")
    assert items[0].blank_before is False
    assert items[1].blank_before is False


def test_magic_renders_headings_as_html_and_equations_as_math(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "## Cálculo de reacciones\nA = 1\n### Equilibrio vertical\nB = 2")

    assert [type(item) for item in displayed] == [HTML, Math, HTML, Math]
    assert "Cálculo de reacciones" in displayed[0].data
    assert "Equilibrio vertical" in displayed[2].data


def test_heading_html_escapes_user_text(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "## <script>alert(1)</script>\nA = 1")

    assert "<script>" not in displayed[0].data
    assert "&lt;script&gt;" in displayed[0].data
