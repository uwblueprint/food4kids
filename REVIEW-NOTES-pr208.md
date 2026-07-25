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
