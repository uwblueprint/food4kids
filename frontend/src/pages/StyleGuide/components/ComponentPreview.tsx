import { type ReactNode, useState } from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { githubGist } from 'react-syntax-highlighter/dist/esm/styles/hljs';

import { cn } from '@/lib/utils';

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
