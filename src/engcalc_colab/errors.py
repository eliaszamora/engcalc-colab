class EngCalcError(Exception):
    """Base user-facing engcalc error."""


class EngSyntaxError(EngCalcError):
    pass


class EngEvaluationError(EngCalcError):
    pass


class AmbiguousSolveError(EngEvaluationError):
    pass


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
    raise ValueError(f"unknown diagnostic code '{code}'")
