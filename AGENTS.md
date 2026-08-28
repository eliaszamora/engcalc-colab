# EngCalc Agent Instructions

## Continuity protocol — mandatory

EngCalc is developed across long ChatGPT/Codex sessions that may hit conversation limits. The repository is the persistent source of project context.

### At the start of every EngCalc work session

1. Read `docs/project-context/CURRENT.md` before planning, editing code, or answering a continuation request.
2. Verify any branch/PR/SHA/test-count claims in that file against GitHub when they affect the requested work.
3. Read the referenced approved spec/plan for the active release before implementation.

### Before the final response of every turn that changes project state

Update `docs/project-context/CURRENT.md` in the same working branch when any of these changed:

- active branch, PR, version, commit or release status;
- approved design/API decision;
- implemented feature or corrected bug;
- test/release-gate evidence;
- known regression, unresolved issue or user-reported visual problem;
- next implementation step or validation instructions.

Do not create a commit merely for greetings or explanations that do not change project state. For state-changing work, the context update is part of the definition of done.

### What CURRENT.md must contain

Keep it compact and replace stale state rather than appending a transcript. Always preserve these sections:

- `Current baseline`
- `Approved behavior`
- `Open issues / user feedback`
- `Validation evidence`
- `Roadmap / active plan`
- `Exact next step`
- `How to resume in a new conversation`

Git history is the audit trail for older context snapshots; do not duplicate the whole history inside the file.

### Safety and repository hygiene

- Never store passwords, tokens, credentials, personal secrets or unrelated user data in project context.
- Do not claim a release is validated unless the recorded tests actually ran on that tree.
- Temporary CI workflows used for validation must be removed before release closure unless intentionally retained.
- Preserve existing EngCalc public behavior unless the active approved spec explicitly changes it.

## Engineering workflow

- Use RED → GREEN TDD for code changes.
- Run focused tests first, then the complete source suite.
- Release branches close with a real wheel build, clean-environment smoke outside the repository, full suite against the installed wheel, repeated source suite and cleanup of temporary validation workflows.
- Keep positive structural moment plotted downward unless an approved design changes the convention.
