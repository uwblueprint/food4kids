import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { setupFor, unreachableReason } from './frameSetup';

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
 * Two ways to get a design in:
 *   1. `pnpm run design:fetch -- <figma-url>` writes public/design-exports/ +
 *      a manifest, and the picker below then switches screen/viewport in one
 *      click (⌥←/⌥→ between screens, 1/2/3 between viewports).
 *   2. Drag-drop, paste (⌘V), or the file picker, for a one-off image.
 *
 * Settings persist in localStorage. Mounted only under import.meta.env.DEV.
 *
 * ---
 *
 * If you go past eyeballing and script a numeric comparison against the Figma
 * REST API, three things will otherwise cost you an afternoon each:
 *
 * 1. Figma's `absoluteBoundingBox` for a TEXT node is its LINE box. A browser
 *    element box only equals that for block text. For a `<button>` or `<input>`
 *    the line sits at `y + (height - lineHeight) / 2`, and a `Range` over a text
 *    node gives the GLYPH box, which reads ~1px high on a 24px heading. Compare
 *    the wrong pair and you will invent differences that are not there.
 * 2. There is a real floor of about 1px: Figma and Chrome measure the same
 *    string at slightly different widths (Figma says 165 for "Forgot your
 *    password?" where Chrome says 164). Right edges and line positions still
 *    agree. That residue is not a defect and cannot be fixed on either side.
 * 3. A frame showing a form error is a SPECIFIC error state. An error row is
 *    26px tall including its gap, so driving the app into a two-error state
 *    under a one-error frame shifts everything below it — and, because these
 *    blocks are vertically centred, everything above it by half as much in the
 *    other direction. That reads exactly like a layout bug. See frameSetup.ts,
 *    where the three password-error frames get three separate recipes.
 *
 * Text that the design shows as a typed field value ("PASS!W1") will never
 * match: the app masks it. Exclude those rather than chasing them.
 */

const STORAGE_KEY = 'f4k_design_overlay_harness';
const MANIFEST_URL = '/design-exports/manifest.json';

interface ManifestFrame {
  id: string;
  nodeId: string;
  label: string;
  /** Which flow the frame belongs to, e.g. "log in" / "drivers screen". */
  flow: string;
  viewport: string;
  route: string | null;
  width: number;
  height: number;
  image: string;
}

interface Manifest {
  fileName: string;
  fetchedAt: string;
  viewports: Record<string, { label: string; width: number }>;
  flows: Record<string, { label: string }>;
  frames: ManifestFrame[];
}

interface HarnessState {
  /** One-off pasted/dropped image. Takes precedence over the manifest frame. */
  manualSrc: string | null;
  opacity: number;
  designWidth: number;
  designHeight: number;
  appPath: string;
  showImage: boolean;
  /** Selected manifest frame id, e.g. "mobile/login-admin". */
  frameId: string | null;
  /** Per-frame route the user typed, when the manifest has none or it's wrong. */
  routeOverrides: Record<string, string>;
}

const DEFAULT_STATE: HarnessState = {
  manualSrc: null,
  opacity: 0.5,
  designWidth: 1440,
  designHeight: 1024,
  appPath: '/login',
  showImage: true,
  frameId: null,
  routeOverrides: {},
};

function loadState(): HarnessState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw)
      return {
        ...DEFAULT_STATE,
        ...(JSON.parse(raw) as Partial<HarnessState>),
      };
  } catch {
    /* ignore */
  }
  // Seed the design image from the floating-overlay tool if one's loaded there.
  try {
    const shared = JSON.parse(
      localStorage.getItem('f4k_design_overlay') || '{}'
    );
    if (shared.src) return { ...DEFAULT_STATE, manualSrc: shared.src };
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
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ ...state, manualSrc: null })
      );
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
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [vw, setVw] = useState(() => window.innerWidth);
  const [vh, setVh] = useState(() => window.innerHeight);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /** Patch state from its previous value, so callbacks never close over stale state. */
  const updateWith = useCallback(
    (patch: (prev: HarnessState) => Partial<HarnessState>) => {
      setState((prev) => {
        const next = { ...prev, ...patch(prev) };
        persist(next);
        return next;
      });
    },
    []
  );

  const update = useCallback(
    (patch: Partial<HarnessState>) => updateWith(() => patch),
    [updateWith]
  );

  const toggleImage = useCallback(
    () => updateWith((prev) => ({ showImage: !prev.showImage })),
    [updateWith]
  );

  useEffect(() => {
    const onResize = () => {
      setVw(window.innerWidth);
      setVh(window.innerHeight);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Load the Figma export manifest, if `design:fetch` has been run.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const res = await fetch(MANIFEST_URL);
        if (!res.ok) return;
        // Vite serves index.html for unknown paths — only trust real JSON.
        if (!res.headers.get('content-type')?.includes('json')) return;
        const data = (await res.json()) as Manifest;
        if (!cancelled) setManifest(data);
      } catch {
        /* no manifest — the manual image flow still works */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const frames = useMemo(() => manifest?.frames ?? [], [manifest]);
  const frame = frames.find((f) => f.id === state.frameId) ?? null;

  /*
   * Resolved before the memos below. The React Compiler treats a call into an
   * imported function as able to mutate anything reachable from its argument,
   * so doing this after `viewportFrames` made it consider that memo's inputs
   * modifiable and bail out of optimizing the component entirely.
   */
  const setup = setupFor(frame?.label);
  const unreachable = unreachableReason(frame?.label);
  const viewports = useMemo(
    () => Object.keys(manifest?.viewports ?? {}),
    [manifest]
  );
  const flows = useMemo(() => Object.keys(manifest?.flows ?? {}), [manifest]);
  const activeFlow = frame?.flow ?? flows[0] ?? null;
  const activeViewport = frame?.viewport ?? viewports[0] ?? null;
  const viewportFrames = useMemo(
    () =>
      frames.filter(
        (f) => f.flow === activeFlow && f.viewport === activeViewport
      ),
    [frames, activeFlow, activeViewport]
  );

  /**
   * Set when a viewport switch could not find the same screen and had to show a
   * different one. Silent fallback is worse than none: it presents one screen's
   * design over another's code, which reads as a layout bug.
   */
  const [viewportFallback, setViewportFallback] = useState<string | null>(null);

  /** What the harness did to the app to reach this frame's state, if anything. */
  const [setupNote, setSetupNote] = useState<string | null>(null);

  /**
   * Drive the app into the frame's state once the iframe has loaded. The iframe
   * is keyed on the frame, so this fires on every switch — always from a fresh
   * mount, never on top of the previous frame's leftovers.
   */
  const runSetup = async (iframe: HTMLIFrameElement | null) => {
    if (!setup) {
      setSetupNote(null);
      return;
    }
    const doc = iframe?.contentDocument;
    if (!doc) return;
    setSetupNote('setting up…');
    try {
      await setup.run(doc);
      setSetupNote(setup.describe);
    } catch {
      // Same-origin only in dev, and the app can always be driven by hand.
      setSetupNote(`could not set up — do it by hand (${setup.describe})`);
    }
  };

  const selectFrame = useCallback(
    (next: ManifestFrame | null | undefined) => {
      if (!next) return;
      /*
       * Whatever the notice was about, you have now picked a frame yourself, so
       * it no longer describes what is on screen. `switchViewport` sets it
       * again after this call when its own switch had to substitute a screen.
       */
      setViewportFallback(null);
      updateWith((prev) => ({
        frameId: next.id,
        manualSrc: null,
        designWidth: next.width,
        designHeight: next.height,
        appPath: prev.routeOverrides[next.id] ?? next.route ?? prev.appPath,
        showImage: true,
      }));
    },
    [updateWith]
  );

  /**
   * Same screen, different viewport.
   *
   * Matched on route first, because the sections do not agree on frame names:
   * mobile and tablet say "Login | Admin" where desktop says "Default Log In -
   * All Users". Label matching alone silently landed on an unrelated screen —
   * comparing one screen's code against another's design, which looks like a
   * layout bug and isn't. Label is still tried second, to tell apart the
   * several frames that share a route (its states).
   */
  const switchViewport = useCallback(
    (viewport: string) => {
      const candidates = frames.filter(
        (f) => f.viewport === viewport && f.flow === activeFlow
      );
      const sameRoute = frame?.route
        ? candidates.filter((f) => f.route === frame.route)
        : [];
      const match =
        sameRoute.find((f) => f.label === frame?.label) ??
        sameRoute[0] ??
        candidates.find((f) => f.label === frame?.label);
      const chosen = match ?? candidates[0];
      selectFrame(chosen);
      /*
       * Warn whenever the screen changed, not merely when the route could not
       * be matched. Several frames share one route — every create-password
       * state, for instance — so a route match can still swap the *state* out
       * from under you, which is just as misleading as swapping the screen.
       */
      setViewportFallback(
        !chosen || !frame || chosen.label === frame.label
          ? null
          : `No "${frame.label}" here — showing "${chosen.label}"`
      );
    },
    [frames, frame, activeFlow, selectFrame]
  );

  /** Switching flow keeps the current viewport where that flow has one. */
  const switchFlow = useCallback(
    (flow: string) => {
      const candidates = frames.filter((f) => f.flow === flow);
      selectFrame(
        candidates.find((f) => f.viewport === activeViewport) ?? candidates[0]
      );
    },
    [frames, activeViewport, selectFrame]
  );

  const stepFrame = useCallback(
    (delta: number) => {
      if (viewportFrames.length === 0) return;
      const i = frame ? viewportFrames.findIndex((f) => f.id === frame.id) : -1;
      selectFrame(
        viewportFrames[
          (i + delta + viewportFrames.length) % viewportFrames.length
        ]
      );
    },
    [viewportFrames, frame, selectFrame]
  );

  const loadImageFile = useCallback(
    async (file: File | undefined | null) => {
      if (!file || !file.type.startsWith('image/')) return;
      update({ manualSrc: await readFileAsDataUrl(file), showImage: true });
    },
    [update]
  );

  // Paste an image from the clipboard (ignored while typing in a field).
  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      if (isTypingTarget(event.target)) return;
      const file = [...(event.clipboardData?.items ?? [])]
        .find((i) => i.type.startsWith('image/'))
        ?.getAsFile();
      if (file) void loadImageFile(file);
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [loadImageFile]);

  // Keyboard: ⌥←/⌥→ step screens, 1/2/3 switch viewport, \ toggles the image.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (isTypingTarget(event.target)) return;
      if (event.altKey && event.key === 'ArrowRight') stepFrame(1);
      else if (event.altKey && event.key === 'ArrowLeft') stepFrame(-1);
      else if (event.key === '\\') toggleImage();
      else if (['1', '2', '3'].includes(event.key)) {
        const target = viewports[Number(event.key) - 1];
        if (!target) return;
        switchViewport(target);
      } else return;
      event.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [stepFrame, switchViewport, viewports, toggleImage]);

  const imageSrc = state.manualSrc ?? frame?.image ?? null;

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
        {/*
         * Keyed on the frame so picking a different one remounts the app.
         * Several frames share a route — the login screen and its error state,
         * every create-password state — and without this React keeps the
         * iframe mounted, so whatever you last drove the app into survives the
         * switch. You then get one screen's state under another's design,
         * which reads as a layout bug: the leftover error rows push
         * everything below them down.
         */}
        <iframe
          key={frame?.id ?? state.appPath}
          title="app"
          src={state.appPath}
          onLoad={(e) => void runSetup(e.currentTarget)}
          style={{
            width: state.designWidth,
            height: state.designHeight,
            border: 0,
            display: 'block',
            background: '#fff',
          }}
        />
        {imageSrc && state.showImage && (
          <img
            src={imageSrc}
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
          fontFamily:
            'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
          fontSize: 12,
          color: '#e5e7eb',
          background: 'rgba(17,17,20,0.92)',
          border: '1px solid #3f3f46',
          borderRadius: 10,
          boxShadow: '0 8px 28px rgba(0,0,0,0.45)',
          padding: 12,
          width: 300,
          display: 'grid',
          gap: 8,
          backdropFilter: 'blur(4px)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <strong>🎯 Overlay harness</strong>
          <button
            type="button"
            onClick={toggleImage}
            style={{ ...chip, color: state.showImage ? '#86efac' : '#fca5a5' }}
            title="Toggle the design image (\)"
          >
            {state.showImage ? 'shown' : 'hidden'}
          </button>
        </div>

        {manifest ? (
          <>
            {/* Flow picker */}
            {flows.length > 1 && (
              <label style={row}>
                <span style={lbl}>Flow</span>
                <select
                  value={activeFlow ?? ''}
                  onChange={(e) => switchFlow(e.target.value)}
                  style={{ ...num, flex: 1 }}
                >
                  {flows.map((f) => (
                    <option key={f} value={f}>
                      {manifest.flows[f].label}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {/* Viewport tabs */}
            <div style={{ display: 'flex', gap: 4 }}>
              {viewports.map((v, i) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => switchViewport(v)}
                  style={{
                    ...btn,
                    flex: 1,
                    background: v === activeViewport ? '#2563eb' : '#27272a',
                    borderColor: v === activeViewport ? '#2563eb' : '#3f3f46',
                  }}
                  title={`${manifest.viewports[v].label} (${i + 1})`}
                >
                  {manifest.viewports[v].label}
                </button>
              ))}
            </div>

            {/* Screen picker */}
            <div style={row}>
              <button
                type="button"
                onClick={() => stepFrame(-1)}
                style={btn}
                title="Previous screen (⌥←)"
              >
                ‹
              </button>
              <select
                value={frame?.id ?? ''}
                onChange={(e) =>
                  selectFrame(frames.find((f) => f.id === e.target.value))
                }
                style={{ ...num, flex: 1 }}
              >
                {!frame && <option value="">Pick a screen…</option>}
                {viewportFrames.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.label}
                    {f.route ? '' : '  ⚠ no route'}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => stepFrame(1)}
                style={btn}
                title="Next screen (⌥→)"
              >
                ›
              </button>
            </div>
            <div style={{ color: '#71717a', fontSize: 11 }}>
              {frame && activeViewport
                ? `${viewportFrames.findIndex((f) => f.id === frame.id) + 1} / ${
                    viewportFrames.length
                  } in ${manifest.viewports[activeViewport].label}`
                : `${frames.length} frames from ${manifest.fileName}`}
            </div>
          </>
        ) : (
          <div
            style={{
              border: '1px dashed #52525b',
              borderRadius: 8,
              padding: 10,
              lineHeight: 1.5,
              color: '#a1a1aa',
              fontSize: 11,
            }}
          >
            No Figma exports yet — run
            <br />
            <code style={{ color: '#e5e7eb' }}>
              pnpm run design:fetch -- &lt;url&gt;
            </code>
            <br />
            or drop/paste an image below.
          </div>
        )}

        {imageSrc ? (
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
        ) : (
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
              style={link}
            >
              choose a file
            </button>
          </div>
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
            onChange={(e) => {
              const appPath = e.target.value;
              updateWith((prev) => ({
                appPath,
                routeOverrides: frame
                  ? { ...prev.routeOverrides, [frame.id]: appPath }
                  : prev.routeOverrides,
              }));
            }}
            style={{ ...num, flex: 1 }}
            title="App route to load in the iframe (remembered per screen)"
          />
        </label>

        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            style={btn}
          >
            {state.manualSrc ? 'Replace' : 'Load'} image
          </button>
          {state.manualSrc && (
            <button
              type="button"
              onClick={() => update({ manualSrc: null })}
              style={{ ...btn, color: '#fca5a5' }}
              title={frame ? 'Back to the Figma export' : 'Clear the image'}
            >
              Clear
            </button>
          )}
        </div>

        <div style={{ color: '#86efac', fontSize: 11 }}>
          {state.designWidth}×{state.designHeight} @ {Math.round(fit * 100)}% —
          always 1:1, no resize needed
        </div>

        {/*
         * The stage is 1:1 in design pixels, but it is scaled to fit the
         * window, and at anything other than 100% the live text and the design
         * PNG resample differently. Small text then looks doubled even when the
         * boxes are identical — which reads as a spacing bug and is not one.
         * Headings and buttons stay crisp, so the effect looks selective, which
         * makes it more convincing rather than less.
         */}
        {fit < 0.995 && (
          <div style={{ color: '#a1a1aa', fontSize: 11 }}>
            Body text looks doubled below 100% — that is resampling, not
            misalignment. Make the window taller to judge it.
          </div>
        )}

        {viewportFallback && (
          <div
            style={{
              color: '#fdba74',
              fontSize: 11,
              border: '1px solid #b45309',
              borderRadius: 4,
              padding: '4px 6px',
            }}
          >
            ⚠ {viewportFallback}
          </div>
        )}

        {/*
         * Say what state the app is in, because for these frames it is not the
         * one a cold load gives you. Silence here is what made a driven-into
         * state look like a layout bug.
         */}
        {unreachable ? (
          <div
            style={{
              color: '#fdba74',
              fontSize: 11,
              border: '1px solid #b45309',
              borderRadius: 4,
              padding: '4px 6px',
            }}
          >
            ⚠ Cannot reach this state: {unreachable}
          </div>
        ) : (
          setupNote && (
            <div style={{ color: '#a1a1aa', fontSize: 11 }}>
              ⏵ app {setupNote}
            </div>
          )
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
    </div>
  );
}

function isTypingTarget(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  return Boolean(
    el &&
    (el.tagName === 'INPUT' ||
      el.tagName === 'TEXTAREA' ||
      el.tagName === 'SELECT' ||
      el.isContentEditable)
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
const link: React.CSSProperties = {
  ...chip,
  color: '#60a5fa',
  textDecoration: 'underline',
};
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
