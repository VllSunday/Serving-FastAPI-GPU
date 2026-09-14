---
name: LLM Serving Lab
description: A dark metro-operations console that makes every model-serving route observable.
colors:
  route-realtime: "#22d3ee"
  route-batch: "#4ade80"
  route-dynamic: "#fbbf24"
  route-stream: "#60a5fa"
  signal-danger: "#fb7185"
  canvas: "#070a0d"
  surface: "#0b1016"
  surface-hover: "#141c25"
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
  label:
    fontFamily: "JetBrains Mono, Cascadia Mono, monospace"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0.1em"
rounded:
  control: "7px"
  navigation: "8px"
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
    typography: "{typography.label}"
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
---

# Design System: LLM Serving Lab

## Overview

**Creative North Star: "The Metro Operations Desk"**

LLM Serving Lab treats inference as a visible transit network rather than a generic chat dashboard. Near-black control surfaces, fine route lines, compact status labels, and instrument-like readouts make the application feel like a calm operations room where the mechanism is always more important than decoration.

The system is dense but ordered. A strategy selects one colored route through Client, Queue, Model, and Response; the rest of the interface stays neutral so that live state, measured output, and route differences remain legible. Motion is reserved for actual request progress and streaming state, and the same interface remains useful when reduced motion is requested.

**Key Characteristics:**

- Near-black tonal layers separated by fine structural lines.
- A single mode-specific route color carries state through navigation, controls, and trace stations.
- Sans-serif explanation paired with monospaced endpoints, telemetry, labels, and event time.
- Compact control-desk density with a dominant, observable request route.
- Responsive transformation from horizontal control room to vertical mobile route.

## Colors

The palette is a restrained dark instrument panel whose four saturated signals identify serving routes, never decorative themes.

### Primary

- **Realtime Cyan:** The default route signal for realtime mode, active trace stations, focus, and the primary dispatch control.

### Secondary

- **Batch Green:** Identifies offline batch mode and also carries healthy runtime status where the meaning is success.
- **Dynamic Amber:** Identifies continuous batching and the neutral connecting state while the server status is unresolved.
- **Streaming Blue:** Identifies token streaming without changing the surrounding neutral console.

### Tertiary

- **Signal Danger:** Reserved for connection failures and error events.

### Neutral

- **Black Glass Canvas:** The uninterrupted application background and darkest text-on-signal color.
- **Control Surface:** The shared plane for route, experiment, results, inspector, and event panels.
- **Surface Hover:** The only neutral hover fill for navigational affordances.
- **Network Line / Strong Network Line:** Structural dividers and interactive field outlines; the stronger line marks stations and editable boundaries.
- **Instrument Ink:** Primary titles and generated output.
- **Muted Ink / Quiet Ink:** Explanatory copy and secondary machine labels respectively.

**The One Active Route Rule.** Exactly one strategy color may carry the active interaction state at a time; inactive structure stays neutral.

**The Signal Has Meaning Rule.** Saturated colors communicate route identity, health, progress, focus, or failure—not ornament.

## Typography

**Display Font:** Onest (with Segoe UI and sans-serif fallbacks)  
**Body Font:** Onest (with Segoe UI and sans-serif fallbacks)  
**Label/Mono Font:** JetBrains Mono (with Cascadia Mono and monospace fallbacks)

**Character:** Onest keeps explanations contemporary and calm, while JetBrains Mono makes endpoints, timing, status, and event history read like real operational evidence. The pairing is technical without imitating a terminal everywhere.

### Hierarchy

- **Display** (700, fluid 30–52px, 0.98 line-height): Strategy title and current operating mode.
- **Headline** (700, 15px, 1.5 line-height): Compact panel headings within the control desk.
- **Body** (400, 14px, 1.5 line-height): Mode explanations and generated text; explanatory lines stay near 700px at the top of the page.
- **Label** (600, 10px, 0.1em letter-spacing): Uppercase telemetry categories, endpoints, state labels, timing, and keyboard hints.

**The Two-Language Rule.** Use Onest for concepts and model content; use JetBrains Mono only for machine-readable facts and control metadata.

## Layout

The desktop shell is a 244px sticky strategy rail beside a fluid work area capped at 1540px. The live route occupies the full width above a three-column control desk: experiment input, results telemetry, and the narrower mode inspector; the event log joins the two right columns. The recurring 14px panel gap keeps dense information spatially connected rather than scattering it into dashboard tiles.

At 1180px the desk becomes two columns and the event log spans both. At 840px the rail becomes a compact top strip with horizontally scrollable mode controls, while the desk collapses to one column. At 620px the request route turns vertical, non-participating stages disappear, metrics become a two-by-two grid, and editable text uses a mobile-safe 16px size.

**The Route-First Rule.** The observable Client-to-Response path remains above controls and telemetry at every viewport; never bury it below the generated answer.

## Elevation & Depth

The system is flat by default and uses no panel drop shadows. Depth comes from tightly controlled tonal layering, one-pixel borders, and the contrast between the canvas, sidebar, fields, and shared surface plane. The only halo-like effect belongs to tiny signal indicators, and it communicates live health or active route state.

**The Structural Depth Rule.** Create hierarchy with surface tone and network lines; do not lift ordinary panels with generic shadows.

## Shapes

Controls use gently compact corners, navigation uses a slightly wider curve, and main surfaces use restrained 12px corners. Route stations and status signals are fully circular, creating the recurring metro-map geometry. One-pixel borders are structural: they define editable fields, shared panels, rails, and stations without becoming decorative frames.

**The Station Geometry Rule.** Circles belong to signals and route nodes; content containers remain low-radius rectangles.

## Components

### Buttons

- **Shape:** Compact control corners with a full-width 50px dispatch button and 44px minimum text actions.
- **Primary:** The active route color fills the dispatch control; dark canvas ink and a small signal dot keep it instrument-like rather than promotional.
- **Hover / Focus:** Hover increases brightness slightly, press moves down by one pixel, and keyboard focus uses a two-pixel active-route outline with a three-pixel offset.
- **Secondary / Ghost:** Text actions remain transparent and use the active route color, shifting to primary ink on hover.

### Cards / Containers

- **Corner Style:** Restrained panel curve (12px; 9px on narrow mobile screens).
- **Background:** A single control-surface plane shared by trace, experiment, results, inspector, and event log.
- **Shadow Strategy:** No panel shadows; see Elevation & Depth.
- **Border:** One-pixel network line.
- **Internal Padding:** 20px by default, with 22–24px where the dominant trace or experiment needs additional operating room.

### Inputs / Fields

- **Style:** Near-black fill, strong network-line stroke, compact corners, and monospaced editable content.
- **Focus:** The border changes to the current route color and the fill lifts one neutral step; the global focus ring remains visible.
- **Error / Disabled:** Errors use Signal Danger; disabled dispatch controls reduce opacity and switch to a wait cursor while preserving their mode color.

### Navigation

The strategy rail uses 58px rows, small route dots, concise title-plus-mechanism labels, and no default fill. Hover reveals the neutral hover surface; active state adds a translucent route wash and a two-pixel route marker. On narrow screens, labels simplify and the rail becomes a horizontally scrollable 48px-high strip.

### Request Route

The signature component is a four-station Client → Queue → Model → Response trace. Neutral connecting lines and station rings show the topology; an active station becomes a solid route signal, completed stations retain a route-colored outline, and a small traveling signal appears only while a request is in flight. Mobile rotates the route vertically without changing its sequence.

### Telemetry and Event Readouts

Metrics form a border-separated instrument row with monospaced values and quiet labels. The event timeline is equally restrained: timestamp and message pairs are divided by hairlines, with failure text as the only danger-colored content.

## Do's and Don'ts

### Do:

- **Do** keep the current mode's route color consistent across navigation, dispatch, focus, trace, and result metadata.
- **Do** expose measured request state and timings in compact monospaced readouts.
- **Do** preserve visible keyboard focus, readable contrast, reduced-motion behavior, and the vertical mobile route.
- **Do** use fine lines and tonal differences to organize dense educational information.

### Don't:

- **Don't** turn the application into a generic message-bubble chat or a collection of interchangeable analytics cards.
- **Don't** add decorative charts, gradients, broad glows, or invented performance claims.
- **Don't** use multiple route colors as simultaneous decoration; a color must correspond to an actual mode or semantic state.
- **Don't** replace operational density with oversized marketing spacing or hide the serving mechanism behind the generated text.
