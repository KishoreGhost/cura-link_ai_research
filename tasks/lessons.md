# Lessons

## Active Rules

- Start each non-trivial task by writing a concrete checklist in `tasks/todo.md` before implementation.
- Stop after each implementation step for review when the user explicitly requests stepwise execution.
- Record durable mistakes and the prevention rule here after any correction or failed assumption.
- Do not lock deviations from an explicit brief requirement unless the approval is recorded in the repo with the decision, approver, and date.
- Do not batch an entire phase behind one review gate when stepwise review is required.
- Do not use fabricated persisted-resource responses that contradict the create/read contract.
- Do not let a create-context path succeed without the minimum domain context required for downstream behavior.
- Removing fields from shared types is not enough if the runtime still accepts and drops them silently.
- Follow-up reuse must validate that stored context is actually sufficient for downstream behavior.
- When adding regression tests, include the exact failure modes that were previously fixed, not just adjacent happy paths and validation errors.
- When moving work earlier in a phased plan, remove or reword the old later-phase item so ownership is not duplicated.
- When a planning decision is resolved, record it in the repo decision log, not only in a free-form strategy doc.
- When the user asks to reiterate the intended product approach from the brief, do not replace that with a current-state scaffold audit unless they explicitly ask for an implementation review.
