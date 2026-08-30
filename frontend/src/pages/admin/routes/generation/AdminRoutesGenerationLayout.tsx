import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

import { useSystemSettings } from '@/api';
import type {
  LocationImportPreview,
  RouteGenerationGroupInput,
} from '@/api/generated/types.gen';
import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';

import { ProgressStepper } from '../components';
import { deliveryTypeSelection } from './deliveryTypeSelection';

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
  fileHeaders: string[];
  setFileHeaders: (h: string[]) => void;
  columnMap: Record<string, string>;
  setColumnMap: (m: Record<string, string>) => void;
  selectedDeliveryType: string;
  setSelectedDeliveryType: (deliveryType: string) => void;
  reviewResult: LocationImportPreview | null;
  setReviewResult: (r: LocationImportPreview | null) => void;
  routeGenerationInputs: RouteGenerationGroupInput[];
  setRouteGenerationInputs: (inputs: RouteGenerationGroupInput[]) => void;
  /**
   * Whether the step being shown has finished its work. Only the last step
   * reports this — the frames tick "Generate Routes" off once the summary is
   * up, and the stepper otherwise has no way to know a step it is sitting on
   * is done.
   */
  currentStepComplete: boolean;
  setCurrentStepComplete: (complete: boolean) => void;
}

export function AdminRoutesGenerationLayout() {
  const { pathname } = useLocation();
  const currentStep = getCurrentStep(pathname);

  const { data: systemSettings, isSuccess: settingsLoaded } =
    useSystemSettings();

  const [file, setFile] = useState<File | null>(null);
  const [fileHeaders, setFileHeaders] = useState<string[]>([]);
  const [columnMap, setColumnMap] = useState<Record<string, string>>({});
  const [selectedDeliveryType, setSelectedDeliveryType] = useState('');
  const [hasSeededFromSettings, setHasSeededFromSettings] = useState(false);
  const [reviewResult, setReviewResult] =
    useState<LocationImportPreview | null>(null);
  const [routeGenerationInputs, setRouteGenerationInputs] = useState<
    RouteGenerationGroupInput[]
  >([]);
  const [currentStepComplete, setCurrentStepComplete] = useState(false);

  if (!hasSeededFromSettings && settingsLoaded) {
    setHasSeededFromSettings(true);
    setColumnMap(systemSettings?.import_column_map ?? {});
    // A single configured delivery type is not a choice, so apply it here and
    // let the import step skip its picker entirely.
    const selection = deliveryTypeSelection(systemSettings);
    if (selection.kind === 'only') {
      setSelectedDeliveryType(selection.deliveryType);
    }
  }

  const context: GenerationOutletContext = {
    file,
    setFile,
    fileHeaders,
    setFileHeaders,
    columnMap,
    setColumnMap,
    selectedDeliveryType,
    setSelectedDeliveryType,
    reviewResult,
    setReviewResult,
    routeGenerationInputs,
    setRouteGenerationInputs,
    currentStepComplete,
    setCurrentStepComplete,
  };

  return (
    // Tall enough to fill the viewport minus the page margins, so the sticky
    // footer's `mt-auto` still puts it at the bottom of the screen on a step
    // whose content doesn't reach that far.
    <div className="desktop:min-h-[calc(100dvh-4rem)] flex min-h-[calc(100dvh-2.75rem)] flex-col gap-10">
      {/* Breadcrumb + subtitle. 4px, not 8: the frames make this block 72 tall
          (44 + 4 + 24), and the extra 4 pushed every section below it down. */}
      <div className="flex flex-col gap-1">
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
          Import data and generate delivery routes
        </p>
      </div>

      {/* Stepper — shared across all steps */}
      <ProgressStepper
        currentStep={currentStep + (currentStepComplete ? 1 : 0)}
      />

      {/* Step content */}
      <Outlet context={context} />
    </div>
  );
}
