# Finding prioritization rubric

Do not collapse categories into an overall grade.

## Priority

| Priority | Use |
|---|---|
| P0 | Security boundary failure, broken primary action, legal/data-risk mismatch, false consequential claim or measurement corruption. |
| P1 | Strong evidence of high user/business impact or a major search/accessibility barrier. |
| P2 | Credible improvement with moderate impact or incomplete behavioral evidence. |
| Experiment | Hypothesis requiring measurement before broad rollout. |
| Monitor | Low-risk observation or volatile platform behavior. |

## Decision fields

For each action record:

- affected users or queries;
- evidence status, source and confidence;
- consequence if unchanged;
- effort and dependencies;
- reversibility and rollback;
- owner;
- verification method;
- whether the recommendation is a defect fix or experiment.

Do not create fake mathematical precision by assigning arbitrary points to unrelated categories.
