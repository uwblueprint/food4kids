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
    <div className="border-grey-300 bg-grey-150 relative rounded-xl border p-6">
      <button
        onClick={handleCopy}
        aria-label="Copy tree"
        className="text-grey-400 hover:text-grey-500 absolute top-4 right-4 rounded p-1 transition-colors"
      >
        {copied ? (
          <CheckIcon className="size-4" />
        ) : (
          <CopyIcon className="size-4" />
        )}
      </button>
      <pre className="text-grey-500 font-mono text-sm leading-6 whitespace-pre">
        {tree}
      </pre>
    </div>
  );
}
