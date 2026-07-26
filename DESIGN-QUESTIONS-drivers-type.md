# Questions for Gurman — type styles on the Drivers screens

Context: while implementing the login screens we found tablet frames using the
mobile type scale. Fehin confirmed (2026-06-10) that the tablet **login**
screens should use the desktop sizes, and those are now fixed. Sweeping the
rest of 🌟 Finalized, the same pattern shows up in the Drivers sections — but
those are yours, so we don't want to touch them on a guess.

All counts are text nodes in **Tablet - Drivers Screen** + **Desktop - Drivers
Screen**, on the 🌟 Finalized page.

---

**1. Should the tablet and desktop Drivers frames use the desktop scale, like
the login screens now do?**

Asking because both sections mix the two in a way that can't be deliberate.
The clearest example — the dashboard header, in two states of the *same* page:

| Element | `Desktop \| 1 route` | `Desktop \| Announcment` |
|---|---|---|
| This Year / Lifetime | 18px Regular `Mobile/Paragraph/P1` | 16px Medium `Desktop/Paragraph/P1` |
| Upcoming / Past | 16px Bold `Desktop/Heading/H3` | 18px `Mobile/Heading/H3` + `Mobile/Paragraph/P1` |

Each frame has half on the desktop scale and half on the mobile scale — and the
halves are **swapped** between the two. That reads as copy-paste between state
frames rather than a choice. It holds across 22 distinct strings in the tablet
section and 11 in the desktop one, including `eric.baker@gmail.com`,
`519 349 5094`, `Oct 18`, `8:00AM`, `Edit`, `Delete`, `Starts in 15h 30m`.

If yes, we've already converted the 37 nodes where a desktop style exists at the
identical font size, so nothing resized or re-wrapped (verified: zero height
changes afterwards).

**2. Can we map the 18px text to 16px — and what should the 18px *headings*
become?**

There is no 18px step in the desktop scale; it jumps 16 → 20. 139 nodes sit on
18px mobile styles. Encouragingly, most have a 16px twin elsewhere in the same
section, so the intent looks readable off the file:

| From | To | Evidence |
|---|---|---|
| `Mobile/Paragraph/P1` 18 Regular | `Desktop/Paragraph/P1` 16 Medium | the same label is 16px on other frames — 26 distinct strings |
| `Mobile/Heading/H3` 18 Bold | **unclear** | maps to `Desktop/Heading/H3` (16) in one place and `Desktop/Heading/H2` (20) in another |

So: confirm the first row and we'll apply it (85 nodes have twins). The ~22
`Mobile/Heading/H3` nodes need your call — 16 or 20, or add an 18px style if
that size is deliberate on the larger breakpoints.

Unlike question 1's fix, this one changes font size and so will reflow layout;
we'd re-measure every frame afterwards and flag anything that re-wraps.

**3. A component named `Address Mobile` is placed on the tablet and desktop
frames (106 nodes). Should there be a non-mobile variant?**

Its text is on mobile styles, so those instances stay mobile-scaled wherever
they're used. We could override each instance, but that fights the next
component update — a variant seems right. Same question for
"Announcement Board" (9 nodes on the desktop frames).

**4. 131 text nodes aren't bound to any type style** (50 tablet, 81 desktop).

Intentional one-offs, or should they be bound? This is the one that most
affects us: unbound text means we can't read the intended size off the style,
so we're guessing from pixel values when we build these screens.

**5. Two panes are stacked on the `Desktop | Announcment` frames.** A
hand-built `Divers Pane` sits underneath the newer `Announcement Board`
component, which covers it exactly — so about 10 text nodes (including two
`Oct 2` dates) are invisible in the render. Safe to delete the hand-built one?

**Also, small:** dates are inconsistent — `Oct 18` / `8:00AM` use
`Desktop/Paragraph/P1` (16px) on the tablet frames but `Desktop/Paragraph/P2`
(14px) on the desktop ones. Which is right? And the **Mobile - Drivers**
section has 9 nodes on `Desktop/*` styles (the reverse drift) — presumably
those should be mobile.

---

## And one for whoever owns the shared form components

This one is the mirror image of question 3, and it is not a drivers-screen
issue — it affects the **mobile** frames of every flow with a text field.

`Password`, `Text Field` and `Status Message` are authored on the desktop type
scale, so instantiating them on a mobile frame puts desktop styles there: 40
text nodes across **Mobile - Log In** (plus 3 loose "Password must include:"
headings), and 9 on **Mobile - Drivers Screens**.

| Component | Nodes on mobile frames | Styles carried over |
|---|---|---|
| `Password` | 18 | `Desktop/Heading/H3`, `Desktop/Paragraph/P2` |
| `Text Field` | 10 | `Desktop/Heading/H3`, `Desktop/Paragraph/P2` |
| `Status Message` | 12 | `Desktop/Paragraph/P2` |

The concrete blocker for us: the password criteria show as 14px SemiBold on the
mobile frames, but that is what the desktop-authored component renders, not a
mobile decision — and the mobile ramp has **no 14px SemiBold** (P3 is 14
Regular, P2 is 16 Regular). Our code currently renders them 16px SemiBold,
which is not a mobile style either. So we need an actual call: what type should
a field's helper text, required asterisk, error message and the password
criteria use at mobile? Mobile variants of these three components would settle
it everywhere at once.

---

Happy to make the changes ourselves once you've decided — we just need the
calls on 2, 3, 4 and this last one.
