# Walkthrough narration (about 2.5 minutes)

A script for recording the walkthrough in your own voice over the live demo,
for example with Loom. Each block is one shot. Read the words at a relaxed pace;
the timings assume about 150 words a minute. Every number here comes from the
result files in `backend/evals/results/` (11 and 12 November 2026).

---

**Shot 1: the empty app, Employee selected (0:00 to 0:15)**

> Employees waste time hunting for policy answers, and a generic chatbot will
> confidently invent company policy. I built a handbook assistant that cites the
> passage behind every claim, only reads what your role is allowed to see, and
> says "I don't know" when the handbook doesn't answer.

**Shot 2: ask "What is the most I can spend on a hotel per night on a work trip?" (0:15 to 0:40)**

> It runs on the public GitLab handbook, 733 pages. Watch the passages arrive
> first, then the answer. Every claim carries a number. Hover it, and the passage
> it came from lights up. Under the answer: which role asked, how many passages
> it used, how long it took, and what it cost. Here, a fraction of a cent.

**Shot 3: as Employee, ask "How many vendor bids do I need for a new $150K purchase?" (0:40 to 1:00)**

> The answer to this one lives on a Finance-only page. As an employee, I get a
> refusal. And notice what it doesn't say: it never says "you lack access",
> because that would reveal the answer exists. The Finance pages were filtered
> out inside the database query, before any search ran.

**Shot 4: switch to Finance analyst, ask the same question (1:00 to 1:15)**

> Same question as a finance analyst, and now the Finance passage is found and
> cited. Across 23 restricted test questions, the wrong role got a restricted
> page zero times.

**Shot 5: as Employee, ask "What is the Wi-Fi password for the Amsterdam office?" (1:15 to 1:25)**

> A question the handbook can't answer. No passage supports one, so it declines
> instead of making something up.

**Shot 6: the results table in the README (1:25 to 2:15)**

> I measured all of this on 50 test questions with known answers, five of them
> designed to be refused, including a prompt injection. All five were refused,
> in every configuration.
>
> I ran six experiments, one change at a time. Hybrid search, meaning keyword
> search alongside meaning-based search, found the right page for 42 of 45
> questions, up from 39. But then the surprise: it also refused more answerable
> questions, 11 instead of 8. Small chunks found the right page without the
> sentence holding the number. Adding a reranker fixed most of that: 7 wrong
> refusals, and the best pass rate. So that's what I serve, even though it's
> about a second slower.

**Shot 7: back to the app, or the repository page (2:15 to 2:35)**

> The lesson: a better retrieval score didn't mean better answers, and I'd have
> shipped the wrong setup if I'd stopped measuring early. The code, the test
> set and every result file are in the repository.

---

## Before you record

- Ask each question once before recording, so a sleeping free-tier server is awake.
- Record at 1280 × 720 or larger, browser zoom 100%, and close other tabs.
- If an answer differs from the script, say what you see on screen, not the script. The model's wording varies between runs.
