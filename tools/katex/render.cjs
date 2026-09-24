// Typeset formulas the way Colab does, and report what fails.
//
// Colab typesets a notebook's `text/latex` outputs, and the mathematics inside its
// Markdown, with KaTeX 0.16.28 - asked from inside an output on 2026-09-23. This reads a
// JSON list of {tex, display} on stdin and writes, for each, {error, warnings}: `error`
// is what KaTeX throws (Colab would show the formula as red source text), `warnings` what
// its strict mode reports about LaTeX it accepts but would not take from real TeX.
//
// Used by tests/test_colab_can_typeset_every_formula.py. Install with
//     npm ci --prefix tools/katex
const katex = require("katex");

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const formulas = JSON.parse(input);
  const results = formulas.map(({ tex, display }) => {
    const warnings = [];
    try {
      katex.renderToString(tex, {
        displayMode: display,
        throwOnError: true,
        strict: (code, message) => { warnings.push(`${code}: ${message}`); return "ignore"; },
      });
      return { error: null, warnings };
    } catch (error) {
      return { error: String(error.message || error), warnings };
    }
  });
  process.stdout.write(JSON.stringify({ version: katex.version, results }));
});
