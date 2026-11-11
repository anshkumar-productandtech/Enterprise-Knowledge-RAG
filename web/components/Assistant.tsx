"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { readEvents } from "@/lib/sse";
import type { Exchange, Outcome, Role, Source } from "@/lib/types";
import { AnswerText } from "./AnswerText";

const MAX_CHARS = 500;

const FALLBACK_ROLE: Role = { name: "employee", label: "Employee", description: "Company-wide policies only" };

// Starter questions. The last one for Employee is about a Finance-only page on
// purpose: it shows what a role without access gets back.
const STARTERS: Record<string, string[]> = {
  employee: [
    "What is the nightly hotel limit on a work trip?",
    "How many paid sick days do I get?",
    "How many vendor bids do I need for a $150K purchase?",
  ],
  engineer: [
    "How do I declare a production incident?",
    "Does an S3 incident have to be mitigated at the weekend?",
    "How is personal data classified?",
  ],
  finance_analyst: [
    "How many vendor bids do I need for a $150K purchase?",
    "When is a purchase order required?",
    "How long does legal review of a purchase request take?",
  ],
  sales_rep: [
    "What quote types can I create for a deal?",
    "How far ahead can a quote start date be?",
    "What is the daily meal allowance when travelling?",
  ],
};

const GROUP_LABEL: Record<string, string> = { general: "All employees" };
const groupLabel = (group: string) =>
  GROUP_LABEL[group] ?? `${group.charAt(0).toUpperCase()}${group.slice(1)} only`;

export function Assistant() {
  const [roles, setRoles] = useState<Role[]>([FALLBACK_ROLE]);
  const [role, setRole] = useState<Role>(FALLBACK_ROLE);
  const [offline, setOffline] = useState(false);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState<{ id: number; n: number } | null>(null);
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetch("/api/roles")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((list: Role[]) => {
        if (list.length) {
          setRoles(list);
          setRole(list[0]);
        }
      })
      .catch(() => setOffline(true));
  }, []);

  const patch = useCallback((id: number, change: (e: Exchange) => Exchange) => {
    setExchanges((all) => all.map((e) => (e.id === id ? change(e) : e)));
  }, []);

  const ask = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || busy) return;
      const id = nextId.current++;
      setBusy(true);
      setDraft("");
      setExchanges((all) => [
        ...all,
        { id, question: q, role, status: "searching", text: "", sources: [] },
      ]);
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ block: "end" }));

      const fail = (failure: string) => patch(id, (e) => ({ ...e, status: "failed", failure }));

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ question: q, role: role.name }),
        });
        if (!res.ok || !res.body) {
          const body = await res.json().catch(() => null);
          fail(body?.message ?? "The assistant isn't responding. Try again in a minute.");
          return;
        }
        let finished = false;
        for await (const ev of readEvents(res.body)) {
          if (ev.event === "sources") {
            patch(id, (e) => ({ ...e, sources: ev.data, status: "writing" }));
          } else if (ev.event === "delta") {
            patch(id, (e) => ({ ...e, text: e.text + ev.data, status: "writing" }));
          } else if (ev.event === "done") {
            finished = true;
            patch(id, (e) => ({ ...e, outcome: ev.data, status: "done" }));
          } else if (ev.event === "error") {
            finished = true;
            fail(ev.data.message);
          }
        }
        if (!finished) fail("The answer was cut off before it finished. Ask again.");
      } catch {
        fail("The connection dropped. Check your network and ask again.");
      } finally {
        setBusy(false);
        inputRef.current?.focus();
      }
    },
    [busy, patch, role],
  );

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void ask(draft);
  };

  const starters = STARTERS[role.name] ?? STARTERS.employee;

  return (
    <div className="shell">
      <header className="masthead">
        <h1>Handbook assistant</h1>
        <fieldset className="roles">
          <legend>Answering as</legend>
          <div className="roles-options">
            {roles.map((r) => (
              <label key={r.name} className={r.name === role.name ? "is-selected" : undefined}>
                <input
                  type="radio"
                  name="role"
                  value={r.name}
                  checked={r.name === role.name}
                  onChange={() => setRole(r)}
                />
                {r.label}
              </label>
            ))}
          </div>
          <p className="roles-note">{role.description}</p>
        </fieldset>
      </header>

      <main className="thread">
        {offline && (
          <p className="notice" role="alert">
            The assistant service isn&apos;t reachable, so questions won&apos;t be answered yet. Start the
            API, then reload this page.
          </p>
        )}

        {exchanges.length === 0 ? (
          <section className="welcome">
            <h2>Ask about a policy. Get the answer and the page it came from.</h2>
            <p>
              Answers are written only from handbook pages the selected role can open. Each claim is
              numbered to the passage that supports it. If nothing supports an answer, you&apos;ll be told
              that instead.
            </p>
            <ul className="starters">
              {starters.map((q) => (
                <li key={q}>
                  <button type="button" onClick={() => void ask(q)} disabled={busy}>
                    <span>{q}</span>
                  </button>
                </li>
              ))}
            </ul>
            {role.name === "employee" && roles.length > 1 && (
              <p className="hint">
                The purchasing question lives on a Finance-only page. Ask it as Employee, then switch
                to Finance analyst and ask it again.
              </p>
            )}
          </section>
        ) : (
          exchanges.map((e) => (
            <ExchangeView
              key={e.id}
              exchange={e}
              activeN={active?.id === e.id ? active.n : null}
              onCite={(n) => setActive(n === null ? null : { id: e.id, n })}
              onRetry={() => void ask(e.question)}
              busy={busy}
            />
          ))
        )}
        <div ref={endRef} />
      </main>

      <footer className="dock">
        <form className="composer" onSubmit={onSubmit}>
          <label htmlFor="question" className="visually-hidden">
            Your question
          </label>
          <textarea
            id="question"
            ref={inputRef}
            rows={1}
            value={draft}
            maxLength={MAX_CHARS}
            placeholder={`Ask a policy question as ${role.label}`}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void ask(draft);
              }
            }}
          />
          <button type="submit" disabled={busy || !draft.trim()}>
            {busy ? "Answering" : "Ask"}
          </button>
        </form>
        <p className="disclosure">
          Demo built on the public GitLab handbook. Not affiliated with GitLab. Roles are simulated to
          show access control. Each question is answered on its own, without memory of earlier ones.
          Answers can be wrong, so open the cited page before acting on one.
        </p>
      </footer>
    </div>
  );
}

function ExchangeView({
  exchange: e,
  activeN,
  onCite,
  onRetry,
  busy,
}: {
  exchange: Exchange;
  activeN: number | null;
  onCite: (n: number | null) => void;
  onRetry: () => void;
  busy: boolean;
}) {
  const sourcesRef = useRef<HTMLElement>(null);
  const cited = new Set(e.outcome?.cited ?? []);
  const settled = e.status === "done";
  const refused = e.outcome?.refused ?? false;

  const used = settled ? e.sources.filter((s) => cited.has(s.n)) : e.sources;
  const unused = settled ? e.sources.filter((s) => !cited.has(s.n)) : [];

  const openSource = (n: number) => {
    const link = sourcesRef.current?.querySelector<HTMLAnchorElement>(`[data-source="${n}"] a`);
    link?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    link?.focus({ preventScroll: true });
  };

  return (
    <article className="exchange">
      <div className="exchange-main">
        <h2 className="question">{e.question}</h2>

        {e.status === "searching" && <p className="progress">Searching pages open to {e.role.label}…</p>}

        {e.status === "failed" ? (
          <div className="failure" role="alert">
            <p>{e.failure}</p>
            <button type="button" onClick={onRetry} disabled={busy}>
              Ask again
            </button>
          </div>
        ) : (
          <div
            className={refused ? "answer is-refusal" : "answer"}
            aria-live="polite"
            aria-busy={e.status !== "done"}
          >
            <AnswerText text={e.text} sourceCount={e.sources.length} onCite={onCite} onOpen={openSource} />
            {e.status === "writing" && <span className="caret" aria-hidden="true" />}
          </div>
        )}

        {settled && e.outcome && <Receipt outcome={e.outcome} exchange={e} />}
      </div>

      {e.status !== "failed" && e.sources.length > 0 && !refused && (
        <aside className="sources" ref={sourcesRef} aria-label="Sources for this answer">
          <h3>{settled ? "Cited passages" : "Passages found"}</h3>
          <ol>
            {used.map((s) => (
              <SourceItem key={s.n} source={s} active={activeN === s.n} />
            ))}
          </ol>
          {unused.length > 0 && (
            <details>
              <summary>
                {unused.length} more {unused.length === 1 ? "passage was" : "passages were"} found but not
                used
              </summary>
              <ol>
                {unused.map((s) => (
                  <SourceItem key={s.n} source={s} active={false} />
                ))}
              </ol>
            </details>
          )}
        </aside>
      )}
    </article>
  );
}

function SourceItem({ source: s, active }: { source: Source; active: boolean }) {
  return (
    <li data-source={s.n} className={active ? "source is-active" : "source"}>
      <span className="source-n" aria-hidden="true">
        {s.n}
      </span>
      <div>
        <a href={s.url} target="_blank" rel="noopener noreferrer">
          {s.title}
        </a>
        {s.heading && <p className="source-heading">{s.heading}</p>}
        <p className="source-snippet">{s.snippet}…</p>
        <p className="source-access">{groupLabel(s.access_group)}</p>
      </div>
    </li>
  );
}

/** One plain sentence about what the answer cost in time and money, and how well grounded it is. */
function Receipt({ outcome: o, exchange: e }: { outcome: Outcome; exchange: Exchange }) {
  const seconds = o.timings_ms.total != null ? (o.timings_ms.total / 1000).toFixed(1) : null;
  const cost = o.cost_usd.total;
  const approx = o.usage.token_source === "estimated" ? "about " : "";

  if (o.refused) {
    return (
      <p className="receipt">
        Asked as {e.role.label}. No passage open to this role answered the question, so nothing was
        made up to fill the gap.
      </p>
    );
  }
  return (
    <>
      {o.uncited && (
        <p className="warning" role="note">
          This answer cites no passage. Treat it as unverified.
        </p>
      )}
      <p className="receipt">
        Asked as {e.role.label}. Cites {o.cited.length} of {e.sources.length} passages found
        {seconds && `, answered in ${seconds} s`}
        {cost != null && cost > 0 && ` for ${approx}$${cost.toFixed(4)}`}.
      </p>
    </>
  );
}
