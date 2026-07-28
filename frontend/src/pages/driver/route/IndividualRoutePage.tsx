import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { RouteDetailView } from './components';

export const IndividualRoutePage = () => {
  const { routeId: routeIdFromUrl } = useParams();
  const [input, setInput] = useState('');
  const [pastedRouteId, setPastedRouteId] = useState<string | null>(null);

  const handleLoad = () => setPastedRouteId(input.trim() || null);
  const routeId = routeIdFromUrl ?? pastedRouteId;

  return (
    <main className="flex flex-col gap-4">
      {/* TODO: Remove this Route ID input once driver navigation lands. It only
          renders on the parameterless /driver/route, so a driver arriving on a
          real link never sees it. */}
      {!routeIdFromUrl && (
        <div className="flex flex-col gap-2">
          <label htmlFor="route-id" className="text-p2 text-grey-500">
            Route ID (dev)
          </label>
          <div className="flex gap-2">
            <input
              id="route-id"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLoad();
              }}
              placeholder="Paste a route UUID"
              className="border-grey-300 bg-grey-100 text-p2 flex-1 rounded-sm border px-3 py-2"
            />
            <button
              type="button"
              onClick={handleLoad}
              className="text-p2 rounded-sm bg-blue-300 px-4 py-2 font-semibold text-white"
            >
              Load
            </button>
          </div>
        </div>
      )}

      {routeId && <RouteDetailView routeId={routeId} />}
    </main>
  );
};
