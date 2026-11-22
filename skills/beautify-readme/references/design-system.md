# Design system

Consolidated design rules from the architecture, infocard, mindmap, and visual-direction skill families. Apply these when freezing the art-direction spec, choosing colors, typography, layout, or checking taste — whether hand-authoring SVG or using code-fence diagram engines.

## Table of contents

1. [Content analysis before design](#content-analysis-before-design)
2. [Tone-sensing palette](#tone-sensing-palette)
3. [Typography hierarchy](#typography-hierarchy)
4. [Color semantics for layered diagrams](#color-semantics-for-layered-diagrams)
5. [Layout patterns](#layout-patterns)
6. [Style families](#style-families)
7. [Taste checklist (anti-AI)](#taste-checklist-anti-ai)
8. [Spacing and visual accents](#spacing-and-visual-accents)
9. [Mind map color palettes](#mind-map-color-palettes)

---

## Content analysis before design

Analyze content along three dimensions before choosing layout, palette, or composition. This applies to infocard editorial cards, architecture diagrams, and hand-authored SVG modules alike.

### Density (determines breathing rhythm)

| Density | Content volume | Visual treatment |
| --- | --- | --- |
| Low | ≤ 50 words core | "Big-character" composition. One oversized element dominates. Generous whitespace. |
| Medium | 50–200 words | Hero + supporting panels. 2–3 main blocks with clear hierarchy. |
| High | 200+ words | Asymmetric multi-column grids. Primary/secondary/supporting blocks. Never equal-weight tiles. |

### Structure (determines layout geometry)

| Structure | Signal | Layout pattern |
| --- | --- | --- |
| Single point | One core concept | One anchor element dominates, rest recedes |
| Contrast | A vs B, old vs new | Split panel, two poles |
| Hierarchy | Layers build on each other | Stacked modules, pyramid |
| Flow | Sequential steps | Vertical cascade, numbered items |
| Radial | Core + derivatives | Hub with surrounding panels |
| Parallel | Multiple equal concepts | Asymmetric grid (never equal columns) |

### Mood (determines color temperature)

| Mood | Visual feel |
| --- | --- |
| Reflective | More whitespace, serif-heavy, lower contrast |
| Sharp | Strong contrast, bold type, vivid accent |
| Warm | Earth tones, rounded feel, gentle rhythm |
| Technical | Monospace accents, grid-like density |

---

## Tone-sensing palette

When no explicit style is chosen, auto-select a color palette based on the content topic. Scan content keywords and match the closest tone.

| Content tone | Background | Accent | Trigger keywords |
| --- | --- | --- | --- |
| Philosophical | `#FAF8F4` | `#7C6853` | cognition, thinking, meaning, philosophy, essence |
| Technical | `#F5F7FA` | `#3D5A80` | architecture, algorithm, system, API, code |
| Literary | `#FBF9F1` | `#6B4E3D` | story, narrative, writing, poetry, character |
| Scientific | `#F4F8F6` | `#2D6A4F` | experiment, data, research, paper, discovery |
| Business | `#F4F3F0` | `#2D6A4F` | market, strategy, growth, finance, investment |
| Creative | `#F6F3F2` | `#B8432F` | design, art, aesthetics, inspiration, creation |
| Default | `#FAFAF8` | `#4A4A4A` | When no clear match — prefer default over wrong match |

When a style template is explicitly chosen (from the architecture or infocard style families below), its colors take precedence over tone sensing.

---

## Typography hierarchy

Maintain a clear type scale and use it consistently across all visual modules — SVG assets, architecture diagrams, and infocard editorial cards.

| Role | Size (SVG units / CSS px) | Weight | Letter-spacing |
| --- | --- | --- | --- |
| Hero title | `48+` / `32–48px` | 700–900 | tight (`-0.02em`) |
| Section title | `40+` / `24–32px` | 700–800 | normal |
| Subtitle / summary | `28–36` / `16–20px` | 400–500 | normal |
| Body text | `20–24` / `14–16px` | 400 | normal |
| Meta / tags / captions | `16–18` / `11–13px` | 500–700 | uppercase, wider |

Rules:
- Body text color: never pure black (`#000000`). Use `#1a1a1a`, `#333`, or `#4a4a4a`.
- Build hierarchy with weight and color, not just font-size scaling.
- Use system font stacks; do not load remote fonts.
- Mix sans-serif, monospace, or serif only when the project supports it.

---

## Color semantics for layered diagrams

When creating architecture or system diagrams, use consistent semantic color coding for layers. The exact palette varies by chosen style, but the semantic mapping stays stable:

| Layer | Meaning | Typical treatment |
| --- | --- | --- |
| User | user-facing interfaces and clients | lightest tier |
| Application | business logic and API services | mid tier |
| AI / Logic | intelligence, rules, processing engines | accent tier |
| Data | databases, caches, storage | deeper tier |
| Infrastructure | containers, networking, DevOps | darkest tier |
| External | third-party APIs, cloud services | dashed border |

Highlight key components with a `.highlight` class. Use `.tech` for smaller technical items. Add technology stack info in `<small>` tags.

---

## Layout patterns

### Architecture diagram layouts

| Layout | Best for |
| --- | --- |
| Three-column | Complex systems with cross-cutting concerns and monitoring sidebars |
| Single stack | Simple services, microservice detail views, focused documentation |
| Left sidebar | Systems with operations/monitoring emphasis, DevOps-centric views |
| Right sidebar | Systems with security/compliance emphasis, governance-focused views |
| Pipeline | Data pipelines, CI/CD flows, ETL processes, horizontal stage-based flows |
| Two-column split | Before/after comparisons, dual-system views, migration architecture |
| Dashboard | System overviews with KPIs, monitoring dashboards, executive summaries |
| Grid catalog | Service catalogs, component libraries, equal-weight microservices |
| Banner + center | Gateway-centric architectures, user-facing systems with shared infrastructure |
| Nested containers | Cloud deployments, VPC/network topology, environment isolation |

### Infocard layout families

| Family | Layouts | Best for |
| --- | --- | --- |
| Core single-topic | hero-card, quote-card, split-panel, stacked-modules | One thesis dominates, supporting content secondary |
| Metrics | metric-board, financial-snapshot, sales-brief, terminal-window | Numbers, status, operating signals |
| Sequence | timeline-flow, station-workflow, roadmap-board, staircase-progression, funnel-stack, incident-review | Stages, steps, directional movement |
| Comparison | pros-cons, quadrant-matrix, matrix-table, comparison, principle-grid | Trade-offs, prioritization, side-by-side |
| Grid | bento-grid, badge-grid, checklist-board | Repeated modules, mixed-size tiles, inventories |
| System mapping | architecture-map, layered-sidebar-map, radial-hub | Structure, adjacency, network relationships |
| Document | research-abstract, board-memo, policy-memo, education-module, healthcare-summary | Structured briefs with explicit sections |
| Governance | risk-register, compliance-audit | Ownership, control status, mitigation detail |
| Narrative | news-bulletin, org-update, customer-story, partner-brief | People, teams, customers, partner motion |

### Composition patterns for hero and proof

- **Artifact wall** — several screenshots or outputs, slightly rotated around a shared axis
- **Before / after** — show the transformation when the mechanism matters
- **System map** — show one source feeding several components or outputs
- **Annotated specimen** — enlarge one real artifact and label the decisions that matter
- **Sequence strip** — show three to six dependent stages
- **Split panel** — title on one side, project structure on the other
- **Integrated** — diagrams, paths, code, or specimens share the same grid as the title

Prefer one strong composition over several small decorative graphics.

---

## Style families

### Architecture styles (12 styles)

| Style | Suitable for |
| --- | --- |
| Steel Blue | Consulting, banking, government, RFP proposals |
| Ember Warm | Retail, education, lifestyle, cultural institutions |
| Neon Dark | Tech talks, gaming, cybersecurity dashboards |
| Stark Block | Creative studios, indie developers, tech blogs |
| Ocean Teal | Travel, logistics, green tech, weather/ocean |
| Dusk Glow | Social media, entertainment, martech, content creation |
| Rose Bloom | Fashion, luxury, wedding, premium memberships |
| Sage Forest | Healthcare, agritech, clean energy, sustainability |
| Frost Clean | Design tools, developer docs, API references, minimalist SaaS |
| Indigo Deep | Enterprise, white papers, internal platforms |
| Pastel Mix | SaaS, startups, general tech architecture |
| Slate Dark | Enterprise dark mode, internal tools, developer dashboards |

### Infocard style families (29 styles across 7 families)

| Family | Styles | Suitable for |
| --- | --- | --- |
| Warm Editorial | Editorial Warm, Customer Spotlight, Sunset Warm, Midcentury | Reflective, human, narrative, culturally textured |
| Soft Lifestyle | Soft Neutral, Slate Chalk, Education Studio | Calm, approachable, low-pressure |
| Paper & Research | Paper Minimal, Lab Journal, Academic Paper, Policy Paper, Navy Formal, Japanese Minimal, Clinical Brief | Memo, report, brief, evidence summary |
| Business & Finance | Corporate Clean, Pitch Deck VC, Sales Room, Trust Center, Partner Channel | Operational, executive, commercially credible |
| Technical | Tech Blueprint, Engineering Whiteprint, Terminal Green | Precision, systems language, implementation detail |
| Broadcast & Contrast | Bold Contrast, News Broadcast, Incident Desk, Neo Brutalism, Swiss Grid | Announce, signal urgency, strong visual punch |
| Signature Visual | Deep Night, Glassmorphism | Visual identity is part of the message |

---

## Taste checklist (anti-AI)

Before finalizing any visual — SVG asset, architecture diagram, infocard, or code-fence diagram — check against these common AI-generated visual patterns.

### Layout

- **No centered-only hero** — do not default-center titles. Prefer left-aligned or asymmetric.
- **No equal-width tiles** — three equal columns side by side is the #1 AI signature. Use `2fr 1fr`, asymmetric grids, or staggered layouts.
- **No uniform panels** — at least one panel must differ in scale, weight, or treatment.

### Typography

- **No pure black** `#000000` — use off-black (`#1a1a1a`, `#2d2a26`) or warm/cool dark.
- **No oversized-only hierarchy** — build hierarchy with weight and color, not just font-size scaling.

### Color

- **Max 1 accent color**, saturation below 80%.
- **No neon gradients** — no purple-blue AI glow, no gradient-filled headlines.
- **Consistent temperature** — do not mix warm gray and cool gray in one composition.

### Content

- **No filler data** — avoid `99.99%`, `50%`, `1234567`. Use organic numbers (`47.2%`, `3.8M`).
- **No AI phrasing** — avoid "empower", "seamless", "unleash", "next-generation".

### Spacing

- Padding and margins must be mathematically precise, no awkward gaps.
- Adjacent elements must be visually aligned.

### Visual weight

- At least one module should feel visually heavier than the others.
- Differentiate through scale, background tone, typographic weight, or accent rules.

---

## Spacing and visual accents

### Card and module spacing

- Card padding: `32px–48px` from edges (or `48–64` SVG units)
- Module gaps: `16px–24px` (or `24–36` SVG units)
- Title area: generous line-height (`1.1–1.3`) and clear separation from body
- Never crowd content against edges

### Visual accents

- Use `4px–6px` thick rules (or `6–8` SVG units) as section dividers or accent borders
- Use subtle tinted backgrounds (`rgba(0,0,0,0.03)` or style-specific tints) for secondary panels
- Accent colors: restrained — one highlight color used for rules, tags, or key numbers
- Optional: `4%` noise overlay for paper texture in editorial styles

### Content rhythm

- High-density modules: group into overview → core judgment → supporting modules → conclusion
- Ranking content: asymmetric hero + structured list (avoid equal tiles)
- Tutorial/analysis content: overview → core insight → detail blocks → boundary/caveats → summary

---

## Mind map color palettes

When creating mind maps (PlantUML `@startmindmap` or Canvas JSON), pick a palette that matches the map's purpose.

### General-purpose (pastel)

| Role | Hex | Usage |
| --- | --- | --- |
| Root | `#2196F3` | Central topic |
| Branch A | `#A5D6A7` | Category / group 1 |
| Branch B | `#90CAF9` | Category / group 2 |
| Branch C | `#CE93D8` | Category / group 3 |
| Branch D | `#FFE082` | Category / group 4 |
| Leaf | `#E0E0E0` | Detail nodes |

### Status / RAG

| Status | Hex | Usage |
| --- | --- | --- |
| Done / OK | `#C8E6C9` | Completed, healthy |
| In Progress | `#FFF9C4` | Active, warning |
| Blocked / Risk | `#FFCDD2` | Issue, danger |
| Not Started | `#E0E0E0` | Pending, neutral |

### Warm corporate

| Role | Hex |
| --- | --- |
| Root | `#1565C0` |
| Level 1 | `#FFB74D` |
| Level 2 | `#4DB6AC` |
| Level 3 | `#E0E0E0` |

### Cool tech

| Role | Hex |
| --- | --- |
| Root | `#263238` |
| Level 1 | `#00BCD4` |
| Level 2 | `#80DEEA` |
| Level 3 | `#B2EBF2` |

### Earth tone

| Role | Hex |
| --- | --- |
| Root | `#5D4037` |
| Level 1 | `#A1887F` |
| Level 2 | `#C8E6C9` |
| Level 3 | `#FFF9C4` |

Avoid pure saturated colors (`#FF0000`, `#00FF00`) — they reduce readability. Prefer soft/muted tones for backgrounds and reserve bold colors for the root only.
