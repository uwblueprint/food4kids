import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Dev-only pixel-perfect design-comparison harness (route: /dev/overlay).
 *
 * Unlike the floating DesignOverlay (which layers an image over the live page
 * and needs the browser viewport to equal the design width), this embeds the
 * real app in a FIXED-size iframe (designWidth × designHeight) so the app always
 * lays out at the design's reference size — no matter how big the window is.
 * The design image is layered over the iframe at its native size, and the whole
 * stage is `transform: scale()`-d to fit the window. Because the iframe and the
 * image are scaled together, the overlay is ALWAYS 1:1 — you never resize.
 *
 * Load a design via drag-drop, paste (⌘V), or the file picker. Settings persist
 * in localStorage. Mounted only under import.meta.env.DEV.
 */

const STORAGE_KEY = 'f4k_design_overlay_harness';

interface HarnessState {
  src: string | null;
  opacity: number;
  designWidth: number;
  designHeight: number;
  appPath: string;
  showImage: boolean;
}

const DEFAULT_STATE: HarnessState = {
  src: null,
  opacity: 0.5,
  designWidth: 1440,
  designHeight: 1024,
  appPath: '/admin/home',
  showImage: true,
};

function loadState(): HarnessState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_STATE, ...(JSON.parse(raw) as Partial<HarnessState>) };
  } catch {
    /* ignore */
  }
  // Seed the design image from the floating-overlay tool if one's loaded there.
  try {
    const shared = JSON.parse(localStorage.getItem('f4k_design_overlay') || '{}');
    if (shared.src) return { ...DEFAULT_STATE, src: shared.src };
  } catch {
    /* ignore */
  }
  return DEFAULT_STATE;
}

function persist(state: HarnessState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, src: null }));
    } catch {
      /* dev tool — give up silently */
    }
  }
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export function DesignOverlayHarness() {
  const [state, setState] = useState<HarnessState>(loadState);
  const [dragActive, setDragActive] = useState(false);
  const [vw, setVw] = useState(() => window.innerWidth);
  const [vh, setVh] = useState(() => window.innerHeight);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const update = useCallback((patch: Partial<HarnessState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      persist(next);
      return next;
    });
  }, []);

  useEffect(() => {
    const onResize = () => {
      setVw(window.innerWidth);
      setVh(window.innerHeight);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const loadImageFile = useCallback(
    async (file: File | undefined | null) => {
      if (!file || !file.type.startsWith('image/')) return;
      update({ src: await readFileAsDataUrl(file), showImage: true });
    },
    [update]
  );

  // Paste an image from the clipboard (ignored while typing in a field).
  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      const t = event.target as HTMLElement | null;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) {
        return;
      }
      const file = [...(event.clipboardData?.items ?? [])]
        .find((i) => i.type.startsWith('image/'))
        ?.getAsFile();
      if (file) void loadImageFile(file);
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [loadImageFile]);

  // Fit the design-sized stage into the window. Never upscale past 1:1.
  const fit = Math.min(
    1,
    vw / state.designWidth,
    (vh - 8) / state.designHeight
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        void loadImageFile(e.dataTransfer.files?.[0]);
      }}
      style={{
        position: 'fixed',
        inset: 0,
        background: dragActive ? '#1e293b' : '#0b0b0d',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* The design-sized stage: app iframe + design image, scaled together. */}
      <div
        style={{
          position: 'relative',
          width: state.designWidth,
          height: state.designHeight,
          transform: `scale(${fit})`,
          transformOrigin: 'center center',
          flex: '0 0 auto',
          boxShadow: '0 0 0 1px #3f3f46',
        }}
      >
        <iframe
          title="app"
          src={state.appPath}
          style={{
            width: state.designWidth,
            height: state.designHeight,
            border: 0,
            display: 'block',
            background: '#fff',
          }}
        />
        {state.src && state.showImage && (
          <img
            src={state.src}
            alt=""
            aria-hidden
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: state.designWidth, // 1 design px = 1 iframe px → always 1:1
              height: 'auto',
              opacity: state.opacity,
              pointerEvents: 'none',
            }}
          />
        )}
      </div>

      {/* Controls (unscaled). */}
      <div
        style={{
          position: 'fixed',
          left: 12,
          bottom: 12,
          zIndex: 10,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
          fontSize: 12,
          color: '#e5e7eb',
          background: 'rgba(17,17,20,0.92)',
          border: '1px solid #3f3f46',
          borderRadius: 10,
          boxShadow: '0 8px 28px rgba(0,0,0,0.45)',
          padding: 12,
          width: 260,
          display: 'grid',
          gap: 8,
          backdropFilter: 'blur(4px)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <strong>🎯 Overlay harness</strong>
          <button
            type="button"
            onClick={() => update({ showImage: !state.showImage })}
            style={{ ...chip, color: state.showImage ? '#86efac' : '#fca5a5' }}
          >
            {state.showImage ? 'shown' : 'hidden'}
          </button>
        </div>

        {!state.src ? (
          <div
            style={{
              border: '1px dashed #52525b',
              borderRadius: 8,
              padding: 12,
              textAlign: 'center',
              lineHeight: 1.5,
              color: '#a1a1aa',
            }}
          >
            Drag an image here, paste (⌘V),
            <br />
            or{' '}
            <button type="button" onClick={() => fileInputRef.current?.click()} style={link}>
              choose a file
            </button>
          </div>
        ) : (
          <label style={row}>
            <span style={lbl}>Opacity</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={state.opacity}
              onChange={(e) => update({ opacity: Number(e.target.value) })}
              style={{ flex: 1 }}
            />
            <span style={val}>{Math.round(state.opacity * 100)}%</span>
          </label>
        )}

        <div style={row}>
          <span style={lbl}>Design</span>
          <input
            type="number"
            value={state.designWidth}
            onChange={(e) => update({ designWidth: Number(e.target.value) })}
            style={num}
            title="Frame width (px)"
          />
          <span style={{ color: '#71717a' }}>×</span>
          <input
            type="number"
            value={state.designHeight}
            onChange={(e) => update({ designHeight: Number(e.target.value) })}
            style={num}
            title="Frame height (px)"
          />
        </div>

        <label style={row}>
          <span style={lbl}>Page</span>
          <input
            type="text"
            value={state.appPath}
            onChange={(e) => update({ appPath: e.target.value })}
            style={{ ...num, flex: 1 }}
            title="App route to load in the iframe"
          />
        </label>

        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button type="button" onClick={() => fileInputRef.current?.click()} style={btn}>
            {state.src ? 'Replace' : 'Load'} image
          </button>
          {state.src && (
            <button
              type="button"
              onClick={() => update({ src: null })}
              style={{ ...btn, color: '#fca5a5' }}
            >
              Clear
            </button>
          )}
        </div>

        <div style={{ color: '#86efac', fontSize: 11 }}>
          {state.designWidth}×{state.designHeight} @ {Math.round(fit * 100)}% — always 1:1, no
          resize needed
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            void loadImageFile(e.target.files?.[0]);
            e.target.value = '';
          }}
        />
      </div>
    </div>
  );
}

const chip: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'inherit',
  font: 'inherit',
  cursor: 'pointer',
  padding: 0,
};
const link: React.CSSProperties = { ...chip, color: '#60a5fa', textDecoration: 'underline' };
const btn: React.CSSProperties = {
  background: '#27272a',
  border: '1px solid #3f3f46',
  color: '#e5e7eb',
  font: 'inherit',
  fontSize: 11,
  cursor: 'pointer',
  borderRadius: 6,
  padding: '4px 8px',
};
const row: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 8 };
const lbl: React.CSSProperties = { width: 48, color: '#a1a1aa' };
const val: React.CSSProperties = { width: 38, textAlign: 'right', color: '#d4d4d8' };
const num: React.CSSProperties = {
  width: 0,
  flex: 1,
  minWidth: 0,
  background: '#27272a',
  border: '1px solid #3f3f46',
  color: '#e5e7eb',
  font: 'inherit',
  fontSize: 11,
  borderRadius: 6,
  padding: '3px 6px',
};
