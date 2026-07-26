/**
 * Recipes that drive the app into the state a design frame shows.
 *
 * Most frames render from a cold load, but a section usually also contains the
 * states you can only reach by using the screen — the login error, the
 * password-criteria error, the "link sent" confirmation. Selecting one of those
 * used to leave the app on its default state under the frame's design, which
 * looks like a layout bug and is really just a screen the harness never
 * navigated to.
 *
 * A recipe runs against the iframe's document after it loads. Frames are
 * matched on label because the same state is named differently per section —
 * mobile says "Login | Error" where desktop says "Default Log In - Error
 * States".
 *
 * Where the state is behind a server call the harness answers that one request
 * itself, rather than asking you to seed a database row and clean it up after.
 * The panel says when it has, because a stubbed response is a weaker claim than
 * a real one — good enough to compare layout, not evidence the call works.
 *
 * UNREACHABLE is for frames with no screen behind them at all. Nothing to
 * drive, so the harness says that instead of letting the fallback route look
 * like a bug.
 */

interface Recipe {
  /** Frame labels, across sections, that this recipe reaches. */
  labels: string[];
  /** Shown in the harness so it is clear what was done to the app. */
  describe: string;
  run: (doc: Document) => Promise<void>;
}

/**
 * React tracks its own value on the DOM node, so a plain assignment is ignored
 * and the native setter has to be called directly. Take it off the element's
 * own prototype rather than `HTMLInputElement.prototype`: the element belongs
 * to the iframe's realm, not ours, so ours would be the wrong object.
 */
const setValue = (el: HTMLInputElement, value: string) => {
  const setter = Object.getOwnPropertyDescriptor(
    Object.getPrototypeOf(el),
    'value'
  )?.set;
  setter?.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
};

const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** Poll rather than fixed-sleep: the response time is the app's, not ours. */
const until = async (test: () => boolean, timeoutMs = 4000) => {
  const started = performance.now();
  while (performance.now() - started < timeoutMs) {
    if (test()) return true;
    await wait(100);
  }
  return false;
};

/**
 * Leave the route and come back, so a screen that checks something on mount
 * checks it again. Needed when the check has already failed by the time the
 * harness gets the load event: React Query caches the rejection, and only a
 * remount asks a second time — by which point the stub is in place.
 */
const reenterRoute = async (doc: Document) => {
  const win = doc.defaultView;
  if (!win) return;
  const target = win.location.pathname + win.location.search;
  const leave = (to: string) => {
    win.history.pushState({}, '', to);
    win.dispatchEvent(new win.PopStateEvent('popstate'));
  };
  leave('/login');
  await wait(300);
  leave(target);
};

/**
 * Answer one request inside the iframe without touching the server.
 *
 * A few frames show a screen that only exists after a write succeeds, and the
 * write needs a row in the database. Faking the response puts the screen up
 * with no fixture to create and nothing to clean up afterwards — and since the
 * harness compares layout, a field value the design never shows is not what is
 * under test.
 *
 * This patches XMLHttpRequest, not fetch: the generated client runs on axios,
 * which uses XHR in the browser. Only the matching request is answered; every
 * other one goes to the real implementation through `super`.
 *
 * It is a stub, and the panel says so — you are looking at the app's own
 * rendering of a response it believes, not a round trip.
 */
const stubResponse = (
  doc: Document,
  matches: (url: string, method: string) => boolean,
  status: number,
  payload: unknown
) => {
  const win = doc.defaultView;
  if (!win) return;
  const Real = win.XMLHttpRequest;
  const body = JSON.stringify(payload);
  win.XMLHttpRequest = class extends Real {
    private stubbed = false;

    override open(method: string, url: string | URL): void {
      this.stubbed = matches(String(url), method.toUpperCase());
      super.open(method, url, true);
    }

    override send(payload?: Document | XMLHttpRequestBodyInit | null): void {
      if (!this.stubbed) {
        super.send(payload);
        return;
      }
      // The instance shadows the prototype's readonly getters.
      const fields = {
        readyState: 4,
        status,
        statusText: 'OK',
        response: body,
        responseText: body,
      };
      for (const [key, value] of Object.entries(fields)) {
        Object.defineProperty(this, key, { value, configurable: true });
      }
      // Asynchronously, so the caller has finished wiring its handlers up.
      setTimeout(() => {
        this.dispatchEvent(new win.Event('readystatechange'));
        this.dispatchEvent(new win.ProgressEvent('load'));
        this.dispatchEvent(new win.ProgressEvent('loadend'));
      }, 0);
    }

    override getAllResponseHeaders(): string {
      return this.stubbed
        ? 'content-type: application/json\r\n'
        : super.getAllResponseHeaders();
    }
  };
};

/** Enough of a registration response for the auth store to accept it. */
const REGISTERED = {
  auth: {
    access_token: 'design-overlay-stub',
    id: '00000000-0000-4000-8000-000000000001',
    first_name: 'Sam',
    last_name: 'Driver',
    full_name: 'Sam Driver',
    email: 'driver@example.com',
  },
  driver: { role: 'Driver' },
};

const RECIPES: Recipe[] = [
  {
    labels: ['Login | Error', 'Default Log In - Error States', 'Redo Log in'],
    describe: 'submitted bad credentials',
    run: async (doc) => {
      const email = doc.querySelector<HTMLInputElement>('input[type=email]');
      const password = doc.querySelector<HTMLInputElement>(
        'input[type=password]'
      );
      if (!email || !password) return;
      setValue(email, 'nobody@example.com');
      setValue(password, 'WrongPassword1!');
      doc.querySelector('form')?.requestSubmit();
      await until(() => /Incorrect email or password/.test(doc.body.innerText));
    },
  },
  {
    labels: [
      'Driver | Create Password Filled (2)',
      'First Time Login - Criteria Not Met',
      "First Time Login - Passwords Don't Match",
    ],
    describe: 'submitted a password that fails the criteria',
    run: async (doc) => {
      const fields = doc.querySelectorAll<HTMLInputElement>(
        'input[type=password]'
      );
      if (fields.length < 2) return;
      /*
       * The frame shows an error under both fields. "Password" fails the digit
       * and symbol rules, and the second has to differ from the first or they
       * match and only the first errors — one row short of the design.
       *
       * The text still differs: the design repeats the criteria message under
       * the confirm field where the code says the passwords do not match. The
       * layout is what this reproduces.
       */
      setValue(fields[0], 'Password');
      setValue(fields[1], 'Password1');
      doc.querySelector('form')?.requestSubmit();
      await until(() => /criteria/i.test(doc.body.innerText));
    },
  },
  {
    labels: ['Forgot Password Link Sent'],
    /*
     * The frame shows the resend control idle, but sending starts a 60s
     * cooldown, so for the first minute the app reads "Send again in N
     * seconds" where the design reads "Send link again". Same row, same
     * position — only the string differs, and only until it expires.
     */
    describe: 'requested a reset link (resend is in its 60s cooldown)',
    run: async (doc) => {
      const email = doc.querySelector<HTMLInputElement>('input[type=email]');
      if (!email) return;
      setValue(email, 'driver@example.com');
      doc.querySelector('form')?.requestSubmit();
      await until(() => /Send again in|link sent/i.test(doc.body.innerText));
    },
  },
  {
    labels: ['Account Created', 'Redo Log in Driver'],
    describe: 'created an account (registration response stubbed)',
    run: async (doc) => {
      stubResponse(
        doc,
        (url, method) => method === 'POST' && url.includes('/drivers/register'),
        201,
        REGISTERED
      );
      const fields = doc.querySelectorAll<HTMLInputElement>(
        'input[type=password]'
      );
      if (fields.length < 2) return;
      // Has to satisfy every criterion, or the form stops at its own validation.
      setValue(fields[0], 'Securepassword123!');
      setValue(fields[1], 'Securepassword123!');
      doc.querySelector('form')?.requestSubmit();
      await until(() => /Account created/.test(doc.body.innerText));
    },
  },
  {
    labels: ['Forgot Password | Driver Create Password Section'],
    describe: 'accepted the reset token (validation stubbed)',
    run: async (doc) => {
      stubResponse(
        doc,
        (url) => url.includes('/auth/validate-reset-token'),
        200,
        {}
      );
      // The check runs as the screen mounts, so it has already failed by now.
      await reenterRoute(doc);
      await until(() => /Enter new password/.test(doc.body.innerText));
    },
  },
  {
    labels: ['First Time Login - Empty State'],
    describe: 'submitted the form empty',
    run: async (doc) => {
      doc.querySelector('form')?.requestSubmit();
      await until(() => /Please enter a password/.test(doc.body.innerText));
    },
  },
];

const NOT_BUILT =
  'the account-creation link flow is designed but not built — nothing to compare against';

/**
 * Frames with no screen behind them at all, as opposed to a screen in a state
 * the harness has to reach. Nothing to drive; the design is simply ahead of the
 * build, and saying so beats letting the fallback route look like a bug.
 */
const UNREACHABLE: Record<string, string> = {
  'No Account Yet | Get Link': NOT_BUILT,
  'No Account Yet - Get Login Link': NOT_BUILT,
  // Their bodies say "a link to create your account", not "a password reset
  // link" — same journey as the screen above, and equally unbuilt. Only
  // "Forgot Password Link Sent" belongs to the reset flow the code implements.
  'Creation Link Sent': NOT_BUILT,
  'Resend Link': NOT_BUILT,
};

export const setupFor = (label: string | undefined) =>
  label ? (RECIPES.find((r) => r.labels.includes(label)) ?? null) : null;

export const unreachableReason = (label: string | undefined) =>
  label ? (UNREACHABLE[label] ?? null) : null;
