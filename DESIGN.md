---
name: LLM Serving Lab
description: A dark metro-operations console that makes model-serving routes and their mechanics observable.
colors:
  route-realtime: "#22d3ee"
  route-batch: "#4ade80"
  route-dynamic: "#fbbf24"
  route-stream: "#60a5fa"
  signal-danger: "#fb7185"
  canvas: "#070a0d"
  surface: "#0b1016"
  surface-hover: "#141c25"
  field-hover: "#485769"
  network-line: "#25303b"
  network-line-strong: "#374554"
  ink: "#edf3f8"
  ink-muted: "#98a6b7"
  ink-quiet: "#7f8da0"
typography:
  display:
    fontFamily: "Onest, Segoe UI, sans-serif"
    fontSize: "clamp(30px, 3.6vw, 52px)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.055em"
  title:
    fontFamily: "Onest, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Onest, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Onest, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  supporting:
    fontFamily: "Onest, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  machine-label:
    fontFamily: "JetBrains Mono, Cascadia Mono, monospace"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0.08em"
  label:
    fontFamily: "JetBrains Mono, Cascadia Mono, monospace"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0.1em"
  micro-label:
    fontFamily: "JetBrains Mono, Cascadia Mono, monospace"
    fontSize: "9px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0.1em"
rounded:
  pixel: "1px"
  lane: "2px"
  token: "3px"
  chip: "4px"
  diagram: "5px"
  compact: "6px"
  control: "7px"
  navigation: "8px"
  mechanics: "9px"
  panel: "12px"
  station: "50%"
spacing:
  hairline: "4px"
  compact: "8px"
  control: "12px"
  panel-gap: "14px"
  section: "20px"
  page: "32px"
components:
  button-dispatch:
    backgroundColor: "{colors.route-realtime}"
    textColor: "{colors.canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
    height: "50px"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.route-realtime}"
    typography: "{typography.machine-label}"
    rounded: "{rounded.control}"
    padding: "6px 4px"
    height: "44px"
  field:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "13px 14px"
  navigation-item:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.navigation}"
    padding: "8px 10px"
    height: "58px"
  navigation-item-active:
    backgroundColor: "rgba(34, 211, 238, 0.11)"
    textColor: "{colors.ink}"
    rounded: "{rounded.navigation}"
    padding: "8px 10px"
    height: "58px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "20px"
  route-station:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.station}"
    size: "32px"
  route-station-active:
    backgroundColor: "{colors.route-realtime}"
    textColor: "{colors.canvas}"
    typography: "{typography.label}"
    rounded: "{rounded.station}"
    size: "32px"
  mechanics-explorer:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "20px 0 0"
  mechanics-module:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.mechanics}"
    padding: "14px"
    height: "142px"
---

# Design System: LLM Serving Lab

## Overview

**Creative North Star: "The Metro Operations Desk"**

LLM Serving Lab treats inference as a visible transit network rather than a generic chat dashboard. Near-black control surfaces, fine route lines, compact status labels, and instrument-like readouts create a calm operations room where the serving mechanism remains more important than decoration.

The system is dense but ordered. A strategy selects one colored route through Client, Queue, Model, and Response; the rest of the interface stays neutral so route differences, generated output, and measured runtime remain legible. A progressively disclosed Mechanics Explorer extends that route into a four-step educational model of tokens, tensors, queues, GPU work, KV cache, and SSE without competing with the primary experiment when collapsed.

**Key Characteristics:**

- Near-black tonal layers separated by fine structural lines.
- A single mode-specific route color carries state through navigation, controls, traces, and mechanics.
- Sans-serif explanation paired with monospaced endpoints, telemetry, tensor labels, and event time.
- Compact control-desk density with a dominant observable request route.
- Progressive disclosure separates the essential experiment from the deeper four-step explanation.
- Responsive transformation from horizontal control room to vertical mobile flows.
- Simulated educational time is explicitly separated from real telemetry and detected runtime.

## Colors

The palette is a restrained dark instrument panel whose saturated signals identify serving routes and operational state, never decorative themes.

### Primary

- **Realtime Cyan** (`#22d3ee`): Default route signal for realtime mode, active trace stations, mechanics steps, focus, and dispatch.

### Secondary

- **Batch Green** (`#4ade80`): Offline batch route and healthy runtime status.
- **Dynamic Amber** (`#fbbf24`): Continuous batching route and its queue-window explanation.
- **Streaming Blue** (`#60a5fa`): Token-stream route and chunk progression.

### Tertiary

- **Signal Danger** (`#fb7185`): Connection failures and error events only.

### Neutral

- **Black Glass Canvas** (`#070a0d`): Uninterrupted application background and dark ink on saturated actions.
- **Control Surface** (`#0b1016`): Shared plane for route, panels, and compute modules.
- **Surface Hover** (`#141c25`): Navigation hover fill.
- **Field Hover** (`#485769`): Stronger editable-field outline on pointer hover.
- **Network Line / Strong Network Line** (`#25303b` / `#374554`): Dividers, module borders, editable boundaries, arrows, and inactive stations.
- **Instrument Ink** (`#edf3f8`): Titles, selected labels, and generated output.
- **Muted Ink / Quiet Ink** (`#98a6b7` / `#7f8da0`): Explanatory copy and secondary machine labels.

**The One Active Route Rule.** Exactly one strategy color may carry the active interaction state at a time; inactive structure stays neutral.

**The Signal Has Meaning Rule.** Saturated colors communicate route identity, health, progress, focus, or failure—not ornament.

## Typography

**Display Font:** Onest (with Segoe UI and sans-serif fallbacks)  
**Body Font:** Onest (with Segoe UI and sans-serif fallbacks)  
**Label/Mono Font:** JetBrains Mono (with Cascadia Mono and monospace fallbacks)

**Character:** Onest keeps explanations contemporary and calm, while JetBrains Mono makes endpoints, timing, tensor shapes, queue windows, state labels, and event history read like operational evidence. The pairing is technical without turning the whole product into a terminal.

### Hierarchy

- **Display** (700, fluid 30–52px, 0.98 line-height): Current serving strategy; fixed at 38px on narrow mobile screens.
- **Title** (700, 17px, 1.5 line-height): Mechanics Explorer explanation title.
- **Headline** (700, 15px, 1.5 line-height): Primary panel headings; compact panel variants use 14px.
- **Body** (400, 14px, 1.5 line-height): Mode explanation and generated model text.
- **Supporting** (400, 12px, 1.5 line-height): Mechanics summary, step title, and route-stage titles.
- **Machine Label** (600, 11px, 0.08em letter-spacing): Mechanics kicker, module labels, step number, and explanatory formulae.
- **Label** (600, 10px, 0.1em letter-spacing): Telemetry, navigation metadata, timestamps, and keyboard hints.
- **Micro Label** (600, 9px, 0.1em letter-spacing): Dense panel categories, flow-link captions, and station details.

**The Two-Language Rule.** Use Onest for concepts and model content; use JetBrains Mono for machine-readable facts, representations, and control metadata.

## Layout

The desktop shell is a 244px sticky strategy rail beside a fluid work area capped at 1540px. The live route occupies the full width above a three-column control desk. Its Mechanics Explorer opens in place beneath the route, preserving the single trace panel rather than adding another dashboard card. Inside it, four equal interactive modules and three 40px links form a left-to-right computational sequence.

At 1180px the desk becomes two columns. At 840px the rail becomes a horizontally scrollable top strip and the desk collapses to one column. At 620px both request route and Mechanics Explorer turn vertical: modules become a single column, links become 18px vertical connectors, non-participating route stages disappear, and metrics become a two-by-two grid. The expanded mobile page intentionally grows with the explanation rather than clipping it.

**The Route-First Rule.** The observable Client-to-Response path remains above controls and telemetry at every viewport; never bury it below the generated answer.

**The Progressive Detail Rule.** Keep the mechanics summary visible in the route panel, but reveal the full educational board only after an explicit “Как это работает” action.

## Elevation & Depth

The system is flat by default and uses no panel drop shadows. Depth comes from tonal layering, one-pixel borders, dim/reached/current opacity states, and the contrast between canvas, board, shared surface, and route-soft current modules. Halo effects belong only to tiny health, route, or active GPU signals where they communicate state.

**The Structural Depth Rule.** Create hierarchy with surface tone, opacity, and network lines; do not lift ordinary panels with generic shadows.

## Shapes

The form language grows from tiny computational marks to restrained containers: tensor cells use 1px corners, lanes 2px, tokens and queue slots 3px, request/result chips 4px, tensor and queue frames 5px, controls 6–8px, compute modules and narrow-screen panels 9px, and primary panels 12px. Route stations and status signals remain fully circular.

**The Station Geometry Rule.** Circles belong to signals and route nodes; content containers remain low-radius rectangles, while miniature compute representations use only the radius needed to remain legible.

## Components

### Buttons

- **Shape:** Compact control corners with a full-width 50px dispatch button, 44px minimum text actions, and 52px minimum mechanics disclosure.
- **Primary:** The active route color fills the dispatch control; dark canvas ink and a small signal dot keep it instrument-like.
- **Hover / Focus:** Hover increases brightness or uses the Field Hover outline, press moves down by one pixel, and keyboard focus uses a two-pixel active-route ring with a three-pixel offset.
- **Secondary / Ghost:** Text and replay actions remain transparent and use the active route color, shifting to primary ink on hover.

### Cards / Containers

- **Corner Style:** Restrained panel curve (12px; 9px on narrow screens).
- **Background:** One control-surface plane shared by trace, experiment, results, inspector, event log, and mechanics modules.
- **Shadow Strategy:** No panel shadows; see Elevation & Depth.
- **Border:** One-pixel network line.
- **Internal Padding:** 20px by default; 22–24px for the dominant trace and experiment, 26px for the desktop mechanics board, and 18px for that board on mobile.

### Inputs / Fields

- **Style:** Near-black fill, strong network-line stroke, 7px corners, and monospaced editable content.
- **Hover / Focus:** Hover uses Field Hover (`#485769`); focus changes the border and two-pixel outline to the current route color.
- **Error / Disabled:** Errors use Signal Danger; disabled dispatch and replay controls preserve context while preventing duplicate work.

### Navigation

The strategy rail uses 58px rows, route dots, concise title-plus-mechanism labels, and no default fill. Hover reveals Surface Hover; active state adds a translucent route wash and a two-pixel marker. On narrow screens labels simplify and the rail becomes a horizontally scrollable 48px-high strip.

### Request Route

The signature route is a four-station Client → Queue → Model → Response trace. Neutral lines and rings show topology; an active station becomes solid route color, completed stations retain a route outline, and one or four 5px payload cells communicate the actual request count represented by the experiment. While running, the route and expanded mechanics step synchronize to Client, Queue, Model, and Response.

### Mechanics Explorer

The explorer is progressive disclosure inside the route panel. Its summary line previews the mode-specific computation; expansion reveals four real button modules so a learner can stop on any step. Replay advances after 850ms for the first state and 1100ms for later states, while collapsing, selecting a step, changing mode, starting an actual run, or hiding the document cancels stale playback.

Each strategy uses a different finite representation: realtime shows separate tokenization and serial model lanes; offline batch shows one wide tensor and shared GPU work; continuous batching shows arrivals, a bounded queue window, an `[N×T]` batch, and Future mapping; streaming shows prompt tokens, KV cache, autoregressive decode, and SSE chunks. Reached modules remain visible, the current module receives the route-soft fill, and the readout explains exactly one of four steps.

The explorer is an educational model, not telemetry. Its simplified tensor shapes and stretched animation time are labeled as such; actual latency, queue time, inference time, batch size, and CPU/CUDA runtime remain in the telemetry and runtime note. During a real request, stage events drive the explorer instead of its demonstration clock.

### Telemetry and Event Readouts

Metrics form a border-separated instrument row with monospaced values and quiet labels. The event timeline uses timestamp-and-message pairs divided by hairlines, with failure text as the only danger-colored content. These readouts are the source of measured truth and must never be populated from the educational animation.

**The Final-State Motion Rule.** Under reduced motion, every module and link renders fully visible with no intermediate transform; comprehension must not depend on playback.

## Do's and Don'ts

### Do:

- **Do** keep the current mode's route color consistent across navigation, dispatch, focus, trace, and mechanics.
- **Do** synchronize expanded mechanics to actual request stages while preserving telemetry as the measured source of truth.
- **Do** make all four mechanics modules keyboard-operable buttons with a visible selected state.
- **Do** preserve visible focus, readable contrast, cancellable replay, reduced-motion final state, and vertical mobile flow.
- **Do** explain token, tensor, queue, GPU, cache, Future, and SSE representations with concise labels and step copy.

### Don't:

- **Don't** present educational animation duration, simplified tensor geometry, or visual request count as measured runtime data.
- **Don't** turn the application into a generic message-bubble chat or interchangeable analytics cards.
- **Don't** add decorative charts, gradients, broad glows, or invented performance claims.
- **Don't** autoplay hidden mechanics, leave obsolete timers running, or make motion the only way to understand state.
- **Don't** clip or horizontally compress the four-step explanation on mobile; stack the flow vertically.
