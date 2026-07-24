import { useState } from 'react';

import { RouteDetailView } from './components';

export const IndividualRoutePage = () => {
  const [input, setInput] = useState('');
  const [routeId, setRouteId] = useState<string | null>(null);

  const handleLoad = () => setRouteId(input.trim() || null);

  return (
    <main className="flex flex-col gap-4">
      {/* TODO: Remove this Route ID input once driver navigation lands — a
          driver will reach this page via a link, so the route ID will come
          from the URL rather than being pasted in manually. */}
      <h1 className="text-h2 text-grey-500 font-bold">Individual Route</h1>

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
            className="border-grey-300 bg-grey-100 text-p2 flex-1 rounded-lg border px-3 py-2"
          />
          <button
            type="button"
            onClick={handleLoad}
            className="text-p2 rounded-lg bg-blue-300 px-4 py-2 font-semibold text-white"
          >
            Load
          </button>
        </div>
      </div>

      {routeId && <RouteDetailView routeId={routeId} />}
    </main>
  );
};
