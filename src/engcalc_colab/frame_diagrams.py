"""The diagrams of a frame, drawn on the frame: what `frame_plot` puts on the page.

Approved on 2026-09-24 over a mock-up of `tools/portico_matricial.eng`. Every member is read
as a beam seen from inside the frame - option (b): a moment is positive when it pulls the
inside fibre, so a knee reads one number from the beam and from the column - and the shear
follows the same reading. The moment is drawn on the side it pulls; shear and axial force
are drawn outside when positive. Values carry their sign, in boxes; loads are red; a
distributed load starts and ends with an arrow at the member's ends.

Nothing here solves anything: the member forces and displacements are the sheet's. What a
joint carries is read back from them - the end forces meeting at a free joint add up to the
load applied there - and a support is a joint the sheet's displacements hold still.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .models import FrameMember, FramePlotResult
from .plotting import _unit_mathtext
from .unit_text import unit_text

FRAME_COLOUR = "#333333"
LOAD_COLOUR = "#b03a2e"
LABEL_COLOUR = "#1f3b57"
LABEL_EDGE = "#9bbad6"
DIAGRAM_COLOUR = {"M": "#1f77b4", "V": "#2e8b57", "N": "#8e44ad", "deformed": "#c0392b"}
_SAMPLES = 121
# Sizes as parts of the frame's larger dimension, from the mock-up he approved.
_DIAGRAM_PEAK = 0.18
_DEFORMED_PEAK = 0.12
_LOAD_NEAR, _LOAD_FAR = 0.12, 0.19
_JOINT_ARROW = 0.17
_SUPPORT_WIDTH = 0.12
# Below this part of the largest value, a number is the float noise of a zero.
_NOISE = 1e-9


@dataclass
class _Member:
    """One member in two sets of numbers: drawing units for where, base units for what."""

    source: FrameMember
    start: tuple[float, float]
    end: tuple[float, float]
    ex: tuple[float, float]
    ey: tuple[float, float]
    length: float  # base units
    forces: list[float] | None
    displacements: list[float] | None
    load: float
    stiffness: float | None
    inside: float = 1.0  # +1 when -y' faces the inside of the frame, -1 when +y' does

    def at(self, s: float) -> tuple[float, float]:
        """The drawing point a base-unit distance `s` along the member."""
        part = s / self.length
        return (
            self.start[0] + part * (self.end[0] - self.start[0]),
            self.start[1] + part * (self.end[1] - self.start[1]),
        )


def _base(quantity) -> float:
    return float(quantity.to_base_units().magnitude)


def _entries(matrix) -> list[float] | None:
    if matrix is None:
        return None
    return [_base(entry) if hasattr(entry, "to_base_units") else float(entry) for entry in matrix]


class _Units:
    """The unit each kind of label is written in: the one the page writes its largest in.

    `convert` is the page's choice - the palette's unit, or the family's - and it is asked
    about the largest value of each kind, as the page would be asked about that value.
    """

    def __init__(self, members: tuple[FrameMember, ...], convert: Callable[[Any], Any]):
        self.convert = convert
        self.references: dict[str, Any] = {}
        candidates: dict[str, list] = {}
        for member in members:
            for kind, matrix, positions in (
                ("N", member.forces, (0, 3)),
                ("V", member.forces, (1, 4)),
                ("M", member.forces, (2, 5)),
                ("displacement", member.displacements, (0, 1, 3, 4)),
            ):
                if matrix is not None:
                    entries = list(matrix)
                    candidates.setdefault(kind, []).extend(entries[p] for p in positions)
            if member.load is not None:
                candidates.setdefault("load", []).append(member.load)
            candidates.setdefault("length", []).extend((*member.start, *member.end))
        for kind, quantities in candidates.items():
            quantities = [q for q in quantities if hasattr(q, "to_base_units") and q.magnitude != 0]
            if quantities:
                self.references[kind] = max(quantities, key=lambda q: abs(_base(q)))

    def unit(self, kind: str):
        reference = self.references.get(kind)
        return None if reference is None else self.convert(reference).units

    def written(self, kind: str, value: float) -> float:
        """A base-unit value in the unit its kind is written in."""
        reference = self.references.get(kind)
        if reference is None:
            return value
        base = reference.to_base_units()
        quantity = base._REGISTRY.Quantity(value, base.units)
        return float(quantity.to(self.convert(reference).units).magnitude)

    def text(self, kind: str) -> str:
        unit = self.unit(kind)
        return "" if unit is None else unit_text(unit)

    def title(self, kind: str) -> str:
        unit = self.unit(kind)
        maths = "" if unit is None else _unit_mathtext(unit)
        return f" [{maths}]" if maths else ""


def _number(value: float, largest: float = 0.0) -> str:
    """`-519 596`, `620`, `0.63`: whole numbers from a hundred, two decimals below."""
    if value == 0 or abs(value) <= _NOISE * largest:
        return "0"
    size = abs(value)
    if size >= 100:
        text = f"{value:,.0f}".replace(",", " ")
    elif size >= 0.01:
        text = f"{value:.2f}"
    else:
        text = f"{value:.3g}"
    if text.startswith("-") and not text.strip("-0."):
        return text[1:]
    return text


def _members(result: FramePlotResult, units: _Units) -> list[_Member]:
    length = units.references.get("length")
    if length is None:
        raise ValueError("a frame of no length")
    draw_unit = units.convert(length).units

    def drawn(point) -> tuple[float, float]:
        return tuple(float(coordinate.to(draw_unit).magnitude) for coordinate in point)

    members = []
    for member in result.members:
        start, end = drawn(member.start), drawn(member.end)
        dx, dy = end[0] - start[0], end[1] - start[1]
        span = math.hypot(dx, dy)
        ex = (dx / span, dy / span)
        members.append(
            _Member(
                source=member,
                start=start,
                end=end,
                ex=ex,
                ey=(-ex[1], ex[0]),
                length=math.hypot(*(_base(b - a) for a, b in zip(member.start, member.end))),
                forces=_entries(member.forces),
                displacements=_entries(member.displacements),
                load=_base(member.load) if member.load is not None else 0.0,
                stiffness=_base(member.stiffness) if member.stiffness is not None else None,
            )
        )
    # The inside of the frame is towards the middle of its joints. A member with the middle
    # on its +y' side is read backwards; a straight beam alone has it on its own line.
    joints = {point for member in members for point in (member.start, member.end)}
    middle = (
        sum(point[0] for point in joints) / len(joints),
        sum(point[1] for point in joints) / len(joints),
    )
    size = _size(members)
    for member in members:
        centre = member.at(member.length / 2)
        towards = (middle[0] - centre[0]) * member.ey[0] + (middle[1] - centre[1]) * member.ey[1]
        member.inside = -1.0 if towards > 1e-9 * size else 1.0
    return members


def _size(members: list[_Member]) -> float:
    xs = [x for member in members for x in (member.start[0], member.end[0])]
    ys = [y for member in members for y in (member.start[1], member.end[1])]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def _along(member: _Member) -> list[float]:
    return [member.length * index / (_SAMPLES - 1) for index in range(_SAMPLES)]


def _internal(member: _Member, diagram: str, s: float) -> float:
    """N, V or M at `s`, in local axes: tension, +y' on the left face, sagging (-y') fibre."""
    f, q = member.forces, member.load
    if diagram == "N":
        return -f[0]
    if diagram == "V":
        return f[1] - q * s
    return -f[2] + f[1] * s - q * s * s / 2


def _key(point: tuple[float, float], size: float) -> tuple[int, int]:
    return (round(point[0] / size * 1e6), round(point[1] / size * 1e6))


class _Drawing:
    def __init__(self, result: FramePlotResult, convert: Callable[[Any], Any]):
        import matplotlib.pyplot as plt

        self.result = result
        self.units = _Units(result.members, convert)
        self.members = _members(result, self.units)
        self.size = _size(self.members)
        first = self.members[0]
        # Drawing units per base unit: the figure is drawn in the sheet's length unit.
        self.per_base = math.hypot(first.end[0] - first.start[0], first.end[1] - first.start[1]) / first.length
        self.figure, self.axis = plt.subplots()
        self.points: list[tuple[float, float]] = []
        # How far a diagram reaches out from each member, so its load is drawn beyond it.
        self.reach: dict[int, dict[float, float]] = {}
        plt.close(self.figure)

    # -- what every diagram shares ---------------------------------------------------

    def box(self, point, text: str, offset=(0, 0), colour: str = LABEL_COLOUR):
        self.axis.annotate(
            text,
            xy=point,
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=8,
            color=colour,
            zorder=6,
            bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": LABEL_EDGE, "lw": 0.6},
        )
        self.points.append(point)

    def frame(self):
        for member in self.members:
            self.axis.plot(
                [member.start[0], member.end[0]],
                [member.start[1], member.end[1]],
                color=FRAME_COLOUR,
                lw=2.2,
                zorder=3,
                solid_capstyle="round",
            )
            self.points += [member.start, member.end]
        self.supports()

    def _joint_state(self):
        """Each joint's global displacement, when every member meeting there gives one."""
        joints: dict[tuple[int, int], dict] = {}
        for member in self.members:
            for end, point in ((0, member.start), (1, member.end)):
                joint = joints.setdefault(
                    _key(point, self.size),
                    {"point": point, "moves": [], "known": True, "forces": [0.0, 0.0]},
                )
                if member.displacements is None:
                    joint["known"] = False
                else:
                    u, v, turn = member.displacements[3 * end: 3 * end + 3]
                    joint["moves"].append(
                        (u * member.ex[0] + v * member.ey[0], u * member.ex[1] + v * member.ey[1], turn)
                    )
                if member.forces is not None:
                    n, shear = member.forces[3 * end], member.forces[3 * end + 1]
                    joint["forces"][0] += n * member.ex[0] + shear * member.ey[0]
                    joint["forces"][1] += n * member.ex[1] + shear * member.ey[1]
                else:
                    joint["known"] = False
        largest = max(
            (abs(value) for joint in joints.values() for move in joint["moves"] for value in move),
            default=0.0,
        )
        for joint in joints.values():
            moves = joint["moves"]
            joint["held"] = bool(moves) and all(
                abs(value) <= _NOISE * largest for move in moves for value in move[:2]
            )
            joint["fixed"] = joint["held"] and all(
                abs(move[2]) <= _NOISE * largest for move in moves
            )
            joint["move"] = moves[0] if moves else None
        return list(joints.values())

    def supports(self):
        width = _SUPPORT_WIDTH * self.size
        for joint in self._joint_state():
            if not (joint["known"] and joint["held"]):
                continue
            x, y = joint["point"]
            lines = [([x - width / 2, x + width / 2], [y, y])]
            if not joint["fixed"]:
                lines.append(([x - width / 3, x, x + width / 3], [y - width / 2, y, y - width / 2]))
                y -= width / 2
                lines.append(([x - width / 2, x + width / 2], [y, y]))
            for index in range(6):
                left = x - width / 2 + index * width / 6
                lines.append(([left, left + width / 6], [y, y - width / 6]))
            for xs, ys in lines:
                (line,) = self.axis.plot(xs, ys, color=FRAME_COLOUR, lw=1.0 if len(xs) == 2 else 1.2)
                line.set_gid("support")
            self.points.append((x, y - width / 5))

    def loads(self):
        arrow = {"arrowstyle": "-|>", "color": LOAD_COLOUR, "lw": 0.9}
        for member in self.members:
            if not member.load:
                continue
            # A load towards -y' is drawn on the +y' side, pointing at the member.
            side = 1.0 if member.load > 0 else -1.0
            normal = (side * member.ey[0], side * member.ey[1])
            count = max(5, round(member.length * self.per_base / self.size * 8) + 1)
            # Clear of the diagram on that side: the hogging moment at a knee runs out
            # past where the arrows would stand, and its value sat on the last arrow.
            near = max(
                _LOAD_NEAR * self.size,
                self.reach.get(id(member), {}).get(side, 0.0) + 0.06 * self.size,
            )
            far = near + (_LOAD_FAR - _LOAD_NEAR) * self.size
            tails = []
            for index in range(count):
                x, y = member.at(member.length * index / (count - 1))
                tip = (x + near * normal[0], y + near * normal[1])
                tail = (x + far * normal[0], y + far * normal[1])
                self.axis.annotate("", xy=tip, xytext=tail, arrowprops=arrow).set_gid("distributed-load")
                tails.append(tail)
            self.axis.plot([tails[0][0], tails[-1][0]], [tails[0][1], tails[-1][1]], color=LOAD_COLOUR, lw=0.9)
            middle = ((tails[0][0] + tails[-1][0]) / 2, (tails[0][1] + tails[-1][1]) / 2)
            written = self.units.written("load", abs(member.load))
            label = f"{_number(written)} {self.units.text('load')}".strip()
            self.axis.annotate(
                label, xy=middle, xytext=(8 * normal[0], 8 * normal[1]), textcoords="offset points",
                ha="center", va="center", fontsize=8, color=LOAD_COLOUR,
            )
            self.points += tails
        self.joint_loads()

    def joint_loads(self):
        joints = [joint for joint in self._joint_state() if joint["known"] and not joint["held"]]
        largest = max(
            (abs(value) for member in self.members if member.forces for value in member.forces),
            default=0.0,
        )
        arrow = {"arrowstyle": "-|>", "color": LOAD_COLOUR, "lw": 1.6}
        length = _JOINT_ARROW * self.size
        for joint in joints:
            x, y = joint["point"]
            for axis, value in enumerate(joint["forces"]):
                if abs(value) <= 1e-6 * largest:
                    continue
                direction = (math.copysign(1.0, value), 0.0) if axis == 0 else (0.0, math.copysign(1.0, value))
                tail = (x - length * direction[0], y - length * direction[1])
                self.axis.annotate("", xy=(x, y), xytext=tail, arrowprops=arrow, zorder=5).set_gid("joint-load")
                written = self.units.written("V", abs(value))
                text = f"{_number(written)} {self.units.text('V')}".strip()
                label = self.axis.annotate(
                    text, xy=tail, xytext=(0, 8), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color=LOAD_COLOUR,
                )
                label.set_gid("joint-load")
                self.points.append(tail)

    # -- the diagrams ------------------------------------------------------------------

    def diagram(self, diagram: str):
        colour = DIAGRAM_COLOUR[diagram]
        values = {
            id(member): [_internal(member, diagram, s) for s in _along(member)]
            for member in self.members
        }
        largest = max(abs(value) for member_values in values.values() for value in member_values)
        scale = _DIAGRAM_PEAK * self.size / largest if largest else 0.0
        # Drawn on the tension side for M; outside when positive for V and N.
        towards = -1.0 if diagram == "M" else 1.0
        shown: set = set()
        for member in self.members:
            local = values[id(member)]
            shown_sign = member.inside if diagram in ("M", "V") else 1.0
            outside = (member.inside * member.ey[0], member.inside * member.ey[1])
            curve = []
            reach = self.reach.setdefault(id(member), {1.0: 0.0, -1.0: 0.0})
            for s, value in zip(_along(member), local):
                x, y = member.at(s)
                offset = towards * shown_sign * value * scale
                curve.append((x + offset * outside[0], y + offset * outside[1]))
                along_ey = offset * member.inside  # the same offset, measured along +y'
                side = 1.0 if along_ey > 0 else -1.0
                reach[side] = max(reach[side], abs(along_ey))
            base = [member.at(s) for s in _along(member)]
            self.axis.fill(
                [p[0] for p in base] + [p[0] for p in reversed(curve)],
                [p[1] for p in base] + [p[1] for p in reversed(curve)],
                color=colour, alpha=0.18, lw=0, zorder=1,
            )
            self.axis.plot([p[0] for p in curve], [p[1] for p in curve], color=colour, lw=1.6, zorder=2)
            self.points += curve
            marks = [(0, base[0]), (len(local) - 1, base[-1])]
            if diagram == "M" and member.load:
                peak = member.forces[1] / member.load
                if 0.02 * member.length < peak < 0.98 * member.length:
                    index = min(range(len(local)), key=lambda i: abs(_along(member)[i] - peak))
                    marks.append((index, None))
            for index, joint in marks:
                value = shown_sign * local[index]
                if diagram == "M" and joint is None:
                    value = shown_sign * _internal(member, "M", member.forces[1] / member.load)
                text = _number(self.units.written(diagram, value), self.units.written(diagram, largest))
                if joint is not None:
                    key = (_key(joint, self.size), text)
                    if key in shown:  # the same value at a joint, from the other member
                        continue
                    shown.add(key)
                self.box(curve[index], text)
        return f"{diagram}{self.units.title(diagram)}"

    def deformed(self):
        colour = DIAGRAM_COLOUR["deformed"]
        shapes = []
        largest = 0.0
        for member in self.members:
            u_i, v_i, t_i, u_j, v_j, t_j = member.displacements
            length = member.length
            shape = []
            for s in _along(member):
                xi = s / length
                v = (
                    (1 - 3 * xi**2 + 2 * xi**3) * v_i
                    + length * (xi - 2 * xi**2 + xi**3) * t_i
                    + (3 * xi**2 - 2 * xi**3) * v_j
                    + length * (-(xi**2) + xi**3) * t_j
                )
                if member.load:
                    v -= member.load * s**2 * (length - s) ** 2 / (24 * member.stiffness)
                u = (1 - xi) * u_i + xi * u_j
                shape.append((s, u, v))
                largest = max(largest, abs(u), abs(v))
            shapes.append((member, shape))
        per_base = self.per_base
        scale = self.result.scale
        if scale is None:
            scale = _nice_scale(_DEFORMED_PEAK * self.size / (largest * per_base)) if largest else 1.0
        for member, shape in shapes:
            curve = []
            for s, u, v in shape:
                x, y = member.at(s)
                dx = u * member.ex[0] + v * member.ey[0]
                dy = u * member.ex[1] + v * member.ey[1]
                curve.append((x + scale * per_base * dx, y + scale * per_base * dy))
            self.axis.plot([p[0] for p in curve], [p[1] for p in curve], color=colour, lw=1.8, zorder=4)
            self.points += curve
            if member.load:
                s, _u, v = max(shape, key=lambda sample: abs(sample[2]))
                index = [sample[0] for sample in shape].index(s)
                text = f"δ = {_number(self.units.written('displacement', v))} {self.units.text('displacement')}"
                self.box(curve[index], text.strip(), offset=(0, -14))
        unit = self.units.text("displacement")
        moves = [joint for joint in self._joint_state() if joint["move"] is not None and not joint["held"]]
        biggest = max((max(abs(j["move"][0]), abs(j["move"][1])) for j in moves), default=0.0)
        for joint in moves:
            x, y = joint["point"]
            dx, dy, _turn = joint["move"]
            moved = (x + scale * per_base * dx, y + scale * per_base * dy)
            lines = [
                f"Δ{name} = {_number(self.units.written('displacement', value))} {unit}".strip()
                for name, value in (("x", dx), ("y", dy))
                if biggest and abs(value) >= 0.1 * biggest
            ]
            for row, text in enumerate(lines):
                self.box(moved, text, offset=(0, 16 + 14 * row))
        return f"Δ{self.units.title('displacement')}   ×{scale:g}"

    def finish(self, title: str):
        axis = self.axis
        axis.set_title(title, fontweight="bold", fontsize=10, pad=10)
        axis.set_aspect("equal")
        axis.axis("off")
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        pad = 0.1 * self.size
        axis.set_xlim(min(xs) - pad, max(xs) + pad)
        axis.set_ylim(min(ys) - pad, max(ys) + pad)
        width = max(xs) - min(xs) + 2 * pad
        height = max(ys) - min(ys) + 2 * pad
        self.figure.set_size_inches(6.4, min(6.4, max(3.0, 6.4 * height / width)))
        self.figure.tight_layout()
        return self.figure


def _nice_scale(raw: float) -> float:
    """The round number at or below `raw`: 1, 2 or 5 times a power of ten."""
    if raw <= 0 or not math.isfinite(raw):
        return 1.0
    power = 10 ** math.floor(math.log10(raw))
    for step in (5, 2, 1):
        if step * power <= raw:
            return float(step * power)
    return float(power)


def render_frame_plot(result: FramePlotResult, convert: Callable[[Any], Any] = lambda q: q):
    """One closed Matplotlib figure: the frame and the diagram `result` asks for.

    `convert` puts a quantity in the unit the sheet's palette declares for it.
    """
    drawing = _Drawing(result, convert)
    drawing.frame()
    if result.diagram == "deformed":
        title = drawing.deformed()
    else:
        title = drawing.diagram(result.diagram)
    # After the diagram, so a load stands clear of it; on the moment and the deformed
    # shape, as in the mock-up he approved.
    if result.diagram in ("M", "deformed"):
        drawing.loads()
    return drawing.finish(title)
