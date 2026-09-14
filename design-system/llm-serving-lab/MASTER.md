# LLM Serving Lab — Master Design System

## Direction

**Metro Operations Desk.** Serving is presented as a visible network, not a
generic chat dashboard. The interface combines a route-first control room with
a progressively disclosed teaching instrument: choose a strategy, dispatch a
request, watch its actual stages, then inspect measured output and the deeper
computational model.

## Palette

| Role | Value | Use |
|---|---:|---|
| Canvas | `#070A0D` | page background and dark text on route actions |
| Surface | `#0B1016` | panels and compute modules |
| Surface hover | `#141C25` | navigation hover |
| Field hover | `#485769` | editable-field hover outline |
| Network line | `#25303B` | structural dividers and borders |
| Strong network line | `#374554` | fields, stations, arrows, tensor frames |
| Primary ink | `#EDF3F8` | titles and generated output |
| Muted ink | `#98A6B7` | explanatory copy |
| Quiet ink | `#7F8DA0` | machine metadata |
| Danger | `#FB7185` | errors only |

| Strategy | Route color |
|---|---:|
| Realtime | `#22D3EE` |
| Offline batch | `#4ADE80` |
| Continuous batch | `#FBBF24` |
| Streaming | `#60A5FA` |

Only the selected strategy color carries active navigation, dispatch, focus,
trace, mechanics, and result state. Saturated color must have operational
meaning; it is never ambient decoration.

## Typography

- **Onest:** mode display `clamp(30px, 3.6vw, 52px)` at 700/0.98; mechanics
  title 17px; panel title 15px (14px compact); body 14px; supporting copy 12px.
- **JetBrains Mono:** mechanics labels and formulae 11px; ordinary machine labels
  10px; dense station and flow metadata 9px.
- Use Onest for concepts and generated language. Use mono for endpoints, tensor
  shapes, queue windows, timing, state, shortcuts, and event records.

## Geometry and rhythm

- Radius scale: tensor cells 1px; lanes 2px; tokens/slots 3px; chips 4px;
  tensor/queue frames 5px; compact controls 6px; inputs/actions 7px; navigation
  8px; compute modules and narrow-screen panels 9px; primary panels 12px;
  stations/signals 50%.
- Desktop rail: 244px. Work area: maximum 1540px.
- Standard panel gap: 14px. Standard panel padding: 20px; dominant trace and
  experiment use 22–24px; mechanics board uses 26px desktop and 18px mobile.
- At 1180px the desk becomes two columns; at 840px navigation moves to a top
  rail and the desk becomes one column; at 620px route and compute flow become
  vertical.

## Core components

- **Strategy navigation:** 58px desktop rows with route dot, mode title,
  mechanism label, translucent active wash, and 2px active marker. Mobile rows
  are 48px and horizontally scroll.
- **Request route:** Client → Queue → Model → Response stations with neutral,
  active, and done states. One or four 5px payload cells reflect actual request
  count; real stage events synchronize the expanded mechanics step.
- **Experiment controls:** near-black fields, strong border, 7px radius, explicit
  `#485769` hover stroke, route-colored focus, and 50px dispatch action.
- **Telemetry:** border-separated instrument readouts are measured truth. Event
  rows use monospaced time and never receive values from the teaching animation.
- **Panels:** flat `#0B1016` surfaces with 1px network border and no decorative
  shadow stack.

## Mechanics Explorer

“Как это работает” is a 52px progressive-disclosure row inside the request
route panel. Collapsed state retains a concise mode-specific formula. Expanded
state adds interactive button modules, one step readout, a replay action, and
explicit educational/runtime notes.

The four strategies use finite, inspectable representations:

1. **Realtime:** separate tokens/tensors, serial model lanes, four calls, four
   whole JSON responses.
2. **Offline batch:** known prompts, one wide tensor, shared GPU/GEMM work, and a
   completed job collected by polling.
3. **Continuous batch:** HTTP arrivals, bounded async queue/wait window,
   activations `[N×T×H]` / GPU batch `[N×T]`, and output-to-Future mapping.
4. **Streaming:** six stages expose prompt tokens, prefill K/V writes, the new
   Q/K/V projection, attention reads, cache append, and SSE delivery before
   `done`.

Each module is a real keyboard-operable button with `aria-pressed`; selecting a
module cancels replay and holds that finite state. Replay starts at step one,
waits 850ms there and 1100ms on later steps. Collapse, mode change, a new actual
run, manual selection, or document hiding cancels stale playback. During real
requests, Client/Queue/Model/Response events drive steps directly.

The board is explicitly an educational visualization: tensor shapes are
simplified and motion time is stretched. Actual latency, queue, inference,
batch size, and CPU/CUDA identity live only in telemetry and the runtime note.

## Motion

- Navigation state: 160ms ease.
- Disclosure: 220ms `cubic-bezier(.16, 1, .3, 1)`; explorer reveal: 360ms with
  the same curve.
- Compute module state: opacity 260ms ease and transform 420ms spring-like curve.
- Flow packet: 700ms; payload cells: 600ms with 90ms stagger.
- Tokens/tensor: 520ms ease-out; GPU array: 560ms with 80ms stagger; queue slots:
  540ms with 110ms stagger; SSE chunks: 420ms with 140ms stagger; serial lanes:
  450ms with 160ms stagger.
- Actual route signal: 1.6s linear; active station: 900ms alternate; real stream
  cursor: 650ms step-end.
- Under `prefers-reduced-motion`, duration becomes effectively instant and all
  modules/links render at opacity 1 with no transform. The final state must be
  understandable without animation.

## Guardrails

- Keep the request path above controls and telemetry at every viewport.
- Keep deep mechanics collapsed until explicitly requested.
- On mobile, stack modules and links vertically; never clip or squeeze them.
- Never present visual timing, simplified geometry, or capped payload markers as
  measured data.
- Do not use light dashboard surfaces, purple AI gradients, glassmorphism,
  ornamental charts, invented metrics, broad glow, emoji icons, hidden focus,
  or hover layout shifts.
