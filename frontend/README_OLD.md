# Frontend — Next.js + Tailwind (planned)

This README describes the planned frontend architecture, pages, components, and environment variables.

## Tech stack
- Next.js (TypeScript recommended)
- Tailwind CSS for styling
- GSAP and Framer Motion for animations
- Fetch to backend API (no server-side payments)

## Pages (minimal)
- `/` — Home / search form
- `/search` — Search results list
- `/train/[number]` — Train details and route
- `/train/[number]/book` — Seat selection and passenger form
- `/booking/[booking_id]` — Booking confirmation
- `/account` — Profile & booking history
- `/admin/import` — Admin import and data tools (protected)

## Environment variables
- NEXT_PUBLIC_API_URL=http://localhost:8000

## Dev commands (to add to `frontend/package.json`)
```
# install deps
npm install
# dev server
npm run dev
# build
npm run build
# start
npm run start
```

## Notes
- The frontend should implement client-side validation (email format, password length), friendly error messages, and UX for seat selection.
- All data-modifying actions go through the backend API.

Design & Theming
- Themes: support Light / Dark / System preferences using Tailwind `darkMode: 'class'` or `next-themes` for Next.js. Persist choice in `localStorage`.
- Aesthetic: minimal layout with colorful accents (two primary accent colors), generous spacing, and clear typographic hierarchy.
- Animations: use Framer Motion for page and component transitions; use GSAP for advanced timeline/seat map animations. Respect `prefers-reduced-motion`.

ASCII Background
- Include the ASCII bullet-train texture in `public/assets/ascii_bullet_train.txt` and render it as a low-opacity, blurred `<pre>` behind main content. Show it on larger screens and hide or reduce on small screens.

See `docs/FRONTEND_DESIGN.md` for detailed color tokens, Tailwind snippets, animation guidance, and implementation patterns.
