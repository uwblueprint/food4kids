# PR #208 — Create / Forgot Password: review notes

Scratchpad for findings to turn into GitHub review comments. Lives on the
overlay branch (never merged), alongside the design-overlay tooling.

PR: https://github.com/uwblueprint/food4kids/pull/208
Head at time of review: `cf8beabf`

## Findings

### 1. Resend cooldown is 60s; the design says 10s

`frontend/src/pages/auth/ForgotPassword.tsx` — `ResetLinkConfirmation` starts
`useState(60)` and resets to `60` after a resend, rendering
`Send again in {countdown} seconds`.

The Figma "Developer Notes" frame *Link send cooldown* (desktop section,
node `4438:35103`) says:

> After 10 seconds, the button will tick down from a 10 second timer until
> they can resend the link.

Confirm which is intended before commenting — 60s may be a deliberate
anti-abuse choice, but it does not match the spec as written.

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

## Still open in Figma

- **Create-password subheader.** Desktop and the code have "Create an account
  to access the app" under the heading; mobile and tablet have no subheader at
  all. Not added: the frames are auto-layout, and the plugin's `create_text`
  appends as the last child with no way to reorder, so a new node lands at the
  bottom of the form rather than under the heading. `clone_node` can't
  reparent either. Needs a designer to add it by hand.
- Nit, not raised: mobile/tablet label reads "Confirm Password"; desktop and
  the code use "Confirm password".

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
