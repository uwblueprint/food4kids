import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Dev-only design-overlay tool ("PerfectPixel"-style).
 *
 * Renders a Figma/PNG export as a fixed, opacity-adjustable image layered over
 * the running app so you can eyeball pixel alignment. Load an image via the file
 * picker, drag-drop onto the panel, or paste from the clipboard. Nudge, scale,
 * fade, and toggle it; all settings persist in localStorage.
 *
 * Mounted only under `import.meta.env.DEV` (see App.tsx). Not shipped to prod.
 *
 * Hotkey: Cmd/Ctrl+Shift+O toggles the overlay image on/off.
 */

const STORAGE_KEY = 'f4k_design_overlay';

interface OverlayState {
  visible: boolean;
  opacity: number; // 0..1
  x: number; // px offset
  y: number; // px offset
  scale: number; // 1 = natural size
  collapsed: boolean;
  src: string | null; // data URL of the design image
}

const DEFAULT_STATE: OverlayState = {
  visible: true,
  opacity: 0.5,
  x: 0,
  y: 0,
  scale: 1,
  collapsed: false,
  src: null,
};

function loadState(): OverlayState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_STATE;
    return { ...DEFAULT_STATE, ...(JSON.parse(raw) as Partial<OverlayState>) };
  } catch {
    return DEFAULT_STATE;
  }
}

function persistState(state: OverlayState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Image data URLs can blow past the ~5MB quota — fall back to persisting
    // everything except the image so at least the layout settings survive.
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ ...state, src: null })
      );
    } catch {
      /* give up silently — this is a dev tool */
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

export function DesignOverlay() {
  const [state, setState] = useState<OverlayState>(loadState);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const update = useCallback((patch: Partial<OverlayState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      persistState(next);
      return next;
    });
  }, []);

  const loadImageFile = useCallback(
    async (file: File | undefined | null) => {
      if (!file || !file.type.startsWith('image/')) return;
      const src = await readFileAsDataUrl(file);
      update({ src, visible: true });
    },
    [update]
  );

  // Toggle hotkey (Cmd/Ctrl+Shift+O) + arrow-key nudge while panel is focused.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.shiftKey &&
        event.key.toLowerCase() === 'o'
      ) {
        event.preventDefault();
        update({ visible: !state.visible });
        return;
      }

      // Arrow nudge only when the control panel owns focus, so we never steal
      // arrow keys from the app.
      const panel = document.getElementById('f4k-design-overlay-panel');
      if (!panel || !panel.contains(document.activeElement)) return;
      if (!state.src || !state.visible) return;
      const step = event.shiftKey ? 10 : 1;
      if (event.key === 'ArrowUp') update({ y: state.y - step });
      else if (event.key === 'ArrowDown') update({ y: state.y + step });
      else if (event.key === 'ArrowLeft') update({ x: state.x - step });
      else if (event.key === 'ArrowRight') update({ x: state.x + step });
      else return;
      event.preventDefault();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [state.visible, state.src, state.x, state.y, update]);

  // Paste an image from the clipboard (ignored while typing in a field).
  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return;
      }
      const file = [...(event.clipboardData?.items ?? [])]
        .find((item) => item.type.startsWith('image/'))
        ?.getAsFile();
      if (file) void loadImageFile(file);
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [loadImageFile]);

  const fitWidth = useCallback(() => {
    if (!state.src) return;
    const img = new Image();
    img.onload = () => {
      update({ scale: window.innerWidth / img.naturalWidth, x: 0, y: 0 });
    };
    img.src = state.src;
  }, [state.src, update]);

  return (
    <>
      {/* The design image layer — never intercepts pointer events. */}
      {state.src && state.visible && (
        <img
          src={state.src}
          alt=""
          aria-hidden
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            transform: `translate(${state.x}px, ${state.y}px) scale(${state.scale})`,
            transformOrigin: 'top left',
            opacity: state.opacity,
            pointerEvents: 'none',
            zIndex: 2147483646,
            maxWidth: 'none',
          }}
        />
      )}

      {/* Control panel. */}
      <div
        id="f4k-design-overlay-panel"
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
          left: 12,
          bottom: 12,
          zIndex: 2147483647,
          fontFamily:
            'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
          fontSize: 12,
          color: '#e5e7eb',
          background: 'rgba(17,17,20,0.92)',
          border: dragActive ? '1px dashed #60a5fa' : '1px solid #3f3f46',
          borderRadius: 10,
          boxShadow: '0 8px 28px rgba(0,0,0,0.45)',
          padding: state.collapsed ? '6px 10px' : 12,
          width: state.collapsed ? 'auto' : 248,
          userSelect: 'none',
          backdropFilter: 'blur(4px)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
          }}
        >
          <button
            type="button"
            onClick={() => update({ collapsed: !state.collapsed })}
            title="Collapse/expand"
            style={chipBtn}
          >
            🎯 Design overlay {state.collapsed ? '▸' : '▾'}
          </button>
          {!state.collapsed && (
            <button
              type="button"
              onClick={() => update({ visible: !state.visible })}
              title="Toggle (Cmd/Ctrl+Shift+O)"
              style={{
                ...chipBtn,
                color: state.visible ? '#86efac' : '#fca5a5',
              }}
            >
              {state.visible ? 'shown' : 'hidden'}
            </button>
          )}
        </div>

        {!state.collapsed && (
          <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
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
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  style={{ ...linkBtn }}
                >
                  choose a file
                </button>
              </div>
            ) : (
              <>
                <label style={row}>
                  <span style={lbl}>Opacity</span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={state.opacity}
                    onChange={(e) =>
                      update({ opacity: Number(e.target.value) })
                    }
                    style={{ flex: 1 }}
                  />
                  <span style={val}>{Math.round(state.opacity * 100)}%</span>
                </label>

                <label style={row}>
                  <span style={lbl}>Scale</span>
                  <input
                    type="range"
                    min={0.1}
                    max={3}
                    step={0.01}
                    value={state.scale}
                    onChange={(e) => update({ scale: Number(e.target.value) })}
                    style={{ flex: 1 }}
                  />
                  <span style={val}>{state.scale.toFixed(2)}×</span>
                </label>

                <div style={row}>
                  <span style={lbl}>Offset</span>
                  <input
                    type="number"
                    value={state.x}
                    onChange={(e) => update({ x: Number(e.target.value) })}
                    style={numInput}
                    title="X (←/→ to nudge)"
                  />
                  <input
                    type="number"
                    value={state.y}
                    onChange={(e) => update({ y: Number(e.target.value) })}
                    style={numInput}
                    title="Y (↑/↓ to nudge)"
                  />
                </div>

                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <button type="button" onClick={fitWidth} style={smallBtn}>
                    Fit width
                  </button>
                  <button
                    type="button"
                    onClick={() => update({ x: 0, y: 0, scale: 1 })}
                    style={smallBtn}
                  >
                    Reset pos
                  </button>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    style={smallBtn}
                  >
                    Replace
                  </button>
                  <button
                    type="button"
                    onClick={() => update({ src: null })}
                    style={{ ...smallBtn, color: '#fca5a5' }}
                  >
                    Clear
                  </button>
                </div>
                <div style={{ color: '#71717a', fontSize: 11 }}>
                  Arrow keys nudge (Shift = 10px) while this panel is focused.
                </div>
              </>
            )}
          </div>
        )}

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
    </>
  );
}

const chipBtn: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'inherit',
  font: 'inherit',
  cursor: 'pointer',
  padding: 0,
};

const linkBtn: React.CSSProperties = {
  ...chipBtn,
  color: '#60a5fa',
  textDecoration: 'underline',
};

const smallBtn: React.CSSProperties = {
  background: '#27272a',
  border: '1px solid #3f3f46',
  color: '#e5e7eb',
  font: 'inherit',
  fontSize: 11,
  cursor: 'pointer',
  borderRadius: 6,
  padding: '4px 8px',
};

const row: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
};

const lbl: React.CSSProperties = { width: 48, color: '#a1a1aa' };
const val: React.CSSProperties = {
  width: 38,
  textAlign: 'right',
  color: '#d4d4d8',
};
const numInput: React.CSSProperties = {
  flex: 1,
  width: 0,
  background: '#27272a',
  border: '1px solid #3f3f46',
  color: '#e5e7eb',
  font: 'inherit',
  fontSize: 11,
  borderRadius: 6,
  padding: '3px 6px',
};
