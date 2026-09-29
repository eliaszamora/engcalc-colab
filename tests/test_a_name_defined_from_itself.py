r"""A name defined from itself stops with its name, and does not hang the notebook.

`v := 2` then `v = v*2` keeps `v` a name in its own formula, `v = 2 v`, and asking for its
number put `2 v` in for `v` without end - `4 v`, `8 v`, ... - until the kernel hung (found
by the second audit of 0.43.2, 2026-09-28, on every release back to 0.41.2 at least). A
chain of definitions resolves in as many passes as the sheet has names; one that goes on
past them goes round, and the line says which name.

Run in a subprocess: a regression hangs, and a hang in-process would hang the suite.
"""

import subprocess
import sys
import textwrap

import pytest

RUN = textwrap.dedent(
    """
    import contextlib, io, sys
    from IPython.display import Math
    import engcalc_colab.magic as magic
    captured = []
    magic.display = captured.append
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", sys.argv[1])
    print(console.getvalue())
    print(" ".join(i.data for i in captured if isinstance(i, Math)))
    """
)


def _run(source: str) -> str:
    done = subprocess.run(
        [sys.executable, "-c", RUN, source], capture_output=True, text=True, timeout=60,
        encoding="utf-8",
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


@pytest.mark.parametrize(
    "source",
    [
        "v := 2\nv = v*2\nnumeric(v)\n",
        "v := 2\nv = v + 1\nnumeric(v)\n",
        "v := 2*m\nv = 2*v^2/m\nnumeric(v)\n",
    ],
)
def test_a_name_defined_from_itself_says_so(source):
    out = _run(source)
    assert "is defined from itself" in out, out


def test_a_long_chain_still_resolves():
    # Written from the end, each name is read through the next: thirty passes, 2^30 m.
    lines = [f"x_{i} = 2*x_{i - 1}" for i in range(30, 0, -1)] + ["x_0 := 1[m]", "numeric(x_30)"]
    out = _run("\n".join(lines) + "\n")
    assert "defined from itself" not in out, out
    assert r"1.07 \times 10^{9}\,\mathrm{m} \end{array}" in out, out
