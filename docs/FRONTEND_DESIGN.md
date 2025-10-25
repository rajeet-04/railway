# Frontend Design Guide — Themes, Animations, and Aesthetic

Goal: create a minimalistic, colorful, and aesthetic UI with strong animations while keeping accessibility and clarity. Support dark/light/system themes and a stylized ASCII bullet-train background that remains subtle.

Core principles
- Minimal layout: concise cards, clear typographic hierarchy, spacing, and focused color accents.
- Colorful but restrained palette: choose 2–3 accent colors with high contrast on both light and dark backgrounds.
- Motion for affordance: animations should guide the user, not distract—use Framer Motion for component transitions and GSAP for more advanced timeline animations.
- Accessibility: ensure contrast ratios, focus states, reduced-motion support, and aria labels.

Theme strategy
- Use Tailwind CSS with `darkMode: 'class'` to control dark/light themes via a `class` on `html` or `body`. Allow system preference by defaulting to `media` or detecting prefers-color-scheme in JS.
- Provide a small theme toggle in the header that cycles: Light / Dark / System.
- Store user preference in `localStorage` and reflect on initial render to avoid flash.
- Use CSS variables for colors to simplify theme inversion for custom styles and animations.

Tailwind snippet (tailwind.config.js)
```js
module.exports = {
  darkMode: 'class', // use class-based dark mode
  theme: {
    extend: {
      colors: {
        accent: {
          50: '#f5f7ff',
          100: '#e6eeff',
          300: '#8fb0ff',
          500: '#3f51ff', // primary accent
          700: '#2a3bbf'
        },
        accent2: {
          300: '#ffb3c1',
          500: '#ff4d6d'
        }
      }
    }
  }
}
```

Design tokens and palette
- Backgrounds: neutral light/dark surfaces.
- Primary accent: cool electric blue (`accent.500`) for main CTA and highlights.
- Secondary accent: coral/pink (`accent2.500`) for status and small accents.
- Neutrals: use Tailwind `gray-50` to `gray-900` for text and surfaces.

Typography & spacing
- Use a clean sans-serif (Inter, Poppins). Large headings (32–44px), medium subheads (18–24px), body 16px.
- Generous spacing: base spacing `1rem` and multiples for cards and gaps.

Animations
- Use Framer Motion for page transitions and small component animations (fade, slide, scale). Use GSAP for complex seat map or timeline animations where you need fine-grained control.
- Respect `prefers-reduced-motion`—if set, disable non-essential animations.

Example Framer Motion usage (motion.div)
- Page transitions: fade + slight upward motion on enter, reverse on exit.
- Buttons: micro-interactions (scale 1.03 on hover, quick 120ms).
- Seat selection: gentle pop + color fill when selected.

ASCII bullet-train background
- The background is a large monospaced ASCII art of a bullet train. To keep it subtle and aesthetic:
  - Render it in a `<pre>` or as a background `<div>` with `font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', monospace;`.
  - Apply low opacity (e.g., 6–10%) and a large blur using CSS `filter: blur(1px)` to make it a texture rather than content.
  - Use CSS `mix-blend-mode: overlay` or `color` adjustments to make it fit both dark and light modes.
  - Optionally animate slow horizontal parallax on scroll for depth (use `transform: translateX()` with small amplitude via GSAP).

Implementation pattern for ASCII background
- Add asset at `public/assets/ascii_bullet_train.txt` (provided) or inline text in a React component.
- Example HTML structure:
  ```jsx
  <div className="absolute inset-0 pointer-events-none -z-10 flex items-center justify-center">
    <pre className="ascii-bg opacity-10 text-[8px] leading-[6px] select-none whitespace-pre-wrap">{asciiText}</pre>
  </div>
  ```
- CSS (Tailwind + custom):
  ```css
  .ascii-bg {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', monospace;
    color: rgba(var(--accent-rgb), 0.06); /* use CSS var for accent color */
    filter: blur(0.5px);
    white-space: pre-wrap;
    transform: translateZ(0);
    user-select: none;
  }
  ```
- For responsive behavior, show more of the ASCII art on large screens and reduce or hide on small screens.

UI components & layout suggestions
- Header: logo, search box (station autocomplete), theme toggle, login button.
- Search results: cards with train info, times, available seats, quick book CTA.
- Train detail: route timeline as compact vertical list with animated arrival/departure markers.
- Seat map modal: grid of seats; selecting a seat triggers motion and color fill. Use SVG overlays for coaches if desired.
- Booking confirmation: show a colorful ticket card with booking ID, passenger names, train info, and a QR-like code (stylized).

Accessibility & performance
- Ensure buttons and interactive elements have focus outlines (customizable via Tailwind `ring` utilities).
- Lazy-load heavy assets and the ASCII background on large screens only to reduce initial paint cost.
- Provide a reduce-motion toggle or honor system preference.

Developer tips
- Use `next-themes` library for theme management in Next.js (works well with Tailwind `dark` class).
- Use Framer Motion's `<AnimatePresence>` for page-level animations.
- Keep animations short (80–300ms) and use easing curves that feel natural (cubic-bezier or `easeOut` presets).

Example color variables (light/dark via CSS variables)
```css
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --text: #0f172a;
  --accent-rgb: 63,81,255; /* accent.500 */
}
.dark {
  --bg: #0b1220;
  --surface: #071026;
  --text: #e6eefc;
  --accent-rgb: 100,120,255;
}
```

Final note
- The goal is colorful yet minimal. Keep layout simple, emphasize motion for clarity, and use the ASCII background as a textured brand element rather than readable content.

Use `frontend/README.md` for quick start and integrate this guide when implementing UI components.
