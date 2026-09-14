# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary user: a student demonstrating and explaining model-serving mechanics to
an instructor during a lesson. The interface is also used independently while
studying the code and collecting observations for notes.

## Product Purpose

LLM Serving Lab makes four inference strategies directly observable: realtime,
offline batching, continuous batching, and token streaming. Success means the
student can run each strategy, see its request path and measured behavior, and
connect the observation to a small, readable implementation.

## Positioning

Unlike a generic chat demo, the product exposes the serving mechanism itself:
queue time, inference time, batch identity and size, job lifecycle, streaming
chunks, and time to first token.

## Operating Context

The project runs locally in a browser next to source code, terminal logs,
OpenAPI, and GPU telemetry. It must work on CPU for development and on one NVIDIA
GPU for meaningful throughput experiments.

## Capabilities and Constraints

- One local FastAPI process owns one Hugging Face causal language model.
- Four serving strategies share the same model runtime.
- The UI must keep all four experiments functional and separately inspectable.
- Offline jobs are intentionally in-memory; this is a teaching project, not a
  durable production queue.
- Concrete benchmark claims must come from the user's own hardware and runs.

## Brand Commitments

The product name is **LLM Serving Lab**. The voice is concise, technical, and
educational. The user explicitly requires a minimal, polished dark interface.

## Evidence on Hand

- Working FastAPI implementation and automated tests in this repository.
- Live server metrics returned by `/health`, `/gpu`, and `/batcher/stats`.
- No supplied performance benchmark results; the UI must not invent them.

## Product Principles

1. Show the mechanism, not only the generated text.
2. Keep every strategy independently traceable in code and UI.
3. Prefer measured runtime facts over decorative analytics.
4. Preserve a direct path from experiment to explanation.
5. Remain usable without an NVIDIA GPU, while stating the limitation honestly.

## Accessibility & Inclusion

Keyboard operation, visible focus, reduced-motion support, readable contrast,
and a responsive layout are required for the browser interface.
