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
    load_end: float = 0.0  # the load at end; equal to `load` when it is uniform
    points: tuple = ()  # (P, a) in base units, P towards -y' at a from start

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
            if member.load_end is not None:
                candidates.setdefault("load", []).append(member.load_end)
            for force, _where in member.points:
                candidates.setdefault("point", []).append(force)
            candidates.setdefault("length", []).extend((*member.start, *member.end))
        for kind, quantities in candidates.items():
            quantities = [q for q in quantities if hasattr(q, "to_base_units") and q.magnitude != 0]
            if quantities:
                self.references[kind] = max(quantities, key=lambda q: abs(_base(q)))

    # What the sheet typed - a load, a point load, a coordinate - keeps the unit it was
    # typed in, as a `:=` value does on the page; what was worked out takes the family's.
    _TYPED = frozenset({"load", "point", "length"})

    def _converted(self, kind: str, reference):
        if kind in self._TYPED:
            try:
                return self.convert(reference, declared=True)
            except TypeError:  # a `convert` that knows nothing of typed values
                return self.convert(reference)
        return self.convert(reference)

    def unit(self, kind: str):
        reference = self.references.get(kind)
        return None if reference is None else self._converted(kind, reference).units

    def written(self, kind: str, value: float) -> float:
        """A base-unit value in the unit its kind is written in."""
        reference = self.references.get(kind)
        if reference is None:
            return value
        base = reference.to_base_units()
        quantity = base._REGISTRY.Quantity(value, base.units)
        return float(quantity.to(self._converted(kind, reference).units).magnitude)

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
                load_end=(
                    _base(member.load_end)
                    if member.load_end is not None
                    else (_base(member.load) if member.load is not None else 0.0)
                ),
                points=tuple(
                    (_base(force), 0.0 if where.dimensionless else _base(where))
                    for force, where in member.points
                ),
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
    """Where a member is drawn: evenly, and on both sides of each point load's jump."""
    samples = [member.length * index / (_SAMPLES - 1) for index in range(_SAMPLES)]
    step = 1e-9 * member.length
    for _force, where in member.points:
        samples += [max(0.0, where - step), min(member.length, where + step)]
    return sorted(samples)


def _loaded(member: _Member) -> bool:
    return bool(member.load or member.load_end or member.points)


def _internal(member: _Member, diagram: str, s: float) -> float:
    """N, V or M at `s`, in local axes: tension, +y' on the left face, sagging (-y') fibre.

    The load runs linearly from `load` at start to `load_end` at end, and each point load
    acts past its own position.
    """
    f, q, rise, length = member.forces, member.load, member.load_end - member.load, member.length
    if diagram == "N":
        return -f[0]
    if diagram == "V":
        return f[1] - q * s - rise * s * s / (2 * length) - sum(
            force for force, where in member.points if s > where
        )
    return (
        -f[2] + f[1] * s - q * s * s / 2 - rise * s**3 / (6 * length)
        - sum(force * (s - where) for force, where in member.points if s > where)
    )


def _held_deflection(member: _Member, s: float) -> float:
    """The deflection of the member under its own loads, both ends held fixed.

    Added to the curve its end displacements give. A particular solution of
    EI v^(4) = -q(s) that starts flat at s = 0, plus c2 s^2 + c3 s^3 so it ends flat at
    s = L; for a uniform load this is -q s^2 (L - s)^2 / (24 EI).
    """
    q, rise, length, stiffness = member.load, member.load_end - member.load, member.length, member.stiffness

    def shape(x):
        return -(
            q * x**4 / 24 + rise * x**5 / (120 * length)
            + sum(force * max(x - where, 0.0) ** 3 / 6 for force, where in member.points)
        ) / stiffness

    def slope(x):
        return -(
            q * x**3 / 6 + rise * x**4 / (24 * length)
            + sum(force * max(x - where, 0.0) ** 2 / 2 for force, where in member.points)
        ) / stiffness

    right, turn = -shape(length), -slope(length)
    determinant = length**4
    c2 = (right * 3 * length**2 - length**3 * turn) / determinant
    c3 = (length**2 * turn - 2 * length * right) / determinant
    return shape(s) + c2 * s**2 + c3 * s**3


def _shear_zeros(member: _Member) -> list[float]:
    """Where the shear crosses zero inside the member: the moment's own extremes.

    Not across a point load's jump, where the extreme is the load's position and is
    labelled there. Refined by bisection, so a peak is the peak and not a sample near it.
    """
    samples = _along(member)
    values = [_internal(member, "V", s) for s in samples]
    scale = max((abs(value) for value in values), default=0.0)
    found = []
    # A zero that falls on a sample - the middle of a uniformly loaded span - is the zero.
    for before, (s, value), after in zip(values, zip(samples[1:], values[1:]), values[2:]):
        if abs(value) <= _NOISE * scale and before * after < 0:
            found.append(s)
    for (left, low), (right, high) in zip(zip(samples, values), zip(samples[1:], values[1:])):
        if abs(low) <= _NOISE * scale or abs(high) <= _NOISE * scale or (low > 0) == (high > 0):
            continue
        if any(left <= where <= right for _force, where in member.points):
            continue
        for _ in range(60):
            middle = (left + right) / 2
            if (_internal(member, "V", middle) > 0) == (low > 0):
                left = middle
            else:
                right = middle
        found.append((left + right) / 2)
    return [s for s in found if 0.02 * member.length < s < 0.98 * member.length]


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
                    {"point": point, "moves": [], "known": True, "forces": [0.0, 0.0], "moment": 0.0},
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
                    joint["moment"] += member.forces[3 * end + 2]
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
            # Which way the structure leaves the support. A fixed end of one member is a
            # wall across that member - a cantilever's is upright - and anything else
            # stands on the ground, as a column's base does.
            into = (0.0, 1.0)
            meeting = [
                member for member in self.members
                if _key(member.start, self.size) == _key(joint["point"], self.size)
                or _key(member.end, self.size) == _key(joint["point"], self.size)
            ]
            if joint["fixed"] and len(meeting) == 1:
                member = meeting[0]
                sign = 1.0 if _key(member.start, self.size) == _key(joint["point"], self.size) else -1.0
                into = (sign * member.ex[0], sign * member.ex[1])
            across = (into[1], -into[0])

            def at(a, b, x=x, y=y, across=across, into=into):
                """A point `a` along the support and `b` away from the structure."""
                return (x + a * across[0] - b * into[0], y + a * across[1] - b * into[1])

            segments = [[(-width / 2, 0.0), (width / 2, 0.0)]]
            base = 0.0
            if not joint["fixed"]:
                segments.append([(-width / 3, width / 2), (0.0, 0.0), (width / 3, width / 2)])
                base = width / 2
                segments.append([(-width / 2, base), (width / 2, base)])
            for index in range(6):
                left = -width / 2 + index * width / 6
                segments.append([(left, base), (left + width / 6, base + width / 6)])
            for segment in segments:
                points = [at(a, b) for a, b in segment]
                (line,) = self.axis.plot(
                    [point[0] for point in points], [point[1] for point in points],
                    color=FRAME_COLOUR, lw=1.0 if len(points) == 2 else 1.2,
                )
                line.set_gid("support")
            self.points.append(at(0.0, base + width / 5))

    def loads(self):
        arrow = {"arrowstyle": "-|>", "color": LOAD_COLOUR, "lw": 0.9}
        for member in self.members:
            for force, where in member.points:
                self._point_load(member, force, where)
            if member.load_end != member.load:
                self._linear_load(member, arrow)
                continue
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

    def _clear_of_the_diagram(self, member, side: float) -> float:
        """How far out a load stands so that it stays off the diagram on its side."""
        return max(
            _LOAD_NEAR * self.size,
            self.reach.get(id(member), {}).get(side, 0.0) + 0.06 * self.size,
        )

    def _linear_load(self, member, arrow):
        """`load=[w_1, w_2]`: arrows growing from w_1 to w_2, an arrow at each end."""
        start, finish = member.load, member.load_end
        largest = max(abs(start), abs(finish))
        side = 1.0 if (start + finish) > 0 else -1.0
        normal = (side * member.ey[0], side * member.ey[1])
        count = max(5, round(member.length * self.per_base / self.size * 8) + 1)
        near = self._clear_of_the_diagram(member, side)
        reach = (_LOAD_FAR - _LOAD_NEAR) * self.size
        tails = []
        for index in range(count):
            s = member.length * index / (count - 1)
            q = start + (finish - start) * s / member.length
            x, y = member.at(s)
            tip = (x + near * normal[0], y + near * normal[1])
            far = near + reach * abs(q) / largest
            tail = (x + far * normal[0], y + far * normal[1])
            if abs(q) > 1e-9 * largest:
                self.axis.annotate("", xy=tip, xytext=tail, arrowprops=arrow).set_gid("distributed-load")
            tails.append(tail)
        self.axis.plot([p[0] for p in tails], [p[1] for p in tails], color=LOAD_COLOUR, lw=0.9)
        for value, tail, along in ((start, tails[0], -1.0), (finish, tails[-1], 1.0)):
            if abs(value) <= 1e-9 * largest:
                continue
            written = self.units.written("load", abs(value))
            self.axis.annotate(
                f"{_number(written)} {self.units.text('load')}".strip(),
                xy=tail, xytext=(8 * normal[0] + 6 * along * member.ex[0], 8 * normal[1] + 6 * along * member.ex[1]),
                textcoords="offset points", ha="center", va="center", fontsize=8, color=LOAD_COLOUR,
            )
        self.points += tails

    def _point_load(self, member, force, where):
        """`point=[P, a]`: an arrow onto the member at a, with P beside it."""
        side = 1.0 if force > 0 else -1.0
        normal = (side * member.ey[0], side * member.ey[1])
        gap = self.reach.get(id(member), {}).get(side, 0.0)
        gap = gap + 0.02 * self.size if gap else 0.0
        x, y = member.at(where)
        tip = (x + gap * normal[0], y + gap * normal[1])
        length = _JOINT_ARROW * self.size
        tail = (tip[0] + length * normal[0], tip[1] + length * normal[1])
        self.axis.annotate(
            "", xy=tip, xytext=tail, zorder=5,
            arrowprops={"arrowstyle": "-|>", "color": LOAD_COLOUR, "lw": 1.6},
        ).set_gid("point-load")
        written = self.units.written("point", abs(force))
        label = self.axis.annotate(
            f"{_number(written)} {self.units.text('point')}".strip(),
            xy=tail, xytext=(8 * normal[0], 8 * normal[1]), textcoords="offset points",
            ha="center", va="center", fontsize=8, color=LOAD_COLOUR,
        )
        label.set_gid("point-load")
        self.points.append(tail)

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
            self._joint_moment(joint)

    def _joint_moment(self, joint):
        """A moment applied at a joint: the end moments meeting there add up to it.

        Drawn as a red arc beside the joint, anticlockwise when positive, with its size.
        """
        from matplotlib.patches import FancyArrowPatch

        moments = [
            abs(member.forces[index])
            for member in self.members
            if member.forces
            for index in (2, 5)
        ]
        value = joint["moment"]
        if not moments or abs(value) <= 1e-6 * max(moments):
            return
        x, y = joint["point"]
        radius = 0.07 * self.size
        low, high = math.radians(-60), math.radians(60)
        start = (x + radius * math.cos(low), y + radius * math.sin(low))
        end = (x + radius * math.cos(high), y + radius * math.sin(high))
        if value < 0:
            start, end = end, start
        self.axis.add_patch(
            FancyArrowPatch(
                start, end, connectionstyle=f"arc3,rad={0.55 if value > 0 else -0.55}",
                arrowstyle="-|>", mutation_scale=10, color=LOAD_COLOUR, lw=1.4, zorder=5,
            )
        )
        written = self.units.written("M", abs(value))
        label = self.axis.annotate(
            f"{_number(written)} {self.units.text('M')}".strip(),
            xy=(x + 1.35 * radius, y), xytext=(4, 0), textcoords="offset points",
            ha="left", va="center", fontsize=8, color=LOAD_COLOUR,
        )
        label.set_gid("joint-moment")
        self.points.append((x + 2.6 * radius, y))

    # -- the diagrams ------------------------------------------------------------------

    def diagram(self, diagram: str):
        colour = DIAGRAM_COLOUR[diagram]
        values = {
            id(member): [_internal(member, diagram, s) for s in _along(member)]
            for member in self.members
        }
        largest = max(abs(value) for member_values in values.values() for value in member_values)
        if diagram not in self.units.references and largest:
            # Every end value is zero - a simply supported beam's end moments: the unit is
            # the one the page would write the largest value in.
            length_reference = self.units.references["length"]
            self.units.references[diagram] = length_reference._REGISTRY.Quantity(
                largest, "N*m" if diagram == "M" else "N"
            )
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
            for index, joint in marks:
                value = shown_sign * local[index]
                text = _number(self.units.written(diagram, value), self.units.written(diagram, largest))
                key = (_key(joint, self.size), text)
                if key in shown:  # the same value at a joint, from the other member
                    continue
                shown.add(key)
                self.box(curve[index], text)
            # Inside the member: the moment's extremes where the shear crosses zero, and
            # at each point load the moment under it and the shear on either side.
            inner = []
            if diagram == "M":
                inner += [(s, 0.0) for s in _shear_zeros(member)]
                inner += [(where, 0.0) for _force, where in member.points]
            elif diagram == "V":
                step = 1e-9 * member.length
                inner += [(where - step, -10.0) for _force, where in member.points if where > 0]
                inner += [(where + step, 10.0) for _force, where in member.points if where < member.length]
            for s, shift in inner:
                value = _internal(member, diagram, s)
                x, y = member.at(s)
                offset = towards * shown_sign * value * scale
                point = (x + offset * outside[0], y + offset * outside[1])
                text = _number(
                    self.units.written(diagram, shown_sign * value), self.units.written(diagram, largest)
                )
                self.box(point, text, offset=(shift * member.ex[0] * 2.2, shift * member.ex[1] * 2.2))
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
                if _loaded(member):
                    v += _held_deflection(member, s)
                u = (1 - xi) * u_i + xi * u_j
                shape.append((s, u, v))
                largest = max(largest, abs(u), abs(v))
            shapes.append((member, shape))
        if "displacement" not in self.units.references and largest:
            # Every end held still, as in a fixed beam: the unit is the deflection's own.
            length_reference = self.units.references["length"]
            self.units.references["displacement"] = length_reference._REGISTRY.Quantity(
                largest, "m"
            ).to(length_reference.to_base_units().units)
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
            if _loaded(member):
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
