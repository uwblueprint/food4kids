import { type CSSProperties, type ReactNode, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

import { cn } from '@/lib/utils';

// githubGist palette mapped to Prism token names so we get consistent
// highlighting on complex nested JSX (hljs's TSX tokenizer breaks on it)
const githubGist: Record<string, CSSProperties> = {
  'code[class*="language-"]': { color: '#24292e', background: 'none' },
  'pre[class*="language-"]': { color: '#24292e', background: 'none' },
  comment: { color: '#6a737d', fontStyle: 'italic' },
  'block-comment': { color: '#6a737d', fontStyle: 'italic' },
  keyword: { color: '#d73a49' },
  boolean: { color: '#d73a49' },
  operator: { color: '#d73a49' },
  tag: { color: '#22863a' },
  'class-name': { color: '#6f42c1' },
  'maybe-class-name': { color: '#6f42c1' },
  function: { color: '#6f42c1' },
  string: { color: '#032f62' },
  'attr-value': { color: '#032f62' },
  regex: { color: '#032f62' },
  'attr-name': { color: '#005cc5' },
  number: { color: '#005cc5' },
  builtin: { color: '#e36209' },
  punctuation: { color: '#24292e' },
  plain: { color: '#24292e' },
};

interface ComponentPreviewProps {
  /** The live component to render in the preview area */
  children: ReactNode;
  /** Raw code string shown in the code panel */
  code: string;
  /** Optional label shown above the preview */
  title?: string;
  /** Min height of the preview area (Tailwind class, default min-h-48) */
  previewClassName?: string;
}

export function ComponentPreview({
  children,
  code,
  title,
  previewClassName,
}: ComponentPreviewProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-grey-300 overflow-hidden rounded-xl border">
      {title && (
        <div className="border-grey-300 border-b bg-white px-4 py-2.5">
          <span className="text-p2 text-grey-500 font-semibold">{title}</span>
        </div>
      )}

      {/* Live preview */}
      <div
        className={cn(
          'flex items-center justify-center bg-white p-12',
          previewClassName ?? 'min-h-48'
        )}
      >
        {children}
      </div>

      {/* Code panel */}
      <div className="border-grey-300 bg-grey-150 relative border-t">
        {open ? (
          <>
            <div className="max-h-64 overflow-y-auto">
              <SyntaxHighlighter
                language="tsx"
                style={githubGist}
                customStyle={{
                  background: 'transparent',
                  margin: 0,
                  padding: '1rem',
                  fontSize: '0.875rem',
                  lineHeight: '1.5rem',
                }}
              >
                {code}
              </SyntaxHighlighter>
            </div>
            <div className="border-grey-300 flex justify-center border-t py-2">
              <button
                onClick={() => setOpen(false)}
                className="text-p3 text-grey-400 hover:text-grey-500 transition-colors"
              >
                Collapse
              </button>
            </div>
          </>
        ) : (
          <div className="relative h-20 overflow-hidden">
            <SyntaxHighlighter
              language="tsx"
              style={githubGist}
              customStyle={{
                background: 'transparent',
                margin: 0,
                padding: '1rem',
                fontSize: '0.875rem',
                lineHeight: '1.5rem',
              }}
            >
              {code}
            </SyntaxHighlighter>
            <div className="from-grey-150 via-grey-150/70 absolute inset-0 flex items-center justify-center bg-gradient-to-t to-transparent">
              <button
                onClick={() => setOpen(true)}
                className="border-grey-300 text-grey-500 shadow-card hover:bg-grey-150 rounded-full border bg-white px-4 py-1.5 text-sm font-medium transition-colors"
              >
                View Code
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
