# Editorial static diagrams

Use this production branch for GitHub-native diagrams that explain repository code but do not need Archify's interactive system-map runtime or PlantUML's domain notation. The published artifact is a static SVG by default; PNG is allowed when raster output is necessary.

This branch borrows the strongest constraints from editorial diagram systems—type routing, deliberate deletion, destination-aware sizing, and evidence ledgers—without copying a template library or introducing remote fonts.

## When to use it

Choose editorial-static for:

- decision logic and code paths → `flowchart`
- module, package, or build relationships → `dependency`
- classes and typed relationships → `class`
- domain entities and relationships → `er`
- physical tables, keys, and indexes → `db-schema`
- hierarchical decomposition → `tree`
- repository or release events → `timeline`
- cross-role handoffs → `swimlane`

Do not use it for:

- runtime/service architecture, request traces, data lineage, or retry lifecycles that need typed validation → Archify
- AWS/Azure/GCP/Kubernetes, BPMN, ArchiMate, network, or security notation → PlantUML
- quantitative charts → Vega/Vega-Lite
- hero title systems or decorative modules → hand-authored project-native SVG
- a relationship simple enough for one sentence or a small Markdown table

## Freeze four output dials

Record these decisions before drawing:

```text
Type: flowchart | dependency | class | er | db-schema | tree | timeline | swimlane
Format: svg | png
Size: doc-inline | doc-wide
Detail: faithful | balanced | simplified
Audience: engineer | mixed | executive
```

Defaults for a README body diagram are:

```text
Format: svg
Size: doc-inline
Detail: balanced
Audience: mixed
```

### Size presets

| Preset | viewBox | Use |
| --- | --- | --- |
| `doc-inline` | `0 0 960 600` | Normal README body diagram |
| `doc-wide` | `0 0 1200 675` | Wide proof or architecture section |

Use at least `40` units of outer safe area for `doc-inline` and `48` for `doc-wide`. Essential labels must still satisfy the rendered-size rules in [readme-canvas.md](readme-canvas.md). If the diagram is unreadable at `360px`, simplify or split it; never repair density by shrinking required labels.

## Evidence before geometry

When the diagram claims to represent repository code:

1. Inspect the relevant entry points, callers, domain types, configuration, tests, and generated code boundaries.
2. Write an evidence list before drawing. Every important node or branch must be supported by at least one repository-relative path and line range.
3. Distinguish observed code facts from conceptual grouping. Do not turn a folder name into a runtime service without evidence.
4. Preserve identifiers when the audience is `engineer`; expand them without changing meaning for `mixed`; use capabilities only when the code supports that interpretation for `executive`.

Neither this branch nor its output checker reverse-engineers the repository automatically. The Agent extracts facts; the manifest and review gate make those facts auditable.

## Complexity budget

Default limits:

| Item | Limit |
| --- | ---: |
| Primary nodes | 9 |
| Connectors | 12 |
| Focal elements | 2 |
| Swimlanes | 5 |
| Tree depth | 4 |
| ER entities | 8 |
| Class boxes | 7 |
| Tables | 5 |

`faithful` may use up to 18 nodes only when every node belongs to one of 2–4 labeled zones. Above 18 nodes, split into an overview and one or more detail diagrams.

When over budget, reduce in this order:

1. Remove decorative notes and duplicate labels.
2. Merge exact replicas into one node with a count.
3. Collapse leaf-only groups into a named capability.
4. Remove degree-one sinks that do not change the main story.
5. Remove cross-cutting infrastructure unless it is the subject.
6. Split into overview and detail.

Never silently drop source-backed facts. Record every merge, collapse, or meaningful omission in the fidelity ledger.

## Visual grammar

- Apply the visual system frozen for the README; do not import another engine's house palette.
- Use one accent on at most two focal elements.
- Use system font stacks only. Remote Google Fonts and `@import` are forbidden in published SVG.
- Draw connectors before opaque nodes.
- Use rounded orthogonal connectors for off-axis nodes; diagonal connector spaghetti fails review.
- Give multiple connectors on one node edge distinct attachment points.
- Keep labels off connector strokes with an opaque background mask and visible gap.
- Do not route a connector behind an unrelated opaque node.
- Include a first-child `<title>`, a `<desc>`, `role="img"`, and a resolving `aria-labelledby`.

## Asset and manifest contract

Store published diagrams and semantic sources separately:

```text
assets/readme/
├── diagrams/
│   └── request-flow.svg
└── source/
    ├── request-flow.diagram.json
    └── request-flow.html          # optional working source
```

Add these attributes to the root of a published SVG:

```svg
<svg
  viewBox="0 0 960 600"
  data-diagram-engine="editorial-static"
  data-readme-preset="doc-inline"
  role="img"
  aria-labelledby="request-flow-title request-flow-desc">
```

The required `source/<slug>.diagram.json` manifest is:

```json
{
  "schema_version": 1,
  "engine": "editorial-static",
  "type": "flowchart",
  "format": "svg",
  "size": "doc-inline",
  "detail": "balanced",
  "audience": "mixed",
  "source_backed": true,
  "evidence": [
    {"path": "src/router.py", "lines": "18-64"}
  ],
  "counts": {
    "nodes": 7,
    "connectors": 8,
    "focal": 1,
    "zones": 0
  },
  "fidelity": {
    "merged": [],
    "collapsed": [],
    "dropped": ["debug-only logging branch"]
  }
}
```

For a conceptual diagram, set `source_backed` to `false`, use an empty `evidence` array, and make the conceptual status explicit in the SVG description and README caption.

## Delivery

1. Save the static asset under `assets/readme/diagrams/`.
2. Save and validate the manifest under `assets/readme/source/`.
3. Embed the static asset with meaningful alt text.
4. Report the fidelity ledger whenever content was merged, collapsed, or dropped.
5. Run `verify_readme.py`; it checks the diagram path, manifest fields, declared complexity budget, evidence paths and line ranges, and SVG marker/preset agreement.
6. Render at `900px` and `360px`; inspect label clipping, connector ambiguity, contrast, and whether the main path is obvious.

The manifest proves declared provenance and output decisions. It does not replace code inspection or perceptual visual review.

## Design influence

The type-routing, output-dial, complexity-budget, degrade-ladder, and fidelity-ledger ideas are informed by the MIT-licensed [Diagram Design](https://github.com/cathrynlavery/diagram-design) project. This skill does not bundle its templates, fonts, icons, or implementation. If future work copies source or substantial assets, preserve the upstream copyright and MIT notice.
