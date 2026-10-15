---
name: AnalyserXDecoder
description: High-precision conversational document intelligence layer with strict evidence grounding and transparent citations
colors:
  primary: "#2563eb"
  primary-hover: "#1d4ed8"
  primary-badge-text: "#93c5fd"
  bg-primary-dark: "#0b0f17"
  bg-sidebar-dark: "#111622"
  bg-card-dark: "#171d2b"
  bg-card-hover-dark: "#1e2638"
  bg-input-dark: "#0e121a"
  border-dark: "#262f42"
  text-primary-dark: "#f8fafc"
  text-secondary-dark: "#cbd5e1"
  text-muted-dark: "#94a3b8"
  accent-green: "#10b981"
  accent-green-text: "#34d399"
  accent-red: "#ef4444"
  white: "#ffffff"
  black: "#000000"
typography:
  display:
    fontFamily: "Outfit, sans-serif"
    fontSize: "1.85rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "Outfit, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Manrope, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
  caption:
    fontFamily: "Outfit, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.08em"
  code:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.8em"
    fontWeight: 500
rounded:
  xs: "4px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "14px"
  lg: "20px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "9px 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
  card:
    backgroundColor: "{colors.bg-card-dark}"
    rounded: "{rounded.md}"
    padding: "14px"
---

# Design System: AnalyserXDecoder

## Overview

AnalyserXDecoder's design language communicates analytical rigor, speed, and uncompromising precision. Built for developers, researchers, and knowledge workers inspecting dense technical documentation and PDFs, the interface balances dense information hierarchy with calm, focused clarity.

The visual direction rejects generic AI-boilerplate tropes (no pulsing dots, no floating glow cards, no overused typefaces) in favor of crisp borders, purposeful color coding, verified WCAG AA contrast (≥ 4.5:1), and honest progress states.

## Colors

### Dark Theme (Default)
- **Primary Canvas (`--bg-primary`):** `#0b0f17` (Deep slate navy)
- **Sidebar Surface (`--bg-sidebar`):** `#111622`
- **Component Card (`--bg-card`):** `#171d2b` (Hover state: `#1e2638`)
- **Field Surface (`--bg-input`):** `#0e121a`
- **Structural Borders (`--border-color`):** `#262f42` (Focus state: `#3b82f6`)
- **Primary Text (`--text-primary`):** `#f8fafc` (14.5:1 contrast ratio)
- **Secondary Text (`--text-secondary`):** `#cbd5e1` (10.5:1 contrast ratio)
- **Muted & Placeholder (`--text-muted`):** `#94a3b8` (5.8:1 contrast ratio — strictly WCAG AA compliant)

### Light Theme
- **Primary Canvas (`--bg-primary`):** `#f8fafc`
- **Sidebar & Card Surfaces (`--bg-card`):** `#ffffff`
- **Structural Borders (`--border-color`):** `#cbd5e1`
- **Primary Text (`--text-primary`):** `#0f172a`
- **Secondary Text (`--text-secondary`):** `#334155`
- **Muted Text (`--text-muted`):** `#475569`

### Accents & Statuses
- **Action Accent (`--primary`):** `#2563eb` (Dark), `#1d4ed8` (Light) — guaranteed ≥ 4.5:1 contrast with white text.
- **Success / Grounded Citations:** `#10b981` (Surface: `rgba(16, 185, 129, 0.12)`, Text: `#34d399` / `#065f46`)
- **Error:** `#ef4444` (Dark), `#b91c1c` (Light)

## Typography

- **Brand & Headings:** `Outfit`, sans-serif (Weights: 600, 700, 800)
- **Interface & Prose:** `Manrope`, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif (Weights: 400, 500, 600, 700)
- **Code, Vectors & Badges:** `JetBrains Mono`, monospace (Weights: 500, 600)

### Modular Scale
The type hierarchy follows a strict modular step (≥ 1.25x between adjacent hierarchy tiers):
- **Brand Title (`h1`):** `1.85rem` (~29.6px, Weight 700)
- **Workspace Heading (`h2`):** `1.3rem` (~20.8px, Weight 600)
- **Empty State / Subhead (`h3`):** `1.0rem` (~16px, Weight 700)
- **Body Text:** `0.875rem` (~14px, Weight 400/500)
- **Category Labels / Caps:** `0.72rem` (~11.5px, Weight 700, Letter-spacing `0.08em`)

## Layout

- **Two-Column Shell:** Fixed-width interactive sidebar (`350px`, min `310px`, max `390px`) coupled with a flexible, full-height chat workspace.
- **Responsive Stacking:** On viewport widths under `860px`, the sidebar smoothly stacks into a scrollable upper panel (`max-height: 45vh`) with full-width chat below.
- **Rhythm:** Modular card gaps of `12px` – `16px`; chat message bubbles max-width capped at `84%` for optimal reading measure.

## Elevation & Depth

- Depth is expressed through surface tinting and crisp 1px borders rather than heavy blur shadows or arbitrary halos.
- Focus rings use a dedicated `2px solid var(--border-focus)` with `2px` offset.
- Hover states transition with `0.15s ease` on surface background and border hues.

## Shapes

- **Inputs, Buttons, Badges:** Border radius `6px` (`--radius-sm`).
- **Cards & Chat Bubbles:** Border radius `10px` (`--radius-md`).
- **Pills & Toggles:** Rounded-full (`9999px`) for quick-prompts and model badges.

## Components

### 1. Brand Header
- Dual-tone gradient mark (38×38px squircle) holding an SVG aperture decode glyph, paired with product title and uppercase subtitle.

### 2. Model & Source Controls
- Dropdown selectors with native keyboard navigation and visible focus rings.
- Segmented dual-tab for URL scraping and PDF drag-and-drop ingestion.

### 3. Citations & Evidence Accordion
- Collapsible cards for chunk-level evidence attribution displaying source URI, chunk ID, and exact snippet excerpt.

### 4. Honest Loading Indicator
- Replaced ambiguous pulsing dots with a calm, labeled spinner (`Synthesizing evidence...`) that accurately reflects retrieval and generation stages.

## Do's and Don'ts

### Do
- Always maintain WCAG AA contrast (≥ 4.5:1) for all body text, secondary labels, and input placeholders.
- Use `Outfit` for headings, `Manrope` for UI text, and `JetBrains Mono` for metadata and citations.
- Explicitly label loading states rather than using decorative blinking dots.
- Support both dark and light modes with seamless instant toggle.

### Don't
- Do not use generic, overused typefaces (Inter, Roboto, Space Grotesk).
- Do not use gradient text or colored halo shadows.
- Do not let placeholder text drop below 4.5:1 contrast against input fields.
- Do not fabricate testimonials or speculative enterprise claims.
