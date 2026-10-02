# Update and resume an SDD change

Local adaptation of OpenSpec v1.13.2 update-change. Invoked through
`/sdd-propose <project> <ticket> --update`; changes planning artifacts, not code.

1. Read the current artifacts, status, PR state if present, code/tests, and user
   request. Never infer the plan from presence of one specs file. If the PR is
   merged or status archived, behavior changes need a new change. Correcting a
   historical typo is narrowly scoped and does not reset delivery history.
2. Before changing an active plan, stop/join all workers for this change and
   preserve their work. If another session owns live workers, report that blocker;
   do not race it or disarm its gates. No content update until writers are quiescent.
3. Work out requested edits and consistency effects in every direction. An edit
   to tasks/design may require revising proposal/specs. Act within existing user
   authorization; ask only for expanded scope or missing decisions. Capture alone
   never starts apply. A missing companion spec under a populated specs directory
   belongs here; do not send it to an unreachable "first missing artifact" step.
4. Classify the change using the table below. For semantic changes, invalidate
   approval/status FIRST, then edit artifacts; an interrupted update must leave
   the change unapproved, never approved against partly edited requirements.
   Refresh owned active markers with design_approved=false. The gate also reads
   the current proposal, so stale marker approval cannot reopen it.
5. Preserve unrelated completed tasks; reopen affected tasks and add any newly
   required work. Scope/design changes require human reapproval. Do not reset all
   checkmarks or silently retain affected completed items. Keep old review.md as
   historical evidence until it is replaced; its fingerprint must not be refreshed
   without re-review. Persist PR identity even when status moves backward.
6. Run draft validation while editing, ready validation when the plan is complete.
   Report changed artifacts, pending decisions, approval/status, and the next
   skill. If incomplete, remain in planning; do not continue implementation here.

| Event | Transition / next phase |
| --- | --- |
| Typo/format/link only | Keep approval. Only from reviewing/verified/delivered, with unchanged code and still-valid CI evidence on an unmerged PR, set status=reviewing when the review fingerprint changes. Preserve proposed/approved/applying/verifying even if a historical review exists; never promote unfinished work. Changed code requires verifying instead. Explain why no behavior changed. |
| Requirement, acceptance, design choice, scope, or applicability changed | Set design_approved=false and status=proposed. After human sign-off, apply resumes. |
| Code bug against unchanged plan | Owning phase records status=applying and reopens the affected task (or adds a same-scope repair task). Keep approval; apply → verify → review. |
| Missing test/evidence against unchanged plan | status=verifying; keep approval. Verify → review. If tests reveal a bug, return to applying. |
| Required review evidence missing | Do not mark verified. Keep reviewing while inspecting existing evidence; route to verifying if additional execution/tests are needed. |
| Plan intent fundamentally changes or PR already merged | New change; preserve old history. |

Re-entry must reuse sdd/<ticket> and its worktree, preserving dirty/in-progress
work; never blindly recreate, reset, force-remove, or merge it into main. Detect
actual group branches/merge state before scheduling pending work. A dependent group
starts from the integrated prerequisite results. A previous green checkmark alone
is not evidence that its code was integrated.

For an existing open PR, apply/verify/review repeat on the same feature branch.
Delivery updates that PR's body and head after freshness checks, then returns to
status=delivered. Do not force-push or change the PR's ready/draft state as a side
effect. If it was merged while rework was underway, stop and create follow-up
work instead of rewriting merged history.
