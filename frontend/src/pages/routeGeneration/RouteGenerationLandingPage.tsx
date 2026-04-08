import { useNavigate } from 'react-router-dom';

import ShareIcon from '@/assets/icons/share.svg?react';
import { Button } from '@/common/components';

// TODO: Replace with real API data when available

interface LastGeneration {
  routes: number;
  families: number;
  generatedAt: Date;
}
const lastGeneration: LastGeneration = {
  routes: 6,
  families: 44,
  generatedAt: new Date('2025-11-02T18:17:00Z'),
};

export const RouteGenerationLandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-8">
      <div className="flex gap-4">
        {/* Import Data Card */}
        <div className="border-grey-300 flex flex-1 flex-col gap-1 rounded-2xl border bg-white p-6">
          <div className="flex flex-col gap-1">
            <h2>Import Data</h2>
            <p className="text-p1 text-grey-400">
              Upload a new Excel file (.xlsx) to generate fresh routes.
            </p>
          </div>

          <div className="flex flex-1 items-center justify-center py-10">
            <ShareIcon className="size-12 text-blue-300" />
          </div>

          <Button className="w-full" onClick={() => navigate('import')}>
            Import New File
          </Button>
        </div>

        {/* Use Last Generation Card */}
        <div className="border-grey-300 flex flex-1 flex-col gap-4 rounded-2xl border bg-white p-6">
          <div className="flex flex-col gap-1">
            <h2>Use Data from Last Generation</h2>
            <p className="text-p1 text-grey-400">
              Generate routes using your previously updated data.
            </p>
          </div>

          <div className="flex flex-1 items-center">
            <div className="w-full rounded-lg border border-blue-100 bg-blue-50 p-4">
              <p className="text-p1 font-semibold">
                {lastGeneration.routes} routes, {lastGeneration.families}{' '}
                families
              </p>
              <p className="text-p2 text-grey-400">
                Generated{' '}
                {lastGeneration.generatedAt.toLocaleString('en-US', {
                  month: 'numeric',
                  day: 'numeric',
                  year: 'numeric',
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true,
                })}
              </p>
            </div>
          </div>

          <Button className="w-full" disabled>
            Use Last Generation Data
          </Button>
        </div>
      </div>
    </div>
  );
};
