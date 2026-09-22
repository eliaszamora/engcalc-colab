"""The whole suite runs once a week, whether or not anybody pushed.

On 2026-09-10 Pint 0.26 changed the character it puts between two unit factors, on every
page, with nobody touching this repository: ten contracts went red on a commit that had
been green an hour before. They went red because somebody happened to push. The engineer
installs with `--upgrade`, so a dependency release reaches his notebook the next time he
opens it - and until now it reached this suite only the next time somebody pushed.

The Deep Gate has had a weekly schedule for a long time, and it does not carry the
reference pages, which are exactly what a spelling change moves. So `ci.yml` - the six
jobs, the pages among them - runs on a schedule too, and can be started by hand from the
Actions tab when there is a reason not to wait for Monday.
"""

from __future__ import annotations

import pathlib

import yaml

WORKFLOW = pathlib.Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"


def _ci() -> tuple[dict, dict]:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads a bare `on:` key as the boolean True, which is the YAML 1.1 rule.
    triggers = document.get("on", document.get(True))
    return triggers, document["jobs"]


def test_the_suite_runs_on_a_weekly_schedule():
    triggers, _ = _ci()
    schedule = triggers.get("schedule")
    assert schedule, "without a schedule a dependency release waits for the next push"
    minute, hour, day_of_month, month, day_of_week = schedule[0]["cron"].split()
    assert (day_of_month, month) == ("*", "*"), schedule
    assert day_of_week != "*", "weekly, as approved - not every day"


def test_a_scheduled_run_runs_every_job():
    """A job that skipped the schedule would make the weekly run green by not running."""
    _, jobs = _ci()
    assert set(jobs) == {"test", "colab-ipython"}, set(jobs)
    for name, job in jobs.items():
        assert "if" not in job, (name, job.get("if"))


def test_the_suite_can_be_started_by_hand():
    triggers, _ = _ci()
    assert "workflow_dispatch" in triggers, triggers


def test_pull_requests_and_pushes_to_main_still_run_it():
    triggers, _ = _ci()
    assert "pull_request" in triggers, triggers
    assert triggers["push"]["branches"] == ["main"], triggers
