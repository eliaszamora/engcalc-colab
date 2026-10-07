# `eigenvals(K, G)` audit harness (for 0.46.2)

Cases and mpmath references built by seven independent audits of the rewrite of
`eigenvals(K, G)` with a singular `G` (2026-10-06/07). Each audit found a silently wrong
eigenvalue in the method of the moment - mostly supports or links written as 1e16-1e20
springs - and the method in `src/engcalc_colab/matrix_numeric.py` on this branch was reworked
each time. They were written in a session scratchpad and copied here so the work can go on.

**The scripts carry the scratchpad's absolute paths and an `ENGROOT` env var.** Before
running, set `ENGROOT` to the repository (e.g. `C:/Users/elias/engcalc`), and fix any path
that points into `AppData/Local/Temp/claude/...` to point here instead.

| folder | what | how it was run |
|---|---|---|
| `a3/` | first audits: page cases (`cases*.json`) and refs (`refs*.json`), the penalty column | `penalty_check.py` |
| `a4/` | `cases1-5.py` with mpmath refs `r1-5.json` and main's results `m1-5.json` | `a4/all.sh` (h4.py + cmp.py) |
| `a5/` | `cases6-7.py` + `.refs.json`; `lib.py` (needs `ENGROOT`), `run.py`, `cmp2.py` | `master.py` |
| `a6/` | `cases8.py` + refs; `lib6.py` (`judge2`), `run6.py` | `master.py` |
| `a7/` | `cases9-13.py`, `beams.py` + refs: springs on half the DOFs, clusters | `master.py` |
| `a8/` | `casesA/B.py` + `refs8`: rigid links (EA 1e13-1e17), frames to 75 DOFs; `p3.py` portal sweep | `run8.py`, `p3.py` |

`battery.sh` runs everything; `corpus.py` compares his 270 book sheets main vs branch (needs
two source trees, see its top). Judgement used: a value is wrong if off by more than
max(1e-5, 100 × its sensitivity to 1e-15 perturbations of the float entries); eigenvalues
that exist only because G is singular to round-off (±1e16) are deliberately not reported.

State at `f2f969c` (last full battery before the pause): 0 wrong in ~900 cases; refusals
where main was right: `A_tie_1e10-14` (two DOFs tied by a stiff spring), `F18_free_fullmass`,
`L_two_rigid_12`, `B_*_1e-9/-11`. His problems 10.8 and 10.9 (`eigenvals(-K_g, K)`) give main's
pages. See `docs/project-context/CURRENT.md` on main for the design and the audit history.
