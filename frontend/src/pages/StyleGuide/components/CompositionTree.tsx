import { useState } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import CopyIcon from '@/assets/icons/copy.svg?react';

interface CompositionTreeProps {
  tree: string;
}

export function CompositionTree({ tree }: CompositionTreeProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(tree);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="relative rounded-xl border border-grey-300 bg-grey-150 p-6">
      <button
        onClick={handleCopy}
        aria-label="Copy tree"
        className="absolute top-4 right-4 rounded p-1 text-grey-400 transition-colors hover:text-grey-500"
      >
        {copied ? (
          <CheckIcon className="size-4" />
        ) : (
          <CopyIcon className="size-4" />
        )}
      </button>
      <pre className="font-mono text-sm text-grey-500 whitespace-pre leading-6">{tree}</pre>
    </div>
  );
}
