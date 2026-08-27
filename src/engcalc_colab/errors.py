class EngCalcError(Exception):
    """Base user-facing engcalc error."""


class EngSyntaxError(EngCalcError):
    pass


class EngEvaluationError(EngCalcError):
    pass


class AmbiguousSolveError(EngEvaluationError):
    pass
