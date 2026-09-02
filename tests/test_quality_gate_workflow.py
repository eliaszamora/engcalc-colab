"""The Deep Gate qualification must not depend on anyone remembering to run it.

`docs/quality-gate.md` says every release candidate is qualified on its exact SHA. That
rule was written down, broken across four releases, recorded as a lapse in
`CURRENT.md` — and then broken across six more. Twice, by the same person, with the
second failure happening after the first had been documented.

A rule that depends on someone dispatching a workflow by hand is not a rule. It is now a
push trigger, and this pins it: the PR loop is untouched, because qualification fires
after the merge rather than before it.
"""

from __future__ import annotations

import pathlib

import yaml


WORKFLOW = pathlib.Path(__file__).resolve().parents[1] / ".github/workflows/quality-gate-deep.yml"


def _workflow() -> dict:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads a bare `on:` key as the boolean True, which is the YAML 1.1 rule.
    triggers = document.get("on", document.get(True))
    return {"triggers": triggers, "jobs": document["jobs"]}


def test_qualification_runs_on_every_push_to_main():
    workflow = _workflow()

    push = workflow["triggers"].get("push")
    assert push is not None, "qualification must not depend on a manual dispatch"
    assert push["branches"] == ["main"]

    condition = workflow["jobs"]["qualification"]["if"]
    assert "github.event_name == 'push'" in condition, condition


def test_exploration_does_not_run_on_a_push():
    """The weekly search stays weekly; only qualification follows main.

    On a push `inputs.mode` is null, so the exploration condition is false. Asserted
    rather than assumed, because a second job firing on every merge would quietly
    multiply the cost of this change by two.
    """
    condition = _workflow()["jobs"]["exploration"]["if"]
    assert "github.event_name == 'push'" not in condition, condition
    assert "schedule" in condition


def test_the_manual_dispatch_still_exists():
    """Qualifying a release candidate before merging it stays possible."""
    workflow = _workflow()
    dispatch = workflow["triggers"]["workflow_dispatch"]
    assert "qualification" in dispatch["inputs"]["mode"]["options"]
