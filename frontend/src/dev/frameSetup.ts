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
 * Some states are deliberately absent: they need a password-reset token that
 * exists in the database, which the harness cannot mint. Those are listed in
 * UNREACHABLE so the harness can say so rather than show a silent mismatch.
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
    labels: [
      'Forgot Password Link Sent',
      'Creation Link Sent',
      'Resend Link',
      'Could do sum like',
    ],
    describe: 'requested a reset link',
    run: async (doc) => {
      const email = doc.querySelector<HTMLInputElement>('input[type=email]');
      if (!email) return;
      setValue(email, 'driver@example.com');
      doc.querySelector('form')?.requestSubmit();
      await until(() => /Send again in|link sent/i.test(doc.body.innerText));
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

/**
 * States that need a password-reset token row in the database. The app checks
 * the token before it will render them, so no amount of clicking gets there
 * from a placeholder UUID — mint a real one and put it in the Page field.
 */
const UNREACHABLE: Record<string, string> = {
  'Account Created':
    'needs a real reset token — the confirmation only appears after the password POST succeeds',
  'Redo Log in Driver':
    'needs a real reset token — the confirmation only appears after the password POST succeeds',
  'Forgot Password | Driver Create Password Section':
    'needs a real reset token — the form is behind a token-validity check',
};

export const setupFor = (label: string | undefined) =>
  label ? (RECIPES.find((r) => r.labels.includes(label)) ?? null) : null;

export const unreachableReason = (label: string | undefined) =>
  label ? (UNREACHABLE[label] ?? null) : null;
