# Graph Explorer — Wireframe Specification

**Author:** Sable Nakamura-Whitfield (Principal UX Designer)
**Issue:** #536
**Date:** 2026-03-29
**Status:** Draft

---

## 1. Design Intent

The Graph Explorer is the primary interactive view for navigating isnad (chain of narration) networks. It must serve two distinct user modes:

1. **Directed lookup** — a researcher searches for a specific narrator and explores their transmission network outward
2. **Serendipitous exploration** — a scholar browses clusters, notices structural patterns (common links, bridge narrators), and follows curiosity

The design prioritizes legibility over spectacle. Every visual encoding (size, color, thickness, position) must carry meaning. Nothing decorative.

**Data scale context:** The full graph contains ~5,000 narrators and ~40,000 hadiths with ~3.25M transmission edges (per PRD estimates). The explorer will never render the full graph at once — progressive, query-driven subgraph loading is mandatory.

---

## 2. Page Layout

### 2.1 Desktop (>=1280px)

```
+-----------------------------------------------------------------------+
| HEADER: Isnad Graph > Graph Explorer                   [user avatar]  |
+-------+---------------------------------------------------------------+
| NAV   | TOOLBAR                                                       |
| SIDE  | [Search...] [Depth: 1|2|3] [Layout: Force|Hierarchy|Radial]   |
| BAR   | [Filters v]               [Reset] [Export v]    [Legend v]     |
| (220) +-----------------------------------------------+---------------+
|       |                                               | DETAIL PANEL  |
|       |                                               | (320px, coll- |
|       |                                               |  apsible)     |
|       |            GRAPH CANVAS                       |               |
|       |            (flex: 1)                           | [Narrator     |
|       |                                               |  profile card |
|       |                                               |  + chain list |
|       |                                               |  + stats]     |
|       |                                               |               |
|       |                                               |               |
|       +-----------------------------------------------+---------------+
|       | STATUS BAR: 47 nodes, 83 edges | Zoom: 120%   | Community: 3  |
+-------+---------------------------------------------------------------+
```

- **Nav sidebar** (220px): Global app navigation (existing `Sidebar` component), always visible
- **Toolbar**: Full-width bar above canvas with search, controls, and actions
- **Graph canvas**: HTML5 Canvas via `react-force-graph-2d`, fills remaining space
- **Detail panel** (320px): Right-side panel, collapsed by default, opens on node click
- **Status bar**: Bottom strip showing graph statistics and zoom level

### 2.2 Tablet (768px–1279px)

```
+-----------------------------------------------------------------------+
| HEADER: Isnad Graph                        [hamburger] [user avatar]  |
+-----------------------------------------------------------------------+
| TOOLBAR (stacked: search row + controls row)                          |
+-----------------------------------------------------------------------+
|                                                                       |
|                    GRAPH CANVAS (full width)                           |
|                                                                       |
+-----------------------------------------------------------------------+
| STATUS BAR                                                            |
+-----------------------------------------------------------------------+
| DETAIL PANEL (bottom sheet, 40vh, swipe-dismissible)                  |
+-----------------------------------------------------------------------+
```

- Nav sidebar collapses to hamburger menu overlay
- Detail panel becomes a bottom sheet (slides up from bottom)
- Toolbar controls stack into two rows
- Filters move into a modal/dropdown

### 2.3 Mobile (<768px)

```
+-----------------------------------+
| HEADER          [ham] [avatar]    |
+-----------------------------------+
| [Search narrator...]             |
| [Depth: 1] [Filters] [Layout]   |
+-----------------------------------+
|                                   |
|        GRAPH CANVAS               |
|        (full width,               |
|         calc(100vh - 200px))      |
|                                   |
+-----------------------------------+
| 12 nodes, 18 edges        [+][-] |
+-----------------------------------+
```

- Detail panel opens as full-screen overlay on node tap
- Toolbar compresses to icon buttons with tooltips
- Touch gestures: pinch-to-zoom, two-finger pan, tap node to select
- Maximum recommended depth on mobile: 2 (to limit node count)

---

## 3. Toolbar Controls

### 3.1 Search

```
+----------------------------------------------+
| [magnifier icon] Search narrator...     [x]  |
+----------------------------------------------+
| > Abu Hurayra (ابو هريرة)                    |  <- dropdown results
| > Abu Hurayra al-Dawsi (ابو هريرة الدوسي)    |
| > ...                                        |
+----------------------------------------------+
```

- Debounced typeahead (300ms) against narrator search API
- Results show both `name_en` and `name_ar` (RTL-aligned)
- Selecting a result fetches the narrator's network at current depth and centers the graph on that node
- Search input retains focus after selection for rapid sequential lookups
- Keyboard: arrow keys navigate results, Enter selects, Escape closes dropdown
- Clear button (x) visible when input has value

### 3.2 Depth Control

```
  Depth: [ 1 | 2 | 3 ]
           ^
```

- Segmented button group (not a dropdown — all options visible at once)
- Controls how many hops from the selected narrator are fetched
- Changing depth re-fetches the network for the current selected narrator
- Active segment visually distinguished (filled background)
- Tooltip on hover: "Number of transmission steps from selected narrator"

### 3.3 Layout Toggle

```
  Layout: [ Force | Hierarchy | Radial ]
```

- **Force-directed** (default): D3 force simulation, nodes repel, edges attract. Best for discovering clusters and bridge narrators.
- **Hierarchical** (top-to-bottom): Teachers at top, students at bottom. Best for reading a single isnad chain linearly.
- **Radial**: Selected narrator at center, concentric rings by hop distance. Best for ego-network analysis.
- Switching layout animates nodes to new positions over 500ms (respects `prefers-reduced-motion`: instant if reduced)

### 3.4 Filter Controls

```
  [Filters v]
  +---------------------------------------+
  | ERA (century AH)                      |
  | [1st] [2nd] [3rd] [4th] [5th+]       |
  |                                       |
  | SECT                                  |
  | [x] Sunni  [x] Shia  [ ] Unknown     |
  |                                       |
  | RELIABILITY                           |
  | [x] Trustworthy  [x] Acceptable      |
  | [x] Weak         [ ] Fabricator       |
  |                                       |
  | COLLECTION                            |
  | [x] Bukhari  [x] Muslim  [x] ...     |
  |                                       |
  | NODE COUNT LIMIT                      |
  | [=====o===========] 200              |
  |  50              500                  |
  |                                       |
  | [ Apply ]  [ Clear All ]             |
  +---------------------------------------+
```

- Opens as a dropdown panel below the Filters button
- Checkbox groups for categorical filters
- Range slider for node count limit (safety valve for performance)
- "Apply" commits filter changes; "Clear All" resets to defaults
- Active filter count shown as badge on Filters button: `[Filters (3)]`
- Filtered-out nodes are hidden, not grayed — reducing visual noise

### 3.5 Actions

- **Reset**: Clears the graph, deselects narrator, returns to empty state
- **Export**: Dropdown with options:
  - Export as PNG (canvas snapshot)
  - Export as SVG (re-rendered vector)
  - Export adjacency list (CSV)

### 3.6 Legend Toggle

```
  [Legend v]
  +---------------------------------------+
  | NODE SIZE: degree (number of links)   |
  |   o  = 1-5 links                      |
  |  (O) = 6-20 links                     |
  | (( )) = 21+ links                     |
  |                                       |
  | NODE COLOR: Louvain community         |
  |   ● Blue    = Community 1             |
  |   ● Orange  = Community 2             |
  |   ● Green   = Community 3             |
  |   ...                                 |
  |                                       |
  | EDGE THICKNESS: transmission freq.    |
  |   ─── = 1 transmission                |
  |   ═══ = 5+ transmissions              |
  |                                       |
  | EDGE ARROWS: direction of narration   |
  |   A ──→ B  = A transmitted to B       |
  +---------------------------------------+
```

- Toggleable panel, collapsed by default
- Updates dynamically to reflect currently visible communities
- Always accessible — never hidden behind interaction

---

## 4. Graph Canvas

### 4.1 Node Visual Encoding

| Property | Visual channel | Source field | Rationale |
|----------|---------------|-------------|-----------|
| Narrator importance | Node radius | `in_degree + out_degree` | Degree correlates with transmission activity; instantly communicates hub narrators |
| Community membership | Node fill color | `community_id` (Louvain) | Distinguishes scholarly circles; uses OKLCH palette for perceptual uniformity |
| Selection state | Stroke ring | UI state | 3px ring in accent color around selected node |
| Hover state | Glow + cursor | UI state | Subtle outer glow, pointer cursor |

**Node radius mapping:**

| Degree range | Radius (px) | Label |
|-------------|------------|-------|
| 1–5 | 4 | Low activity |
| 6–20 | 8 | Moderate |
| 21–50 | 12 | High |
| 51+ | 16 | Hub narrator |

**Color palette** (OKLCH-based, distinguishable in all three color-vision deficiency types):

```
Community 1:  oklch(65% 0.15 250)  — blue
Community 2:  oklch(70% 0.15 60)   — amber
Community 3:  oklch(60% 0.15 150)  — green
Community 4:  oklch(55% 0.15 330)  — purple
Community 5:  oklch(65% 0.15 25)   — red-orange
(additional communities cycle with lightness offset)
```

All community colors meet WCAG 2.2 AA contrast ratio (4.5:1) against the canvas background (#fafafa).

### 4.2 Edge Visual Encoding

| Property | Visual channel | Source | Rationale |
|----------|---------------|--------|-----------|
| Direction | Arrow head | `TRANSMITTED_TO` direction | Shows flow from teacher to student |
| Frequency | Stroke width | Count of parallel transmissions | Thicker = more hadiths shared via this link |
| Relationship type | Stroke style | `relationship` field | Solid = `TRANSMITTED_TO`, dashed = `STUDIED_UNDER` |
| Highlighted chain | Color + opacity | UI state (path selection) | Full opacity + accent color for selected chain; dimmed for others |

**Edge width mapping:**

| Transmission count | Width (px) |
|-------------------|-----------|
| 1 | 1 |
| 2–5 | 2 |
| 6–20 | 3 |
| 21+ | 4 |

### 4.3 Node Labels

- **Default (zoom < 1.5x):** No labels — reduces clutter at overview zoom levels
- **Medium zoom (1.5x–3x):** Show `name_en` for hovered/selected nodes only
- **High zoom (>3x):** Show `name_en` (LTR) below node, `name_ar` (RTL) above node for all visible nodes
- Label font: system sans-serif, 10px (scales inversely with zoom to maintain readability)
- Label collision avoidance: labels that overlap are hidden (lowest-degree node hidden first)

### 4.4 Interaction States

#### Idle (no selection)

```
    ●───────●
   / \       \
  ●   ●───●   ●
       |
       ●
```

All nodes at base opacity (1.0), all edges at 0.4 opacity.

#### Node Hover

- Hovered node: outer glow (4px, community color at 40% opacity)
- Hovered node label: visible (name_en + name_ar)
- Adjacent edges: opacity 0.8
- Tooltip appears after 200ms delay:

```
+----------------------------------+
| Abu Hurayra (ابو هريرة)          |
| Gen: Sahabi | d. 59 AH           |
| 342 transmissions | Community 7  |
| Trustworthiness: Thiqah          |
+----------------------------------+
```

#### Node Selected (click)

- Selected node: 3px accent ring (#1a73e8)
- Connected nodes: full opacity
- Non-connected nodes: 0.2 opacity (fade to background)
- Connected edges: full opacity, colored by relationship type
- Non-connected edges: 0.1 opacity
- Detail panel opens (or updates) on right side
- Double-click: re-centers graph on this node and fetches its network

#### Chain Highlighted (from detail panel)

When user selects a specific chain from the detail panel:

- Chain path edges: 3px, accent color (#1a73e8), full opacity
- Chain path nodes: full opacity, accent ring
- All other nodes/edges: 0.15 opacity
- Chain renders as a clear linear path through the network

### 4.5 Canvas Controls

```
  +-----+
  | [+] |   Zoom in (keyboard: =)
  | [-] |   Zoom out (keyboard: -)
  | [o] |   Fit to view (keyboard: 0)
  | [c] |   Center on selected (keyboard: c)
  +-----+
```

- Floating button group in bottom-left corner of canvas
- Mouse wheel: zoom in/out centered on cursor
- Click-drag on canvas: pan
- Click-drag on node: reposition node (pins it; double-click to unpin)

---

## 5. Detail Panel

Opens when a node is selected. 320px wide, collapsible via [x] button or Escape key.

### 5.1 Narrator Detail Card

```
+---------------------------------------+
| [x]                     NARRATOR      |
+---------------------------------------+
|                                       |
|  ابو هريرة الدوسي                     |  <- RTL, large
|  Abu Hurayra al-Dawsi                 |  <- LTR, medium
|                                       |
|  Kunya: Abu Hurayra                   |
|  Nisba: al-Dawsi                      |
|  Generation: Sahabi                   |
|  Birth: — AH | Death: 59 AH          |
|  Sect: Sunni                          |
|  Trustworthiness: Thiqah              |
|                                       |
+---------------------------------------+
|  NETWORK STATISTICS                   |
+---------------------------------------+
|  Teachers (in):    12                 |
|  Students (out):  342                 |
|  Betweenness:      0.087             |
|  PageRank:         0.0042            |
|  Community:        7 (● Blue)         |
+---------------------------------------+
|  CHAINS (47 total)           [See all]|
+---------------------------------------+
|  ► Bukhari 1: "Actions are by..."     |
|  ► Muslim 23: "The religion is..."    |
|  ► Abu Dawud 4: "Whoever believes..." |
|  ► Tirmidhi 11: "The best of you..."  |
|  ... (scrollable)                     |
+---------------------------------------+
|  [View Full Profile →]                |
+---------------------------------------+
```

- Arabic name displayed in RTL with `dir="rtl"` and appropriate font stack
- "View Full Profile" navigates to the dedicated NarratorDetailPage
- Chain list items are clickable — selecting one highlights that chain path in the graph
- Network statistics use the narrator's pre-computed graph metrics

### 5.2 Edge Detail (hover)

When hovering an edge, a lightweight tooltip appears near the cursor:

```
+----------------------------------------+
| Abu Hurayra → Ibn Shihab al-Zuhri      |
| TRANSMITTED_TO                          |
| 23 shared hadiths                      |
+----------------------------------------+
```

---

## 6. Data Visualization Strategy

### 6.1 Node Sizing by Centrality

Two modes available via a small toggle in the legend panel:

1. **Degree mode** (default): Node radius maps to `in_degree + out_degree`. Simple, intuitive — bigger nodes have more connections.
2. **Centrality mode**: Node radius maps to `betweenness_centrality`. Reveals bridge narrators who connect otherwise separate communities (e.g., al-Zuhri, Nafi').

### 6.2 Community Clustering

- Louvain `community_id` drives node color
- Force simulation includes a weak cluster force that pulls same-community nodes together without overriding the natural edge-based layout
- Communities of <3 visible nodes are grouped under "Other" in the legend to avoid legend bloat

### 6.3 Era/Generation Overlay

Optional toggle in the legend to color-code by generation instead of community:

| Generation | Color |
|-----------|-------|
| Sahabi (Companion) | oklch(65% 0.15 250) — blue |
| Tabi'i (Successor) | oklch(70% 0.15 150) — green |
| Tabi' al-Tabi'in | oklch(65% 0.15 60) — amber |
| Later | oklch(55% 0.15 0) — neutral gray |

This mode is mutually exclusive with community coloring — a radio toggle, not additive.

---

## 7. Performance Strategy

### 7.1 Progressive Loading

- Graph starts empty. User searches for a narrator, which fetches that narrator's ego-network at depth N.
- Clicking a node in the graph fetches _that_ node's network and merges new nodes/edges into the existing graph (current behavior in `GraphExplorerPage.tsx`).
- Duplicate nodes/edges are deduplicated client-side by ID (current behavior).

### 7.2 Node Count Limits

| Tier | Node count | Rendering strategy |
|------|-----------|-------------------|
| Small | <200 | Canvas 2D, labels visible at moderate zoom, full interaction |
| Medium | 200–1,000 | Canvas 2D, labels only on hover/select, reduced charge strength |
| Large | 1,000–5,000 | Canvas 2D, no labels except selected, simplified node rendering (circles only, no glow), lower simulation tick rate |
| Overflow | >5,000 | Blocked — user must apply filters or reduce depth to bring count below 5,000. Warning banner displayed. |

### 7.3 Level-of-Detail (LOD)

At low zoom levels (viewing many nodes):
- Nodes render as simple filled circles (no stroke, no glow)
- Labels hidden
- Edges render as 1px lines (no arrows)
- Tooltip disabled — requires minimum zoom level to activate

At high zoom levels (viewing few nodes):
- Full node rendering (stroke, glow on hover)
- Labels visible for all nodes in viewport
- Edge arrows and variable width visible
- Tooltip on hover active

Transition between LOD levels is continuous, not stepped — properties interpolate with zoom level.

### 7.4 Viewport Culling

- Nodes outside the visible viewport are excluded from canvas draw calls
- Force simulation continues for off-screen nodes but rendering is skipped
- Edge rendering is skipped if both endpoints are off-screen

### 7.5 Simulation Management

- Force simulation runs for 300 ticks max, then freezes
- User can unfreeze by dragging a node or clicking "Re-layout" in toolbar
- On depth/filter change, simulation restarts with alpha 0.3 (gentle re-arrangement, not full re-randomization)
- `requestAnimationFrame`-based render loop, not timer-based

---

## 8. RTL and Bidirectional Text

### 8.1 Arabic Text Rendering

- All Arabic names use `dir="rtl"` and `lang="ar"` attributes
- Canvas text rendering: Arabic labels use a right-to-left `textAlign: 'right'` with appropriate Arabic font (Noto Naskh Arabic, with system Arabic fallback)
- Mixed-script labels: Arabic name above node (RTL), English name below node (LTR) — never on the same line

### 8.2 Layout Direction

- The page layout itself remains LTR (sidebar on left, detail panel on right)
- Within the detail panel, Arabic content sections use `dir="rtl"` block-level direction
- Search results show Arabic names right-aligned within each result row
- Hadith matn text in chain list items uses `dir="rtl"`

### 8.3 Font Stack

```css
--font-arabic: 'Noto Naskh Arabic', 'Geeza Pro', 'Traditional Arabic', serif;
--font-ui: system-ui, -apple-system, sans-serif;
```

---

## 9. Accessibility

### 9.1 Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move focus through toolbar controls, then to graph canvas, then to detail panel |
| Enter/Space | Activate focused control; in graph, select focused node |
| Arrow keys | In graph canvas: move focus between nodes (nearest-neighbor traversal) |
| Escape | Close detail panel, deselect node, close filter dropdown |
| + / - | Zoom in / out |
| 0 | Fit graph to viewport |
| c | Center on selected node |
| / | Focus search input |
| ? | Open legend |

- When graph canvas has focus, a visible focus ring appears around the currently focused node (2px dashed outline)
- Tab order within detail panel follows visual order top-to-bottom

### 9.2 Screen Reader Support

- Graph canvas has `role="application"` with `aria-label="Narrator transmission network graph"`
- On node focus, screen reader announces: "{name_en}, {generation}, {degree} connections, community {community_id}. Press Enter to select and view details."
- On node select, screen reader announces: "Selected {name_en}. Detail panel opened. {teachers} teachers, {students} students."
- Edge information is available via a structured data table alternative (accessible via "View as table" link above the canvas)

### 9.3 Alternative Table View

For users who cannot use the visual graph, a "View as table" toggle renders the same data as two accessible tables:

**Narrators table:**
| Name (EN) | Name (AR) | Generation | Degree | Community | Centrality |

**Transmissions table:**
| From | To | Relationship | Shared hadiths |

- Tables support sorting by any column
- Row click navigates to narrator detail page
- This is a full alternative, not a secondary view — it must contain all information present in the graph

### 9.4 High Contrast Mode

- Respects `prefers-contrast: more` media query
- In high contrast mode:
  - Node outlines become 2px solid black
  - Edge colors switch to black (directional) and dark gray (non-directional)
  - Community differentiation adds pattern fills (hatching, dots, stripes) in addition to color
  - Canvas background becomes pure white (#fff)
  - All text becomes black (#000)

### 9.5 Reduced Motion

- Respects `prefers-reduced-motion: reduce`
- Force simulation runs to completion instantly (no animated convergence)
- Layout transitions are instant (no 500ms animation)
- Node hover/select state changes are instant (no glow fade)

---

## 10. Isnad Chain Path Highlighting

A key scholarly use case: tracing a complete isnad chain through the network.

### 10.1 Trigger

From the detail panel chain list, clicking a chain entry (e.g., "Bukhari 1: Actions are by intentions...") highlights the full chain path.

### 10.2 Visual Treatment

```
Before highlighting:

    ●───●───●───●
   / \       \
  ●   ●───●   ●

After highlighting chain [A → B → C → D]:

    ●━━━●━━━●━━━●        <- chain path: thick, accent color
   / \       \
  ○   ○───○   ○          <- non-chain: faded to 0.15 opacity
```

- Chain edges: 3px stroke, accent color (#1a73e8), directional arrows
- Chain nodes: full opacity, accent ring, labels visible
- Non-chain elements: 0.15 opacity
- "Clear highlight" button appears in the toolbar when a chain is highlighted
- Keyboard: Escape clears the chain highlight

### 10.3 Multiple Chains

If a narrator participates in multiple chains, the user can highlight one at a time. A small "chain navigator" appears:

```
  Chain 1 of 47   [<] [>]   [Clear]
```

---

## 11. Export Specifications

### 11.1 PNG Export

- Renders current canvas state at 2x resolution (for retina/print)
- Includes visible labels and legend
- Excludes toolbar and detail panel
- Filename: `isnad-graph-{narrator-name}-{depth}hop-{timestamp}.png`

### 11.2 SVG Export

- Re-renders graph as SVG elements (not canvas rasterization)
- Preserves node colors, edge styles, labels
- Suitable for academic publication embedding
- Filename: `isnad-graph-{narrator-name}-{depth}hop-{timestamp}.svg`

### 11.3 CSV Export

- Adjacency list format: `source_id, source_name, target_id, target_name, relationship, weight`
- Includes all currently loaded nodes and edges
- Filename: `isnad-graph-{narrator-name}-{depth}hop-{timestamp}.csv`

---

## 12. Empty and Error States

### 12.1 Empty State (no search yet)

```
+-----------------------------------------------+
|                                               |
|           [graph icon, muted]                 |
|                                               |
|    Search for a narrator to begin             |
|    exploring the transmission network.        |
|                                               |
|    Try: Abu Hurayra, al-Zuhri, Malik          |
|         ibn Anas, Aisha bint Abi Bakr         |
|                                               |
+-----------------------------------------------+
```

- Suggested names are clickable — each triggers the search
- Graph icon is a simple line drawing of connected nodes

### 12.2 No Results State

```
+-----------------------------------------------+
|                                               |
|    No narrators found for "xyz"               |
|    Try searching with Arabic name or          |
|    a different transliteration.               |
|                                               |
+-----------------------------------------------+
```

### 12.3 Loading State

- Skeleton overlay on canvas area (not a spinner)
- Toolbar remains interactive
- "Loading network..." text in status bar

### 12.4 Error State

```
+-----------------------------------------------+
|                                               |
|    Could not load network data.               |
|    [Retry]                                    |
|                                               |
+-----------------------------------------------+
```

### 12.5 Node Limit Exceeded

```
+-----------------------------------------------+
| WARNING: This query returned 6,234 nodes.     |
| For performance, results are limited to 5,000.|
| Apply filters or reduce depth to see the full |
| network.                                      |
|                                 [Open Filters] |
+-----------------------------------------------+
```

---

## 13. Responsive Breakpoint Summary

| Feature | Desktop (>=1280) | Tablet (768-1279) | Mobile (<768) |
|---------|:---:|:---:|:---:|
| Nav sidebar | Visible (220px) | Hamburger overlay | Hamburger overlay |
| Toolbar | Single row | Two rows | Compact icons |
| Graph canvas | flex: 1 | Full width | Full width |
| Detail panel | Right side (320px) | Bottom sheet (40vh) | Full-screen overlay |
| Filter panel | Dropdown | Modal | Modal |
| Legend | Dropdown | Dropdown | Collapsed, icon toggle |
| Touch gestures | n/a | Pinch/pan | Pinch/pan/tap |
| Max recommended depth | 3 | 3 | 2 |
| Node label visibility | Zoom-dependent | Zoom-dependent | Selected only |
| Export | PNG/SVG/CSV | PNG/CSV | PNG only |
| Table alternative | Inline toggle | Inline toggle | Default view option |

---

## 14. Component Mapping

How this wireframe maps to the existing frontend architecture:

| Wireframe element | Existing component | Changes needed |
|-------------------|-------------------|----------------|
| Page shell | `GraphExplorerPage.tsx` | Major expansion — toolbar, detail panel, filters |
| Force graph | `ForceGraph.tsx` (react-force-graph-2d) | Add LOD, node sizing, edge styling, chain highlighting |
| Search | Inline in page | Extract to `GraphSearch` component |
| Detail panel | New | `NarratorDetailPanel` component |
| Filter panel | New | `GraphFilters` component |
| Legend | New | `GraphLegend` component |
| Table alternative | New | `GraphTableView` component |
| Layout | `Layout.tsx` | No changes needed |
| Sidebar | `Sidebar.tsx` | No changes needed |

---

## 15. Design Tokens

Recommended CSS custom properties for the graph explorer (to be added to the design system):

```css
/* Graph canvas */
--graph-bg: #fafafa;
--graph-bg-contrast: #ffffff;

/* Node states */
--node-stroke: #ffffff;
--node-stroke-selected: var(--color-accent, #1a73e8);
--node-stroke-width: 1.5px;
--node-stroke-width-selected: 3px;
--node-opacity-dimmed: 0.2;

/* Edge states */
--edge-color-default: #cccccc;
--edge-color-highlight: var(--color-accent, #1a73e8);
--edge-opacity-default: 0.4;
--edge-opacity-dimmed: 0.1;

/* Detail panel */
--panel-width: 320px;
--panel-bg: #ffffff;
--panel-border: #e0e0e0;

/* Text */
--label-color: #333333;
--label-font-size: 10px;
```

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-03-29 | Sable Nakamura-Whitfield | Initial wireframe specification |
