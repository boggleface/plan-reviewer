import React, { useEffect, useRef } from 'react';

type Props = {
  text: string;
  activeQuote: string | null;
  onClearQuote: () => void;
};

function findQuoteRange(
  source: string,
  quote: string | null
): { start: number; end: number } | null {
  if (!quote || !quote.trim()) return null;
  // Normalize whitespace into flexible regex
  const words = quote
    .trim()
    .split(/\s+/)
    .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  try {
    const regex = new RegExp(words.join('\\s+'), 'i');
    const match = source.match(regex);
    if (!match || match.index === undefined) return null;
    return { start: match.index, end: match.index + match[0].length };
  } catch {
    return null;
  }
}

export const PlanText: React.FC<Props> = ({
  text,
  activeQuote,
  onClearQuote,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const quoteRange = findQuoteRange(text, activeQuote);

  useEffect(() => {
    if (activeQuote && quoteRange) {
      const el = document.getElementById('active-quote-highlight');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeQuote, quoteRange]);

  // Helper to render inline text with potential quote highlight
  const renderInlineWithHighlight = (
    content: string,
    contentStart: number
  ) => {
    if (!quoteRange) {
      return renderBold(content);
    }

    const contentEnd = contentStart + content.length;
    // Check if quoteRange overlaps [contentStart, contentEnd]
    const overlapStart = Math.max(contentStart, quoteRange.start);
    const overlapEnd = Math.min(contentEnd, quoteRange.end);

    if (overlapStart < overlapEnd) {
      const relStart = overlapStart - contentStart;
      const relEnd = overlapEnd - contentStart;

      const before = content.slice(0, relStart);
      const highlighted = content.slice(relStart, relEnd);
      const after = content.slice(relEnd);

      return (
        <>
          {renderBold(before)}
          <mark
            id="active-quote-highlight"
            className="quote-highlight"
            title="Active verbatim quote from review"
          >
            {highlighted}
          </mark>
          {renderBold(after)}
        </>
      );
    }

    return renderBold(content);
  };

  // Helper to parse **bold** text
  const renderBold = (str: string) => {
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  // Render text blocks preserving offsets
  const renderBlocks = () => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let currentOffset = 0;
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const lineStart = currentOffset;
      const lineLen = line.length + 1; // +1 for \n

      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={i}>
            {renderInlineWithHighlight(line.slice(2), lineStart + 2)}
          </h1>
        );
        currentOffset += lineLen;
        i++;
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={i}>
            {renderInlineWithHighlight(line.slice(3), lineStart + 3)}
          </h2>
        );
        currentOffset += lineLen;
        i++;
      } else if (line.startsWith('### ')) {
        elements.push(
          <h3 key={i}>
            {renderInlineWithHighlight(line.slice(4), lineStart + 4)}
          </h3>
        );
        currentOffset += lineLen;
        i++;
      } else if (line.startsWith('|')) {
        // Parse markdown table
        const tableLines: { text: string; start: number }[] = [];
        while (i < lines.length && lines[i].startsWith('|')) {
          tableLines.push({ text: lines[i], start: currentOffset });
          currentOffset += lines[i].length + 1;
          i++;
        }

        const isDivider = (l: string) =>
          l.replace(/[|\s-:]/g, '').length === 0;

        const headerLine = tableLines[0];
        const bodyLines = tableLines.slice(1).filter((l) => !isDivider(l.text));

        const parseCells = (rowText: string) =>
          rowText
            .split('|')
            .slice(1, -1)
            .map((c) => c.trim());

        elements.push(
          <table key={`table-${i}`}>
            {headerLine && (
              <thead>
                <tr>
                  {parseCells(headerLine.text).map((cell, cIdx) => (
                    <th key={cIdx}>{cell}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {bodyLines.map((row, rIdx) => {
                const cells = parseCells(row.text);
                return (
                  <tr key={rIdx}>
                    {cells.map((cell, cIdx) => {
                      // find offset of cell within row
                      const cellIdxInRow = row.text.indexOf(cell);
                      const cellStart =
                        row.start +
                        (cellIdxInRow >= 0 ? cellIdxInRow : 0);
                      return (
                        <td key={cIdx}>
                          {renderInlineWithHighlight(cell, cellStart)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        );
      } else if (line.startsWith('- ')) {
        elements.push(
          <ul key={i}>
            <li>{renderInlineWithHighlight(line.slice(2), lineStart + 2)}</li>
          </ul>
        );
        currentOffset += lineLen;
        i++;
      } else if (line.trim().length === 0) {
        currentOffset += lineLen;
        i++;
      } else {
        elements.push(
          <p key={i}>
            {renderInlineWithHighlight(line, lineStart)}
          </p>
        );
        currentOffset += lineLen;
        i++;
      }
    }

    return elements;
  };

  return (
    <div className="card plan-panel">
      <div className="card-header">
        <span className="section-label">Source Plan Document</span>
        {activeQuote && (
          <button className="btn-link" onClick={onClearQuote}>
            Clear highlight
          </button>
        )}
      </div>
      <div className="plan-text-body" ref={containerRef}>
        {renderBlocks()}
      </div>
    </div>
  );
};
