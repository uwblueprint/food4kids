import { CheckIcon } from 'lucide-react';

import { cn } from '@/lib/utils';

import { getPasswordRequirements } from './passwordUtils';
import { fieldNote } from './styles';

interface PasswordRequirementsListProps {
  password: string;
}

export const PasswordRequirementsList = ({
  password,
}: PasswordRequirementsListProps) => {
  const requirements = getPasswordRequirements(password);

  return (
    <div className="desktop:mt-5 mt-2">
      <p className={cn(fieldNote, 'mb-[3px]')}>Password must include:</p>
      <ul className="space-y-[3px]">
        {requirements.map((req, index) => (
          <PasswordRequirement
            key={index}
            label={req.label}
            isSatisfied={req.isSatisfied}
          />
        ))}
      </ul>
    </div>
  );
};

interface PasswordRequirementProps {
  label: string;
  isSatisfied: boolean;
}

const PasswordRequirement = ({
  label,
  isSatisfied,
}: PasswordRequirementProps) => {
  return (
    <li className={cn(fieldNote, 'flex items-center gap-1')}>
      {isSatisfied ? (
        <CheckIcon
          className="h-4 w-4 shrink-0 text-green-500"
          strokeWidth={3}
        />
      ) : (
        // A little custom gray dot indicator when invalid
        <div className="flex h-4 w-4 shrink-0 items-center justify-center">
          <span className="h-1 w-1 rounded-full bg-black" />
        </div>
      )}
      <span
        className={cn(
          'transition-colors duration-200',
          isSatisfied ? 'text-success-stroke' : 'text-current'
        )}
      >
        {label}
      </span>
    </li>
  );
};
