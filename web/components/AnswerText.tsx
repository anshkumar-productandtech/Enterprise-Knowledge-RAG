import type { ReactNode } from "react";

type Props = {
  text: string;
  sourceCount: number;
  onCite: (n: number | null) => void;
  onOpen: (n: number) => void;
};

/**
 * Renders model output as paragraphs and lists, turning [n] into citation
 * buttons. Text is only ever inserted as React children, never as HTML, so
 * nothing the model (or a poisoned document) writes can inject markup.
 */
export function AnswerText({ text, sourceCount, onCite, onOpen }: Props) {
  const blocks: ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flush = () => {
    if (!list) return;
    const Tag = list.ordered ? "ol" : "ul";
    blocks.push(
      <Tag key={blocks.length}>
        {list.items.map((item, i) => (
          <li key={i}>{inline(item)}</li>
        ))}
      </Tag>,
    );
    list = null;
  };

  const inline = (line: string): ReactNode[] =>
    line.split(/(\[\d{1,2}\]|\*\*[^*]+\*\*)/g).map((part, i) => {
      const cite = /^\[(\d{1,2})\]$/.exec(part);
      if (cite) {
        const n = Number(cite[1]);
        if (n < 1 || n > sourceCount) return null; // a citation to a source that doesn't exist is dropped
        return (
          <button
            key={i}
            type="button"
            className="cite"
            aria-label={`Source ${n}`}
            onMouseEnter={() => onCite(n)}
            onMouseLeave={() => onCite(null)}
            onFocus={() => onCite(n)}
            onBlur={() => onCite(null)}
            onClick={() => onOpen(n)}
          >
            {n}
          </button>
        );
      }
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = /^[-*•]\s+(.*)$/.exec(line);
    const numbered = /^\d+[.)]\s+(.*)$/.exec(line);
    if (bullet || numbered) {
      const ordered = Boolean(numbered);
      if (!list || list.ordered !== ordered) {
        flush();
        list = { ordered, items: [] };
      }
      list.items.push((bullet ?? numbered)![1]);
      continue;
    }
    flush();
    if (line) blocks.push(<p key={blocks.length}>{inline(line.replace(/^#+\s*/, ""))}</p>);
  }
  flush();

  return <>{blocks}</>;
}
