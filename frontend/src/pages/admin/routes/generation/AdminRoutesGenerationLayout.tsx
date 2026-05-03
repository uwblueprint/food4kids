import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';

import { ProgressStepper } from '../components';

const STEP_PATHS = [
  'import',
  'validate',
  'review',
  'configure',
  'generate',
] as const;

function getCurrentStep(pathname: string): number {
  const segment = pathname.split('/').pop();
  const index = STEP_PATHS.indexOf(segment as (typeof STEP_PATHS)[number]);
  return index === -1 ? 0 : index;
}

export interface GenerationOutletContext {
  file: File | null;
  setFile: (f: File | null) => void;
  columnMap: Record<string, string>;
  setColumnMap: (m: Record<string, string>) => void;
}

export function AdminRoutesGenerationLayout() {
  const { pathname } = useLocation();
  const currentStep = getCurrentStep(pathname);

  const [file, setFile] = useState<File | null>(null);
  const [columnMap, setColumnMap] = useState<Record<string, string>>({});

  const context: GenerationOutletContext = {
    file,
    setFile,
    columnMap,
    setColumnMap,
  };

  return (
    <div className="flex flex-col gap-10">
      {/* Breadcrumb + subtitle */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-1">
          <Link
            to="/admin/routes"
            className="text-h1 text-grey-400 cursor-pointer font-bold"
          >
            Routes
          </Link>
          <ChevronRightIcon className="text-grey-400 size-8 shrink-0" />
          <span className="text-h1 text-grey-500 font-bold">
            Route Generation
          </span>
        </div>
        <p className="text-p1 text-grey-500">
          Import family data and generate delivery routes
        </p>
      </div>

      {/* Stepper — shared across all steps */}
      <ProgressStepper currentStep={currentStep} />

      {/* Step content */}
      <Outlet context={context} />
    </div>
  );
}
