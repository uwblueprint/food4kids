import { type ReactNode } from 'react';

import AlertTriangleIcon from '@/assets/icons/alert-triangle.svg?react';
import { cn } from '@/lib/utils';

import { fieldNote } from './styles';

interface ErrorNoteProps {
  children: ReactNode;
  className?: string;
}

/**
 * The red note the auth screens put under a field — or under the form as a
 * whole, when the failure isn't any one field's fault.
 */
export const ErrorNote = ({ children, className }: ErrorNoteProps) => (
  <div className={cn(fieldNote, 'text-red flex items-center gap-1', className)}>
    <AlertTriangleIcon className="h-4 w-4 shrink-0" />
    <span>{children}</span>
  </div>
);
