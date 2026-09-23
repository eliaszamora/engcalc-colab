class EngCalcError(Exception):
    """Base user-facing engcalc error."""


class EngSyntaxError(EngCalcError):
    pass


class EngEvaluationError(EngCalcError):
    pass


class AmbiguousSolveError(EngEvaluationError):
    pass


class NoRealValueError(EngEvaluationError):
    """A value with no real result: the root of a negative number, the logarithm of one.

    Its own type because one caller must tell it from every other failure: `roots` reads
    it as a candidate outside the real domain - `sqrt(-a)` for `x^2 + a` - where any other
    error means the candidate could not be evaluated and the fallback has to run.
    """


def diagnostic_hint(code: str, **context) -> str:
    """Return a stable corrective hint for a known engineering-facing error."""
    if code == "direct_numeric_argument":
        example = context.get("example", "M(2.5*m)")
        return f"Use numeric({example}) directly when the function argument is fully numeric."
    if code == "unknown_numeric_name":
        name = context["name"]
        return f"Define the numeric value first, for example: {name} := <value>*<unit>."
    if code == "incompatible_function_units":
        function = context["function"]
        return f"Provide compatible units for the argument and terms of numeric function '{function}'."
    if code == "unresolved_numeric_symbols":
        names = tuple(context.get("names", ()))
        examples = ", ".join(f"{name} := <value>*<unit>" for name in names)
        return f"Define the missing numeric values first, for example: {examples}."
    if code == "keyword_unit_name":
        name = context["name"]
        replacement = context["replacement"]
        return (
            f"'{name}' is a Python keyword and cannot be a name here; "
            f"write {replacement}."
        )
    raise ValueError(f"unknown diagnostic code '{code}'")
