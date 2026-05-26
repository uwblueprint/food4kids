import { useState } from 'react';

import { RouteMapView } from './components';

export const DriverHomePage = () => {
  const [input, setInput] = useState('');
  const [routeId, setRouteId] = useState<string | null>(null);

  return (
    <main className="page-margins flex flex-col gap-4">
      <h1>Driver Home</h1>

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
            placeholder="Paste a route UUID"
            className="flex-1 rounded-lg border border-grey-300 bg-grey-100 px-3 py-2 text-p2"
          />
          <button
            type="button"
            onClick={() => setRouteId(input.trim() || null)}
            className="rounded-lg bg-blue-300 px-4 py-2 text-p2 font-semibold text-white"
          >
            Load
          </button>
        </div>
      </div>

      {routeId && (
        <RouteMapView routeId={routeId} className="h-[60vh] md:h-[500px]" />
      )}
    </main>
  );
};