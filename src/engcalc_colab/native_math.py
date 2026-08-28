from __future__ import annotations

from html import unescape
import re

from latex2mathml.converter import convert

from .renderer import CalculationResult, render_responsive_results

_INLINE_MATH_RE = re.compile(r"\$([^$]*)\$", re.DOTALL)


def latex_fragments_to_mathml(html: str) -> str:
    """Convert EngCalc's inline $...$ fragments to native MathML markup."""

    def replace(match: re.Match[str]) -> str:
        latex = unescape(match.group(1))
        return convert(latex)

    return _INLINE_MATH_RE.sub(replace, html)


def render_responsive_native_results(results: list[CalculationResult]) -> str:
    """Render responsive EngCalc HTML with browser-native MathML fragments."""
    return latex_fragments_to_mathml(render_responsive_results(results))
