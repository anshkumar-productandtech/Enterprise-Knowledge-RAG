# Enterprise Knowledge Assistant: case study draft

Skeleton for the portfolio page. Sections 5 to 8 describe what is built and are ready to edit. Everything marked [X] needs a number from your own runs: `backend/evals/results/experiments.md` has them once the experiments have run. Label each one real, with the date, models and question count.

## 1. TL;DR

- **Problem:** Employees lose time hunting for policy answers across scattered pages, and a generic chatbot will confidently invent company policy.
- **Built:** A handbook assistant that cites the passage behind every claim, only reads pages the asker's role may open, and declines when the handbook has no answer.
- **Result:** [X]% of 50 test questions handled correctly, up from [X]% for the first version. [X] changes made the difference; [X] made things worse.

## 2. Skills shown

RAG · LLMs · Evaluation design · Product design · APIs · Business analytics

## 3. Problem and user

[Your evidence here: 3 to 5 short interviews, a survey, or public data on time spent searching for internal information. State the source and sample size.]

Primary user: an employee with a policy question ("can I expense this?") who wants an answer they can act on and a link to check it.
Second user: the team that owns the policy, who needs wrong answers to be traceable to a passage.

## 4. Goals and success metrics

| | Metric | Target | Result |
| --- | --- | --- | --- |
| North star | Pass rate on the golden set (correct answer, or correct refusal) | [X]% | [X]% |
| Guardrail | Faithfulness (claims supported by the cited passages) | [X]% | [X]% |
| Guardrail | Restricted pages leaked to the wrong role | 0 | [X] |
| Guardrail | p95 latency | under [X] s | [X] s |
| Guardrail | Cost per question | under $[X] | $[X] |

Set the targets before running the full experiments, and say so.

## 5. Solution and scope

In v1: single-turn questions over [X] handbook pages, numbered citations, six demo roles with different access, refusals, streaming answers, cost and latency shown per answer.

Left out on purpose, and why:

- **Conversation memory.** Follow-ups need query rewriting, which adds a failure mode that would blur the retrieval experiments.
- **Real sign-in.** The role switcher makes access control visible in a demo. Production would read the role from SSO.
- **Feedback buttons.** Useful only with real users to press them.
- **Live re-indexing.** The corpus is a fixed snapshot so results are reproducible.

## 6. Design

Flow: pick a role, ask, watch passages arrive, read the answer with numbered citations, hover a number to see its passage light up in the margin, open the source page.

States designed for:

- **Empty:** three starter questions per role. One of the Employee starters is about a Finance-only page, to invite the access comparison.
- **Searching / writing:** passages appear before the answer does, so the wait shows progress.
- **Answered:** one plain sentence under the answer with role, citations used, time and cost.
- **No answer:** a short refusal that doesn't hint at what other roles can see.
- **Unverified:** an answer with no valid citation gets a warning.
- **Failure:** what went wrong and a retry, with no provider error text shown.

[Add 2 to 3 screenshots.]

## 7. Architecture

See the diagram in the README. Components: markdown loader and cleaner, chunker (sentence or heading-aware), embeddings, Postgres + pgvector with a keyword index, access filter, reciprocal rank fusion, optional reranker, answer model, citation validator, FastAPI stream, Next.js UI.

Models used: answers [X], embeddings [X], reranker [X], judge [X]. Chosen because [X: the cheapest configuration that met the targets, with the comparison].

## 8. AI decisions

- **Access control lives in the SQL query.** Telling a model "don't mention finance documents" is a suggestion, not a control. A restricted chunk is never retrieved, so it can't reach the reranker, the prompt or the logs.
- **Deny by default.** A page that matches no access rule is visible to admins only.
- **Refusal is a first-class outcome.** The model returns a sentinel when the sources don't answer; the server swaps it for a fixed message before anything is shown. Five of the 50 test questions exist only to check this, including a prompt injection.
- **Citations are checked, not trusted.** A citation number that points at no passage is dropped, and an answer left with none is flagged.
- **Fusion by rank, not score.** Vector similarity and keyword rank aren't on the same scale, so results are merged by position.
- **One change per experiment.** Each row of the table differs from its parent in one setting.
- **Golden set validated against the corpus.** The handbook changes daily; a script confirms every reference answer is still on its source page for the snapshot used.
- **Human check on the judge.** [X of 10] hand-graded answers agreed with the judge model.

Prompt iterations: [what you changed between v1 and the final prompt, and the score change each time].

## 9. Results

Paste `experiments.md` here.

All figures real: measured on 50 golden questions on [date], handbook commit [X], models as listed.

What moved the number:

1. [Change]: [X]% to [X]%. Why it helped: [X].
2. [Change]: [X]% to [X]%.
3. [Change]: [X]% to [X]%.
4. [Change]: [X]% to [X]%.

What didn't work: [X]. Still failing: [X of 50], mostly [pattern].

Cost per question: $[X]. Latency: p50 [X] s, p95 [X] s.

## 10. Learnings and next steps

- [The trade-off that surprised you.]
- [Where the judge and you disagreed.]
- Next: conversation memory with query rewriting, feedback capture feeding the golden set, nightly re-index, a larger test set.

Assets: live demo [link], repository [link], 2 to 3 minute walkthrough [link], architecture diagram, experiment table.
