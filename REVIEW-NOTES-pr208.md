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

One inconsistency, now **FIXED** by hand (see the type-scale sweep below): all
six used `Mobile/Paragraph/P2` (16 Regular). Correct on mobile; on tablet it
should be `Desktop/Paragraph/P1` (16 Medium) — `7601:30613`, `7601:30618`,
`7601:30622`. The plugin has no font-weight or text-style setter, so this could
not be scripted.

Why: the file has no tablet text styles, and the tablet frames use `Desktop/*`
styles for *every* text node — heading `Desktop/Heading/H1`, labels
`Desktop/Heading/H3`, placeholders `Desktop/Paragraph/P1`, criteria
`Desktop/Paragraph/P2`. The clearest precedent is "Return to Log in": the same
16px paragraph role, already `Desktop/Paragraph/P1` on tablet where mobile has
`Mobile/Paragraph/P2`. This matches the note in `index.css` attributing to
design (Gurman/Fehin, 2026-06) that tablet uses the desktop type scale and
only 0–499px uses the mobile scale, and it is what `Wrapper.tsx` renders via
`text-m-p2 tablet:font-medium`.

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

Tracked as its own task (spawned 2026-07-26) rather than piled onto #208,
since it is a backend concern that predates this PR: add limiting to
`/forgot-password`, `/login` and the reset/registration routes, per-IP and
per-email, 429 + `Retry-After`, keeping the non-enumerating 204 response. Pick
storage based on how many replicas actually run.

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

## Type-scale sweep (2026-07-26)

The tablet subtitle issue is systemic, not limited to the three added
subheaders. In **Tablet - Log In**, ten text nodes sit on
`Mobile/Paragraph/P2` and should be `Desktop/Paragraph/P1` (16 Medium):

`4438:35378`, `4438:35436`, `4438:35535` (login subtitles) ·
`4438:35455` (Account Created) · `4438:35467`, `4438:35481`, `4438:35495`
(link-sent confirmations) · `7601:30613`, `7601:30618`, `7601:30622`
(create-password subheaders)

None are inside component instances, so a style can be applied directly. The
supporting evidence is that "Return to Log in" on those same frames is already
`Desktop/Paragraph/P1`, and the code gives the subtitle and that footer link
the identical class (`text-m-p2 tablet:font-medium`) — so the design treats
them differently where the implementation does not.

Applied by Colin 2026-07-26 and verified via the REST API: all ten are
`fontWeight` 500 and *bound* to the shared `Desktop/Paragraph/P1` style rather
than carrying a hand-typed weight, so later edits to the style will propagate.
Fills still `#1c1b1f`, widths unchanged. **Tablet - Log In is now clean: 125
text nodes, zero on `Mobile/*`.**

Fehin (2026-06-10) confirms the intent: "the tablet login screens should
definitely use desktop heading sizes and not the mobile ones."

### The drivers screens have the same drift — and it is not deliberate

I first read the drivers sections' mobile styling as intentional. That was
wrong. Counting bound styles per section:

| Section | `Mobile/*` text nodes | of total |
|---|---|---|
| Mobile - Drivers | 505 | 778 |
| Tablet - Drivers | 123 | 360 |
| **Desktop - Drivers** | **139** | 509 |

Desktop is contaminated just as badly as tablet. A deliberate "tablet uses the
mobile scale" decision would have left desktop clean, so this is drift of the
same kind Fehin apologised for, not a choice. Grouped by what contains them:

| Group | Tablet | Desktop | Fix |
|---|---|---|---|
| Loose nodes, not in any instance | 67 | 80 | direct style application |
| Inside the **"Address Mobile"** component | 56 | 50 | needs a non-mobile variant |
| Inside "Announcement Board" | — | 9 | component fix |

The instance halves are the real work: a component *named* `Address Mobile` is
being placed on tablet and desktop frames. Overriding text styles on those
instances only sprays overrides that the next component update will fight, so
it wants a desktop variant. Designer's call, and out of scope for #208.

Also noted while counting: 50 tablet / 81 desktop / 187 mobile text nodes are
bound to no style at all. Unrelated to this issue, but it means the drivers
designs are not a reliable source for type until it is cleaned up.

Consequently `index.css` is **correct** as written — tablet does use the
desktop scale, and the drivers designs are the thing that disagrees. No code
change; `Wrapper.tsx`'s `text-m-p2 tablet:font-medium` stands.

#### What was fixed (2026-07-26), and the rule used

Only where a desktop style exists at the **same font size**, so that no node is
resized and nothing can reflow:

| From | To | Nodes |
|---|---|---|
| `Mobile/Paragraph/P2` 16 Regular lh24 | `Desktop/Paragraph/P1` 16 Medium lh24 | 35 |
| `Mobile/Paragraph/P3` 14 Regular lh18 | `Desktop/Paragraph/P2` 14 SemiBold lh18 | 0 — skipped |

Confidence came from the sections contradicting themselves rather than from the
ramp alone: the *same string in the same role* is bound both ways within one
section — `eric.baker@gmail.com`, `519 349 5094`, `Oct 18`, `8:00AM`, `Edit`,
`Delete`, `Starts in 15h 30m` each appear as `Desktop/Paragraph/P1` in one
frame and `Mobile/Paragraph/P2` in another. That is copy-paste drift.

The two `Mobile/Paragraph/P3` dates (`3560:24152`, `3560:24328`) were skipped
as not worth the churn. Note they are *not* flagged hidden — `visible=true`,
no hidden ancestor — so they do render, 14px Regular where the ramp says
SemiBold.

Verified after: 35/35 bound to `Desktop/Paragraph/P1` at 16px lh24, **0 height
changes** (nothing rewrapped), 14 boxes 1px wider from Medium glyphs and 4
right-aligned countdowns shifted 1px.

#### Still broken in the drivers designs — blocks implementing those screens

- **110 loose nodes on an 18px style the desktop ramp does not have.**
  `Mobile/Paragraph/P1` (18 Regular): 38 tablet, 50 desktop.
  `Mobile/Heading/H3` (18 Bold): 12 tablet, 10 desktop. Desktop jumps 16 → 20,
  so every one of these is a *resize* decision, and it differs per element
  (body copy probably 16, section headings probably 20). Not guessable at 110
  nodes' scale.
- **106 nodes inside a component named `Address Mobile`** placed on the tablet
  and desktop frames (56 + 50). Wants a non-mobile variant; per-instance
  overrides would fight the next component update. Plus 9 in
  "Announcement Board".
- **131 text nodes bound to no style at all** (50 tablet, 81 desktop).
- Unresolved even among the fixed nodes: the `Oct 18` / `8:00AM` pairs went to
  P1 by the same-size rule, but the sibling precedent disagrees across
  sections — tablet's correct copy is `Desktop/Paragraph/P1` (16px), desktop's
  is `Desktop/Paragraph/P2` (14px). If dates are meant to be 14px that is a
  resize, so it was left alone.

Clean, no action needed: Error Pages and Route Generation (desktop-only),
Email Templates (different medium).

**Correction (2026-07-26):** I originally recorded the Mobile sections as clean,
excusing their `Desktop/Paragraph/P2` nodes on the grounds that the mobile scale
has no 14px SemiBold. That is an explanation of the symptom, not evidence of
intent, and it was wrong to dismiss. The reverse drift is real — 43 nodes on
**Mobile - Log In** and 9 on **Mobile - Drivers Screens** use `Desktop/*`
styles. See finding 9: almost all of it comes from shared components authored on
the desktop scale, so it is a component-library problem rather than 52 stray
nodes.

## Hazard: stale duplicates on the Hi-fi page

Every fix in this document was made on the **🌟 Finalized** page. The
**🟢 Hi-fi** page carries its own "Desktop / Mobile / Tablet - Log In"
sections with the pre-fix copy — "Password must be:" with five bullets, the
Email field, "Create Password", "Confirm Password", the old forgot-password
subheader. Anyone implementing from Hi-fi will build the old design. Point
reviewers at Finalized, and consider moving Hi-fi to 🗑️ Archive.

(The Figma plugin can only read and write the current page, which is why the
REST fetch script pins to `/finalized/i` — and why none of these edits could
have landed on the wrong page.)

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

## Measured against the design: mobile create-password (2026-07-26)

Overlay harness + Figma node geometry, both in design pixels. Frame
`4438:35155` (375×821) vs the running app.

| Element | Design y | Code y | Design type | Code type |
|---|---|---|---|---|
| logo | 20 (111×28) | 20 | — | — |
| `h1` "Create a password" | **154** | **64** | 24 Bold | 24 700 ✓ |
| subheader | 186 | 96 | 16 Regular | 16 400 ✓ |
| label "Enter new password" | 234 | 152 | 18 Bold | 18 700 ✓ |
| "Password must include:" | 434 | 344 | **14 SemiBold** | **16 600** ✗ |
| first criterion | 454 | 371 | **14 SemiBold** | **16 600** ✗ |
| submit button | 588 | 524 | 16 Medium | 16 500 ✓ |

Left edge is 20px in both, and every font size matches except the criteria.

### 8. Mobile create-password sits ~90px too high — caused by finding 3

The design keeps the space where the illustration would be: nothing but the
logo occupies its top 154px (verified — the only node above the heading is
`image 58`, the 111×28 logo at y=20). Removing the graphic in code collapsed
that space entirely, so the heading rides up to y=64.

So finding 3 was right that the graphic goes, but incomplete: it dropped the
spacing too. The design's mobile heading positions are 154 (create-password,
no illustration), 300 (login), 376 (forgot password and the confirmations) —
three distinct values, so this is per-screen spacing rather than one rule.

Worth checking as part of the walkthrough: the code's illustration screens
compute to ~300 (64 top padding + 212 illustration + 24 margin), which matches
the design's login frames but is 76px short of the 376 the forgot-password
family uses. Not verified against the running app yet — design side only.

### 9. Password criteria: 16px in code, 14px in the design — but the design is not authoritative here

`text-p2` is responsive in `index.css`: `--text-m-p2` (16px) below the tablet
breakpoint, `--text-p2` (14px) from tablet up. So mobile renders 16px where the
mobile design frames show 14px SemiBold.

**Do not "fix" the code to 14px on that basis.** I first read the design's 14px
as a mobile spec, then as a badly-authored component. Both were wrong. The real
cause is an **incomplete per-instance override** on the mobile frames.

The `Password` component's default is entirely desktop, which is right — tablet
uses the desktop scale, and the tablet instances render exactly that. On the
mobile frames, only two of its four texts were overridden:

| Layer | Component default | On the mobile frame | |
|---|---|---|---|
| label | `Desktop/Heading/H3` 16 Bold | `Mobile/Heading/H3` 18 Bold | overridden |
| placeholder | `Desktop/Paragraph/P1` 16 Medium | `Mobile/Paragraph/P2` 16 Regular | overridden |
| required `*` | `Desktop/Heading/H3` 16 Bold | unchanged | **missed** |
| helper text | `Desktop/Paragraph/P2` 14 SemiBold | unchanged | **missed** |

`Status Message` — the four criteria — was never overridden at all, which is why
all 12 of its nodes show desktop styles, and the three loose "Password must
include:" headings (`4438:35165`, `4438:35204`, `4438:35223`) were styled to
match what it renders. Totals on **Mobile - Log In**: `Password` 18,
`Text Field` 10, `Status Message` 12, loose 3.

So the 14px is a desktop default leaking through, not a mobile decision — and
the override cannot simply be completed, because the mobile ramp has no
equivalents: no 14px SemiBold for the helper text and criteria (P3 is 14
Regular), and no 16px Bold for the asterisk (Mobile/Heading/H3 is 18 Bold).

**Leave the code as it is.** At 16px SemiBold the criteria are arguably closer
to the mobile scale than the design is — 16px is `Mobile/Paragraph/P2`'s size —
and the label at 18px Bold already matches the one text that *was* overridden.
Changing to 14px would chase an artifact.

### 8b. FIXED — mobile create-password now lands on the design

After the `pt-[154px]` change, measured at 375px against frame `4438:35155`:
h1 154 (Δ0), subheader 186 (Δ0), criteria heading 434 (Δ0), first criterion 455
(Δ+1), submit 584 (Δ−4). `/login` unmoved at 300, matching its own frame.

### 9b. FIXED — criteria and error text now 14px at every width

`fieldNote` in `CreatePasswordForm` is `text-m-p3 font-normal
tablet:font-semibold`: constant 14px/18px, Regular on mobile
(`Mobile/Paragraph/P3`) and SemiBold from tablet up (`Desktop/Paragraph/P2`) —
each ramp's own weight at 14px, per the mapping Colin approved.

My first attempt was `text-p3 tablet:text-p2`, which the repo's own ESLint rule
rejected: the `text-p1..p3` utilities carry their own internal breakpoint, so a
`tablet:` variant does not compose and the inner media query wins. The rule
names the fix — a static `text-m-*` for a constant size. Verified 14px/18px with
weight 400 at 375px and 600 at 834px and 1440px.

### 11. Wrapper gap is wrong at tablet on every screen

The design's wrapper→form spacing, read off the frames' auto-layout
`itemSpacing`, is per screen family. `Wrapper` hardcodes `gap-8 tablet:gap-4`:

| Family | Design mobile | Design tablet | Code mobile | Code tablet |
|---|---|---|---|---|
| create-password | 24 | 32 | 32 (**+8**) | 16 (**−16**) |
| login | 32 | 32 | 32 ✓ | 16 (**−16**) |
| forgot / confirmations | 16 | 16 | 16 ✓ | 16 ✓ |

The forgot family only lands right because `ForgotPassword` passes `gap-4`.
`tablet:gap-4` is wrong wherever the design says 32, and the Account Created
confirmation wants 16/16 but inherits the wrapper's 32.

Fixing it properly means: base `tablet:gap-8`; `gap-6` on the password-entry
screens; `tablet:gap-4` added to `ForgotPassword` so it stays at 16; and a
gap for `CreatePassword`'s CONFIRMATION step. Not done — see finding 12, since
it is the same shared-spacing question.

### 12. Heading position on the forgot/confirmation family is 16–76px short

Measured at 375px: `/forgot-password` h1 at 360 against the design's 376, and
Account Created computes to 300 against 376. Only `/login` (300) and
create-password (154, now fixed) match. `ForgotPassword` already hand-tunes its
own `pt-31`, so the per-screen-padding convention exists — these two just have
the wrong numbers.

### 10. Nits found while measuring

- The two "Driver | Create Password Filled" mobile frames disagree with each
  other: heading at 154 in one, 126 in the other.
- The design's button reads "Create Account"; the code says "Create account".
  The flow is sentence case throughout (see finding 7), so the code is right
  and the Figma button wants changing — but it is inside a `UI/Button`
  component instance, so it needs care.

## Screens still to walk

Four routes, checked at mobile (375) / tablet (834) / desktop (1440):

- `/login` — default, filled, credential error, "Get your login link"
- `/forgot-password` — FORM, CONFIRMATION + countdown
- `/forgot-password/:token` — validating, invalid token, form, submit error
- `/create-password/:token` — bad UUID, FORM, CONFIRMATION

`CreatePasswordForm` is shared by the last two; its empty / criteria-not-met /
passwords-don't-match states need checking from both entry points.
