# Canonical specs — opt-in post-merge synchronization

Local vault adaptation of OpenSpec v1.13.2 (`db230978`),
`workflows/sync-specs.ts`. No CLI or Stores migration. This is a skill procedure,
not a claim of atomic filesystem transactions or a general Markdown merge engine.

## Project opt-in and scope

Enable only at the user's explicit project setup request by creating
`01 Work/projects/<PROJECT>/specs/README.md` with frontmatter:

```yaml
type: spec-index
sdd_spec_sync: true
```

The body explains that `<capability>.md` describes merged target-branch behavior,
not production deployment; include the repo/base mapping for multi-repo projects.
A missing opt-in preserves legacy finalize behavior. A malformed/conflicting
opt-in is an error, not silent legacy fallback. This skill upgrade alone enables
no real project and rewrites no old ticket.

Canonical path: `<PROJECT>/specs/<capability>.md`; ticket delta remains
`<PROJECT>/SDD/<ticket>-<slug>/specs/<capability>.md`. Preserve existing capability
paths and vault No-H1 convention. Do not treat historical/in-flight deltas as a
canonical baseline or concatenate them to reconstruct an entire project.

## Capture baseline during proposal

For each touched existing capability, read its current canonical spec and preserve
an exact snapshot in the ticket's optional `baseline/<capability>.md`, with a
`baseline/source.md` recording source path, source commit or content hash, repo and
base branch. Record explicitly when a new capability had no baseline. These files
are evidence owned by propose, not independent requirements and not edited by apply.

If the existing capability has no canonical spec, establish one only within the
approved setup/proposal scope from pre-change code/tests and confirmed merged
history. Identify uncertain behavior and ask only for the missing decisions. Do
not invent a baseline for MODIFIED/RENAMED. Old in-flight tickets missing baselines
need an explicit baseline recovery from their pre-change revision; failure blocks
sync, not a fabricated snapshot of the new behavior. Baseline files are frozen
for this revision; if --update changes targeted capabilities, capture the additional
baselines and reconcile all affected artifacts before renewed approval.

## Finalize sequence

1. Confirm the persisted PR is MERGED in the intended repo/base. Read merged
   commit/tree, current canonical files and delta. Check the merged result still
   implements the reviewed contract; remote PR edits after local review require
   evidence reconciliation, not blind sync. Squash merges can legitimately have a
   different SHA; compare content/behavior, not SHA equality alone.
2. If skip_specs=true, record spec_sync=not-applicable. If project not enabled,
   record spec_sync=legacy. Both paths continue existing Git cleanup.
3. For an enabled project, serialize canonical writes per project: acquire a
   machine-local lock directory under `~/.claude/` keyed by the canonical project
   path hash (atomic mkdir). Never steal an existing lock; check for a live owner
   and report an abandoned lock for recovery. Keep credentials/runtime locks out
   of the vault. Release only the lock this run acquired, including on failure.
4. Under the lock, reread current canonical files. Compare baseline/current/desired
   for each operation below. Prepare the complete result before writing. Preserve
   requirements and sections outside the delta. Show conflicting requirement names
   and evidence; stop rather than overwrite. Recheck file hashes immediately before
   replacement; non-cooperating/manual edits must also cause reconciliation.
5. Validate the resulting behavior contract, nonempty scenarios where required,
   and retained unrelated content. Write each file through a temporary sibling and
   replacement; remove your temporary files. Record source ticket, PR URL and merge
   commit in the canonical spec's frontmatter. Re-read to confirm the expected
   content. This is per-file atomic, not a cross-file transaction.
6. Only once every capability is confirmed, set proposal spec_sync=synced. Release
   the lock, then perform Git cleanup and finally status=archived. On conflict,
   unreadable baseline, or partial write keep delivered and preserve the marker /
   worktree so finalize can retry. Do not set archived on partial sync.

## Operation and retry rules

| Operation | Safe result |
| --- | --- |
| ADDED | Add when absent; identical desired requirement is already synced; a different existing requirement is a conflict. |
| MODIFIED | Replace the full baseline requirement only if current still matches baseline; identical desired content is already synced; other divergence is a conflict. |
| REMOVED | Remove if current matches baseline; already absent is a no-op; changed current behavior requires reconciliation. |
| RENAMED | If FROM exists, require it to equal the frozen baseline before moving/deleting it, including rename+MODIFIED; otherwise conflict. Move to an absent TO using preserved behavior or accompanying MODIFIED result. FROM absent is a no-op only when TO equals desired; missing both or a divergent/colliding TO is a conflict. |

Do not erase a capability's entire file merely because its last requirement was
removed: retain Purpose and an explicit retired note unless capability retirement
was separately included in the approved change. New canonical specs inherit the
reviewed Purpose. Never replace a whole current file with a ticket's delta.

A rerun must compare content even if spec_sync says synced; provenance alone is not
proof. For a partially completed multi-file sync, recognize already-applied desired
content and process only remaining changes. Preserve the original baseline snapshots
so a partial write cannot masquerade as a fresh baseline. Do not replay an archived
old ticket over newer specs: archived finalize is read-only completion reporting.

Spec sync is part of authorized finalize for opted-in projects. It is separate
from the optional human-approved learning write-back into keypoint/Self/wiki.
