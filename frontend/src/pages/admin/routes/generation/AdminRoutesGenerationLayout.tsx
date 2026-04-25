import { Outlet, useLocation } from 'react-router-dom';

import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';

import { ProgressStepper } from '../components';

const STEP_PATHS = [
  'import',
  'validate',
  'review',
  'configure',
  'complete',
] as const;

function getCurrentStep(pathname: string): number {
  const segment = pathname.split('/').pop();
  const index = STEP_PATHS.indexOf(segment as (typeof STEP_PATHS)[number]);
  return index === -1 ? 0 : index;
}

export function AdminRoutesGenerationLayout() {
  const { pathname } = useLocation();
  const currentStep = getCurrentStep(pathname);

  return (
    <div className="bg-grey-200 min-h-screen px-20 py-10">
      <div className="flex flex-col gap-10">
        {/* Breadcrumb + subtitle */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1">
            <span className="font-nunito text-h1 text-grey-400 font-bold">
              Routes
            </span>
            <ChevronRightIcon className="text-grey-400 size-8 shrink-0" />
            <span className="font-nunito text-h1 text-grey-500 font-bold">
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
        <Outlet />
      </div>
    </div>
  );
}
