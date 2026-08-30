from pathlib import Path


path = Path("src/engcalc_colab/models.py")
text = path.read_text(encoding="utf-8")
marker = "\n\n@dataclass(frozen=True)\nclass PlotSeries:\n"
if text.count(marker) != 1:
    raise SystemExit("could not locate unique PlotSeries insertion point")

models = '''

_CHARACTERISTIC_PROVENANCE = {"exact", "numeric"}
_CHARACTERISTIC_SIDES = {"at", "left", "right"}


@dataclass(frozen=True)
class CharacteristicPoint:
    x_symbolic: Any
    x_quantity: Any
    value_symbolic: Any | None
    value_quantity: Any | None
    provenance: str
    side: str = "at"
    roles: tuple[str, ...] = ()
    source_label: str | None = None

    def __post_init__(self) -> None:
        if self.provenance not in _CHARACTERISTIC_PROVENANCE:
            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")
        if self.side not in _CHARACTERISTIC_SIDES:
            raise ValueError("characteristic side must be 'at', 'left' or 'right'")
        object.__setattr__(self, "roles", tuple(self.roles))


@dataclass(frozen=True)
class CharacteristicInterval:
    lower_symbolic: Any
    upper_symbolic: Any
    lower_quantity: Any
    upper_quantity: Any
    role: str
    provenance: str = "exact"
    value_symbolic: Any | None = None
    value_quantity: Any | None = None

    def __post_init__(self) -> None:
        if self.provenance not in _CHARACTERISTIC_PROVENANCE:
            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")


@dataclass(frozen=True)
class RootsResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))


@dataclass(frozen=True)
class IntersectionsResult:
    statement: ParsedStatement
    left_label: str
    right_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))


@dataclass(frozen=True)
class ExtremaResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()
    unbounded_above: bool = False
    unbounded_below: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))
'''

text = text.replace(marker, models + marker, 1)
path.write_text(text, encoding="utf-8")
