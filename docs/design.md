# UI/UX Design System: Lenny Growth Assistant

---

## 1. DESIGN SYSTEM LANGUAGE
*   **Backdrop**: Premium, modern dark violet palette:
    - Primary Deep Backdrop: `#050914`
    - Glass Card Surfaces: `#131026`
    - Secondary Paneling: `#181532`
*   **Primary Accent**: Glowing Neon Purple (`#7C3AED`) and Pink (`#EC4899`) gradients.
*   **Typography**: Inter Sans-Serif, optimized for skimmability and technical reading.

---

## 2. INFORMATION ARCHITECTURE
The desktop interface is structured as a premium 3-panel workspace:
```
┌──────────────────┬─────────────────────────────┬───────────────────────────┐
│                  │                             │                           │
│  Navigation &   │      Conversational         │      Claude-Style         │
│  Chat History    │      Workspace &            │      Interactive          │
│                  │      Composer Controls      │      Artifact Panel       │
│                  │                             │                           │
└──────────────────┴─────────────────────────────┴───────────────────────────┘
```

---

## 3. KEY INTERACTION STATES

### 3.1 Conversational State
*   User bubble right-aligned, gradient background.
*   Assistant bubble left-aligned, borderless transparent text for high readability.
*   **Honing Reasoning Accordion**: Interactive drop-down displaying active search status (searching database, counts, matching guest discussion metadata).

### 3.2 Artifact Slide-Over Panel
*   Opens automatically when specialized skill tags (`<artifact>`) are parsed in the SSE stream.
*   **TOC Navigation**: Dynamically compiles the headers inside the document, allowing 1-click smooth scrolling to sections.
*   **Preview / Source tabs**: Toggle seamlessly between rich editorial preview and raw source code.

---

## 4. ACCESSIBILITY & RESPONSIVENESS
*   **Dark / Light Mode**: Double-tap on the top navbar toggle switches variables between deep violet and high-contrast light mode slate.
*   **Responsive Breakpoints**: Sidebar collapses on mobile; Artifact Viewer overlays full-screen as an interactable slide-up drawer.
