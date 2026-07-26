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

Asking because both sections currently mix the two, and it looks accidental
rather than chosen: the *same string in the same role* is bound one way in one
frame and the other way in a neighbouring frame — `eric.baker@gmail.com`,
`519 349 5094`, `Oct 18`, `8:00AM`, `Edit`, `Delete`, `Starts in 15h 30m` each
appear as both `Desktop/Paragraph/P1` and `Mobile/Paragraph/P2`.

If yes, we've already converted the 37 nodes where a desktop style exists at the
identical font size (so nothing resized or re-wrapped). Everything below is what
we couldn't decide without you.

**2. There's no 18px step in the desktop scale. What should the 18px text
become — or should an 18px desktop style be added?**

139 nodes sit on 18px mobile styles: `Mobile/Paragraph/P1` (18 Regular, 117
nodes) and `Mobile/Heading/H3` (18 Bold, 22). The desktop scale jumps straight
from 16 to 20:

| | 16px | 18px | 20px |
|---|---|---|---|
| Headings | Desktop/Heading/H3 (Bold) | — | Desktop/Heading/H2 (Bold) |
| Paragraphs | Desktop/Paragraph/P1 (Medium) | — | — |

So each of these is a resize, which changes layout — hence not something we
want to pick. Our guess would be body copy → 16 and section headings → 20, but
if 18px is deliberate on the bigger breakpoints, adding the style is cleaner.

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

**Also, small:** dates are inconsistent — `Oct 18` / `8:00AM` use
`Desktop/Paragraph/P1` (16px) on the tablet frames but `Desktop/Paragraph/P2`
(14px) on the desktop ones. Which is right? And the **Mobile - Drivers**
section has 9 nodes on `Desktop/*` styles (the reverse drift) — presumably
those should be mobile.

---

Happy to make the changes ourselves once you've decided — we just need the
calls on 2, 3 and 4.
