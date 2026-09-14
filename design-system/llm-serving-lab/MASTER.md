# LLM Serving Lab — Design System

## Direction

**Metro operations control room.** The interface treats inference as a visible
route through stations rather than as a generic chat application. The request
path is the primary visual anchor; controls, measured output, and event history
form one compact operating desk below it.

## Visual thesis

- Near-black canvas suited to use beside an IDE and terminal.
- Thin infrastructure lines and circular route stations communicate movement.
- One strategy color at a time identifies the active route.
- Typography is compact and technical, but the main heading remains readable.
- Effects are functional: only a currently active stage pulses.

## Tokens

| Role | Value |
|---|---|
| Canvas | `#070A0D` |
| Surface | `#0B1016` |
| Raised surface | `#0F151D` |
| Border | `#25303B` |
| Strong border | `#374554` |
| Primary text | `#EDF3F8` |
| Secondary text | `#98A6B7` |
| Quiet metadata | `#687789` |
| Error | `#FB7185` |
| Success | `#4ADE80` |

### Route colors

| Strategy | Color | Meaning |
|---|---|---|
| Realtime | `#22D3EE` | direct low-latency request |
| Offline batch | `#4ADE80` | completed background work |
| Continuous batch | `#FBBF24` | short queue/wait window |
| Streaming | `#60A5FA` | flowing response chunks |

## Typography

- Headings/body: **Onest**, fallback Segoe UI.
- Endpoints, metrics, timings, shortcuts: **JetBrains Mono**, fallback Cascadia
  Mono.
- Use uppercase only for small metadata labels, never for paragraphs.

## Layout

- Desktop: 244 px fixed navigation rail, fluid content up to 1540 px.
- Main route spans the page; desk below uses three columns.
- Under 1180 px the desk becomes two columns.
- Under 840 px navigation becomes a horizontal top rail and the desk becomes one
  column.
- At 375 px the route is vertical and skipped stations are removed.

## Components

- Panels use a 1 px border and 9–12 px radius; no decorative shadow stack.
- Inputs use the canvas color inside a bordered surface.
- The primary action uses the active route color and a dark label.
- Metrics are instrument readouts separated by rules, not independent cards.
- Mode navigation uses a route dot, restrained tint, and 2 px active line.

## Interaction

- 150–180 ms hover/focus transitions.
- Current pipeline station has a small pulsing signal.
- Streaming output uses a blinking caret.
- Every click target is at least 40 px; primary and mobile targets are 48 px.
- Visible 2 px focus ring uses the active route color.
- Under `prefers-reduced-motion`, animation and transitions become effectively
  instant.

## Prohibited

- White or light dashboard surfaces.
- Purple AI gradients, glassmorphism, ornamental charts, and fake metrics.
- Excessive glow or every panel competing for attention.
- Emoji icons, hidden focus states, hover layout shifts, or clipped mobile
  content.
