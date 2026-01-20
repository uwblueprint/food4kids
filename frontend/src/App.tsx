import { useState } from 'react';

import viteLogo from '/vite.svg';

import reactLogo from './assets/react.svg';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white">
      <div className="mb-8 flex gap-12">
        <a
          href="https://vite.dev"
          target="_blank"
          className="transition-all duration-300 hover:drop-shadow-[0_0_2em_#646cffaa]"
        >
          <img src={viteLogo} className="h-24 p-6" alt="Vite logo" />
        </a>
        <a
          href="https://react.dev"
          target="_blank"
          className="transition-all duration-300 hover:drop-shadow-[0_0_2em_#61dafbaa]"
        >
          <img
            src={reactLogo}
            className="h-24 p-6 animate-[spin_20s_linear_infinite]"
            alt="React logo"
          />
        </a>
      </div>
      <h1 className="text-6xl font-bold leading-tight">Vite + React</h1>
      <div className="flex flex-col items-center rounded-lg p-8">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="mb-4 rounded-lg border border-transparent bg-gray-800 px-5 py-2.5 text-base font-medium transition-colors hover:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/50"
        >
          count is {count}
        </button>
        <p className="text-gray-400">
          Edit <code className="font-mono">src/App.tsx</code> and save to test
          HMR
        </p>
      </div>
      <p className="mt-8 text-gray-500">
        Click on the Vite and React logos to learn more
      </p>
    </div>
  );
}

export default App;
