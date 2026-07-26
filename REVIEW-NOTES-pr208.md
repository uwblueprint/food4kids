# PR #208 — Create / Forgot Password: review notes

Scratchpad for findings to turn into GitHub review comments. Lives on the
overlay branch (never merged), alongside the design-overlay tooling.

PR: https://github.com/uwblueprint/food4kids/pull/208
Head at time of review: `cf8beabf`

## Findings

### 0. Subheader added by hand — one weight fix left

Colin added the six create-password subheaders (2026-07-26). Geometry checks
out: heading→subheader gap 0px in all six, matching desktop; wrapper→form gap
24px on all three mobile frames and 32px on all three tablet frames; x aligned
to the heading; 16px/24 line-height, `#1c1b1f` throughout.

One inconsistency: all six are **Nunito Sans Regular (400)**. Per
`Wrapper.tsx` (`text-m-p2 tablet:font-medium`) and the ramp note in
`index.css`, the subtitle is Regular on mobile but **Medium (500) from tablet
up** — and desktop's subheader is Medium. So the three mobile ones are right;
the three tablet ones should be Medium: `7601:30613`, `7601:30618`,
`7601:30622`. No font-weight setter exists in the plugin, so this needs doing
by hand.

Not cross-checked: desktop's wrapper is the last child of its parent, so
there is no desktop wrapper→form gap to compare the 24/32px against.

### 1. Resend cooldown is 60s; the design says 10s

`frontend/src/pages/auth/ForgotPassword.tsx` — `ResetLinkConfirmation` starts
`useState(60)` and resets to `60` after a resend, rendering
`Send again in {countdown} seconds`.

The Figma "Developer Notes" frame *Link send cooldown* (desktop section,
node `4438:35103`) says:

> After 10 seconds, the button will tick down from a 10 second timer until
> they can resend the link.

**Recommendation: keep 60s in code, change the design note.** 30–60s is the
usual convention for email resend cooldowns. 10s is short enough that the
first email often hasn't arrived yet, so it invites a second click that
produces nothing new for the user and doubles the send volume — which matters
here, given the project's cost constraints.

Good news on one related worry: `PasswordResetTokenService.create` deletes any
existing token for the user before inserting, so resending doesn't leave
multiple live reset tokens.

**The real gap is server-side.** The countdown is client state only
(`useState(60)` in the component), so it does nothing against direct calls to
`POST /forgot-password`. There is no rate limiting anywhere in
`backend/python/app/` — no slowapi, no limiter, no throttling. With a known
address, that endpoint can be used to mail-bomb a volunteer and to burn email
quota. Worth raising as its own review point, independent of the timer value.

### 2. Password-criteria copy — FIXED (code + Figma)

Designer confirmed the desktop wording wins. Mobile/tablet Figma said
"Password must be:" with five verbose bullets; desktop said "Password must
include:" with four. Code had the desktop bullets under the mobile heading.

- Code: heading → "Password must include:"; first bullet "(12 or more is
  recommended)" → "(12 or more is better)".
- Figma: "Driver | Create Password" reworded to the desktop copy on mobile
  (`4438:35155`) and tablet (`4438:35352`), and the separate lowercase bullet
  deleted so both list four items.

The four "Create Password Filled" state frames (mobile `4438:35194`,
`4438:35214`; tablet `4438:35391`, `4438:35411`) took the desktop wording too.
Each showed uppercase satisfied but lowercase not, which the merged bullet
can't express, so the merged row inherits the *unmet* styling — done by
deleting the satisfied (green) row and keeping the unmet (black) one, then
retexting it. Number and special-character stay green. Net effect: the
colouring still reads "not all criteria met", which is what those frames are
demonstrating.

### 4. Email field on mobile create-password — FIXED (Figma)

Mobile and tablet "Driver | Create Password" had an Email field above the
password fields. The flow identifies the user by the invite token in the URL,
so it is not functionally needed, and desktop omits it. Deleted from mobile
`4438:35155`/`4438:35194` and tablet `4438:35352`/`4438:35391` (the "(2)"
variants never had one). No code change — the implementation never had it.

### 5. Forgot-password subheader — FIXED (Figma)

Desktop (`4438:35026`) already read "What email did your admin use to sign you
up?", matching the code. Mobile (`4438:35325`) and tablet (`4438:35522`) had a
longer variant; both now match desktop and the code.

### 3. Create-password mobile graphic — FIXED (code)

`WrapperWithLogo` rendered the mobile illustration on every auth screen. The
designs drop it only on the password-entry forms (login, forgot password, and
the Account Created confirmation all keep it). Added
`showMobileIllustration` (default true); `CreatePassword` passes
`step === 'CONFIRMATION'` and `ResetPassword` passes `false`.

### 6. Screen headings — FIXED (Figma)

- Create-password heading: mobile/tablet "Create Password" → "Create a
  password", matching desktop and the code. Six frames: `4438:35157`,
  `35196`, `35216` (mobile); `35354`, `35393`, `35413` (tablet).
- Forgot-password heading: here *desktop* was the outlier, so `4438:35025`
  "Forgot password" → "Forgot password?", matching mobile/tablet and the code.

### 7. "Confirm password" casing — FIXED (Figma)

The flow is sentence case throughout ("Enter new password"; desktop is 6/6
"Confirm password"). Mobile and tablet had five "Confirm Password" outliers,
now normalised: `I4438:35163;2941:20669`, `I4438:35202;2941:20669` (mobile);
`I4438:35360;2941:20669`, `I4438:35399;2941:20669`,
`I4438:35418;2941:25244` (tablet).

## Still open in Figma

- **Create-password subheader.** Desktop and the code have "Create an account
  to access the app" under the heading; mobile and tablet have no subheader at
  all. Tested rather than assumed: `create_text` with the correct coordinates
  and `parentId` landed the node *below the Create Account button*, because
  the frame is auto-layout and appends children in order. There is no reorder
  tool, `clone_node` cannot reparent, and `create_text` has no font-family
  option (so it would not be Nunito Sans anyway). The test node was deleted.
  Converting the frame's auto-layout off and back on would reorder by
  position but would drop its spacing and padding settings, which is a worse
  outcome than a missing subheader. Needs to be added by hand.

  Text: "Create an account to access the app". Style, copied from desktop
  node `4438:34895`: Nunito Sans Medium (500), 16px, line-height 24, `#1c1b1f`.
  Insert as the second child of "Frame 241", directly after the heading:

  | Viewport | Frame | Parent | After heading | Before |
  |---|---|---|---|---|
  | Mobile | `4438:35155` | `4438:35156` | `4438:35157` | `4438:35158` |
  | Mobile | `4438:35194` | `4438:35195` | `4438:35196` | `4438:35197` |
  | Mobile | `4438:35214` | `4438:35215` | `4438:35216` | `4438:35217` |
  | Tablet | `4438:35352` | `4438:35353` | `4438:35354` | `4438:35355` |
  | Tablet | `4438:35391` | `4438:35392` | `4438:35393` | `4438:35394` |
  | Tablet | `4438:35411` | `4438:35412` | `4438:35413` | `4438:35414` |

- **"Didn't get a link?" subheader wording** — a copy decision, not a
  mismatch to mechanically resolve. Desktop (`4438:34882`) ends "We'll send a
  new **login** link"; mobile (`4438:35312`) and tablet (`4438:35509`) end
  "a new **setup** link". "Login link" matches the CTA on the login screen
  that leads here; "setup link" better describes a first-time driver's invite.
  Out of scope for #208 either way — that screen isn't implemented. Pick one
  and it's a one-line change.

## Verified as matching the design notes

- Password unhide is per-field, not both at once (`showPassword` and
  `showConfirmPassword` are separate) — matches the *Drivers Creating account*
  note.
- The forgot-password confirmation does not reveal whether the account exists
  ("If an account exists for that email…") — matches the *Creation Link Sent*
  note.

## Screens still to walk

Four routes, checked at mobile (375) / tablet (834) / desktop (1440):

- `/login` — default, filled, credential error, "Get your login link"
- `/forgot-password` — FORM, CONFIRMATION + countdown
- `/forgot-password/:token` — validating, invalid token, form, submit error
- `/create-password/:token` — bad UUID, FORM, CONFIRMATION

`CreatePasswordForm` is shared by the last two; its empty / criteria-not-met /
passwords-don't-match states need checking from both entry points.
