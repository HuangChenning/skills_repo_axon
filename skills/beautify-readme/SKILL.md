---
name: beautify-readme
description: Redesign GitHub README homepages or create project-native pure SVG, hybrid SVG-composed PNG/WebP, code-fence diagrams, optional Archify system maps, and opt-in animated GIF assets. Use when a user asks to beautify, redesign, rebrand, visually upgrade, simplify, or audit a GitHub README; create a hero, section headers, diagrams, badges, motion graphics, showcase modules, or other README assets; add PlantUML, Vega, infographic, architecture, or Archify architecture/workflow/sequence/dataflow/lifecycle diagrams to a README; or turn a repository homepage into a cohesive visual story. Supports both GitHub-native rendering and Markdown Viewer enhanced diagrams.
---

# Beautify README

Turn a repository homepage or requested visual asset into a concise, theme-specific visual story. Treat Markdown as the content layer, deterministic SVG as the layout system, generated raster material as an optional visual ingredient, and diagram engines as structured visual production aids. Support both GitHub-native rendering and Markdown Viewer enhanced diagrams so the README works everywhere.

## Rendering contexts

Choose a rendering context before producing assets. The context determines which techniques are safe and which diagram engines are available.

### GitHub-native context

The README renders on `github.com` using GitHub's built-in Markdown renderer. This is the safest and most portable context.

- Use hand-authored SVG files embedded as `<img>` for heroes, section banners, and deterministic design modules.
- GitHub strips `<script>`, `foreignObject`, external stylesheets, web fonts, and animation inside SVG. Use only paths, shapes, text, patterns, gradients, clipping paths, and simple transforms.
- Use GIF for approved motion that must play directly on GitHub.
- Use Markdown for body copy, commands, tables, links, and details.
- Diagram engines (PlantUML, Vega, Archify, etc.) may be used as production aids: generate the diagram, export a static SVG or PNG, and embed the image file. Keep the semantic source alongside the exported asset. For polished system maps (architecture, workflow, sequence, dataflow, lifecycle), prefer the optional Archify branch in [references/diagram-engines.md](references/diagram-engines.md) when available.

### Markdown Viewer enhanced context

The README renders in a Markdown Viewer browser extension (Chrome, Edge, Firefox, VS Code, Obsidian) that supports code-fence diagrams. This unlocks richer, editable diagrams that live directly in the Markdown source.

- Use code-fence diagrams: ` ```plantuml `, ` ```vega-lite `, ` ```vega `, ` ```infographic `, ` ```canvas ` for diagrams that render inline.
- Use direct HTML embedding (no code fence) for `architecture` layer diagrams and `infocard` editorial cards.
- These diagrams are editable in the Markdown source and re-render on every view, but they do not render on `github.com` itself. If the README must also work on GitHub, export the key diagrams as static SVG or PNG and embed them as fallback images, or provide a note pointing readers to the Markdown Viewer extension.

### Choosing the context

| Priority | Recommendation |
| --- | --- |
| Must work on github.com for everyone | GitHub-native context |
| Team uses Markdown Viewer and wants live-editable diagrams | Markdown Viewer enhanced context |
| Both audiences matter | GitHub-native for the hero and first screen; add code-fence diagrams lower in the README as an enhancement, or export them as images |

When the user does not specify, default to GitHub-native. Read [references/diagram-engines.md](references/diagram-engines.md) for the full diagram engine catalog and syntax rules.

## Workflow

### 1. Confirm the mode before editing

Use exactly one execution mode:

- **README mode** — improve the whole README: information order, copy hierarchy, proof, Markdown, and visual system.
- **Asset-only mode** — create only the requested static SVG, diagram, or visual asset set. Static SVG is the default. Only after the user explicitly opts into meaningful motion, optionally deliver a GitHub-safe GIF while keeping the SVG as the editable fallback. Do not rewrite, reorder, or embed anything in the README unless the user explicitly adds that scope.

If the mode is not explicit, ask one compact question before making changes:

> Would you like me to improve the whole README or only create visual assets? If asset-only, tell me whether you need a hero, section headers, workflow, badge, motion graphic, diagram, or a coordinated set.

When a hero, badge, workflow, or diagram has meaningful motion and the user has not specified static or animated output, ask one compact follow-up:

> Should this stay as a static SVG, or would you like a GitHub-safe GIF animation with the SVG kept as the editable fallback?

GIF is opt-in and never the default. If the user declines, does not answer, or has no meaningful motion case, continue with static SVG only. Do not ask when motion would be purely decorative or the user already chose the output. Read-only inspection is allowed before the answer when it helps understand the repository. Once the user chooses asset-only mode, expanding into README edits requires new authorization.

If the user explicitly asks only for an audit, audit without editing and do not force the two-mode question.

### 2. Inspect before designing

- Read the existing README, repository tree, package metadata, screenshots, examples, design tokens, logo, and real outputs.
- In asset-only mode, inspect only the context needed to design the requested assets.
- For a GitHub URL, inspect the current remote page and default branch before proposing changes.
- Identify the audience, the problem solved, the clearest proof, the shortest path to first use, and any claims that lack evidence.
- Preserve unrelated user changes. Start read-only; do not commit, push, rename, or publish without explicit authorization.

### 3. Confirm the visual implementation before creating hero-like assets

For a hero, large banner, showcase board, or expressive title system where both implementations are viable, explain the difference and ask before producing the asset:

> Which implementation would you like?
>
> - **Pure SVG** — fully deterministic, lightweight, sharply scalable, easy to edit, and best for typography, diagrams, code, icons, and geometric scenes. It does not use image generation and is weaker for realistic people, organic texture, complex materials, or cinematic lighting.
> - **Hybrid SVG composition** — use SVG for layout and typography, optionally use ImageGen for a project-specific raster subject, remove its background when appropriate, and compose the layers into a final PNG/WebP.

Do not ask this question when the user already chose an implementation, requested an audit, or the asset is obviously deterministic (workflow, architecture diagram, badge, compact section header, code-native illustration). Prefer real screenshots, outputs, logos, or existing project art over generated material.

If the user delegates the decision, default to pure SVG unless generated or photographic material clearly communicates the repository's identity or mechanism better. Do not begin ImageGen work until the user selects hybrid composition or explicitly delegates the choice.

### 4. Extract the project story

Write these before drawing:

```text
Audience:
One-sentence value:
Primary proof:
First successful action:
Visual theme:
```

Do not invent adoption, benchmarks, compatibility, testimonials, or features. Prefer a real screenshot, output, diagram, or generated artifact over decorative stock imagery.

### 5. Define a theme-specific visual system

Read [references/visual-direction.md](references/visual-direction.md) and [references/design-system.md](references/design-system.md). Freeze a compact art-direction spec:

```text
Palette: background / foreground / primary / accent / muted
Typography: system font stack / scale / weight contrast
Shape: radius / stroke / grid / spacing
Motif: one recurring project-specific visual cue
Composition: calm / editorial / technical / playful / cinematic
```

Derive the motif from the project. A terminal tool may use prompts and cursor marks; an icon system may use keylines and cutouts; a research project may use coordinates and evidence labels. Never apply the same template to every repository. When the content has a clear tone (philosophical, technical, literary, scientific, business, creative), apply the tone-sensing palette from [references/design-system.md](references/design-system.md).

Before designing the hero, read [references/project-native-hero.md](references/project-native-hero.md). Build the title from project content rather than treating it as a banner placed above the proof.

### 6. Execute only the selected mode

#### README mode

Decide how deeply the README needs to change:

- **Full redesign** — restructure the story and build a new visual system.
- **Visual refresh** — preserve the information architecture while replacing weak or inconsistent presentation.

Use the smallest change inside README mode that can produce a meaningful improvement. A strong default reading order is:

1. Hero: name + plain-language value.
2. Proof: screenshots, outputs, or a showcase wall.
3. What it is: one short explanation.
4. Why it is different: mechanism, not slogans.
5. How it works: a short process or architecture.
6. How to use: install + first command.
7. Limits, compatibility, license, or contribution details when relevant.

Put the example before the long explanation. Remove repeated promises and internal implementation detail that does not help adoption.

#### Asset-only mode

- Confirm the requested asset type, whether the user wants one asset or a coordinated set, and whether a meaningful motion candidate should stay static or become a GIF.
- Derive exact copy and style from the repository when they are unambiguous; ask only for missing decisions that would materially change the result.
- Create assets under `assets/readme/` or another user-approved path and provide rendered previews.
- Follow the confirmed visual implementation. Default to pure, maintainable SVG for title systems, section headers, diagrams, badges, and deterministic modules.
- For Markdown Viewer enhanced diagrams, use the appropriate code fence and follow [references/diagram-engines.md](references/diagram-engines.md).
- Keep one shared visual grammar across a set, but give every asset a specific communication job.
- Do not change README text, reading order, embeds, or links. Offer an embed snippet separately when useful; only insert it after explicit approval.

### 7. Build the visual layer

Read [references/readme-canvas.md](references/readme-canvas.md), [references/svg-production.md](references/svg-production.md), and [references/design-system.md](references/design-system.md) before creating assets.

- Use SVG for the hero, section banners, deterministic design modules, and GitHub-native diagrams.
- Use code-fence diagram engines (PlantUML, Vega, infographic, canvas, architecture, infocard) for Markdown Viewer enhanced diagrams. Read [references/diagram-engines.md](references/diagram-engines.md) for the engine selection guide and critical syntax rules.
- For polished GitHub-native system maps (architecture, workflow, sequence, dataflow, lifecycle), use the optional **Archify** production branch when the Archify skill/CLI is available: author typed JSON → `validate` → `deliver` → export a Share Card or static PNG/SVG → embed the image and keep the JSON (and optional HTML) under `assets/readme/source/`. Do not embed interactive Archify HTML as the sole GitHub image.
- Use PNG/WebP for screenshots, generated art, photo material, Archify Share Cards, and complex compositing. Use GIF only for approved motion.
- When hybrid composition is selected, read [references/hybrid-svg-production.md](references/hybrid-svg-production.md), use the `imagegen` Skill for generation, and keep exact copy out of the generated raster layer.
- Keep body copy, commands, tables, links, and details in Markdown.
- Prefer a `1200`-unit-wide SVG `viewBox`, `width="100%"` embeds, system fonts, semantic alt text, and rounded containers.
- Use one reusable component grammar, but vary the art direction by repository theme.
- Let the hero absorb a real project diagram, screenshot, code fragment, output, or artifact when it makes the first screen more useful.

When a diagram engine exports an SVG or PNG for GitHub-native embedding, apply the frozen project palette rather than the engine's house theme where possible, use system fonts, and inspect the output for `<script>`, `foreignObject`, remote resources, and clipped labels. For Archify exports, choose the closest visual preset/theme and keep the IR source editable.

Do not rasterize the whole README. Avoid decorative borders and heavy shadows unless the theme genuinely calls for them.

### 8. Verify output compliance (mandatory gate)

This step is a mandatory gate — do not proceed to step 9 until all checks pass. The goal is to prevent the most common failure mode: delivering a visual redesign (hero SVG, directory structure, table sorting) while skipping the content architecture, visual system rules, and quality bar that this skill defines.

Read [references/output-verification.md](references/output-verification.md) for the full four-dimension checklist before proceeding.

#### 8a. Run programmatic checks

In README mode, run both scripts:

```bash
python3 scripts/audit_readme.py /path/to/repository/README.md
python3 scripts/verify_readme.py /path/to/repository/README.md
```

`verify_readme.py` checks four dimensions programmatically:

- **Content architecture** — sections present, install path, alt text, no TOC-first
- **Visual system** — SVG viewBox/title/desc, no fragile features, no pure black, system fonts
- **Quality bar** — no AI filler phrases, no filler data, image references valid
- **Diagram engine syntax** — PlantUML start/end, Vega JSON validity, infographic syntax; Archify validate/deliver and static embed checks are manual

If any programmatic check fails, fix the gap and re-run. Do not declare success with known failures.

#### 8b. Run manual checks

Walk through every checklist item in [references/output-verification.md](references/output-verification.md) that the script cannot cover:

- **Dimension 1 (Content architecture)** — first-screen test, content sequence, editing rules, visual-to-text division
- **Dimension 2 (Visual system)** — visual system spec frozen, text legibility at 900px and 360px, diagram engine compliance, motion compliance
- **Dimension 3 (Quality bar)** — project-native design, proof and clarity, graceful degradation, taste checklist (anti-AI)
- **Dimension 4 (Workflow compliance)** — mode and context confirmed, story and system extracted, verification executed, reporting complete

#### 8c. Produce a verification summary

Report a summary table showing pass/fail for each dimension:

```text
Verification summary
=====================
Dimension 1 — Content architecture:    PASS (12/12)
Dimension 2 — Visual system:            PASS (15/15)
Dimension 3 — Quality bar:              PASS (10/10)
Dimension 4 — Workflow compliance:      PASS (10/10)

Programmatic checks:  15 passed, 0 failed
Manual checks:        32 passed, 0 failed

Overall: PASS
```

If any dimension has failures, the overall result is FAIL. Fix the gaps and re-run before proceeding to step 9. Do not skip, defer, or mark known failures as acceptable.

#### 8d. Visual inspection

- Render a local GitHub-width preview or inspect the README on a local Markdown renderer.
- Check wide (`900px`) and narrow (`360px`) layouts, image legibility, clipped SVG text, missing assets, excessive file size, and dark/light-mode contrast.
- Visually inspect the hero, every section transition, and the final call to action.
- In asset-only mode, render and inspect every requested asset at GitHub content width; for GIFs, inspect entry, settled hold, exit, and loop boundary.
- For code-fence diagrams, verify they render correctly in a Markdown Viewer and check syntax against the rules in [references/diagram-engines.md](references/diagram-engines.md).
- For Archify diagrams, confirm `validate`/`deliver` passed, the published file is a static PNG/SVG (not HTML-only), the IR source is retained, and labels remain legible at GitHub width.
- Report what changed, what remains intentionally plain, and which files were deliberately left untouched.

### 9. Hand off safely

Show the local preview and diff first. Only commit, push, open a PR, merge, rename a repository, or publish assets when the user explicitly asks.

## Diagram engine quick reference

When the README needs structured diagrams, pick the engine that matches the job. Read [references/diagram-engines.md](references/diagram-engines.md) for full syntax rules and critical pitfalls before writing any code fence.

| Need | Engine | Code fence / output | Context |
| --- | --- | --- | --- |
| Polished runtime / service architecture | Archify — `architecture` | PNG/SVG Share Card | GitHub-native |
| CI/CD, approvals, tool-call workflows | Archify — `workflow` | PNG/SVG Share Card | GitHub-native |
| API / cache / auth call traces | Archify — `sequence` | PNG/SVG Share Card | GitHub-native |
| Pipelines, lineage, sensitivity boundaries | Archify — `dataflow` | PNG/SVG Share Card | GitHub-native |
| States, retries, waits, outcomes | Archify — `lifecycle` | PNG/SVG Share Card | GitHub-native |
| Software modeling (class, sequence, activity, state, component) | PlantUML — `uml` | ` ```plantuml ` | Both |
| Cloud architecture (AWS, Azure, GCP, K8s) | PlantUML — `cloud` | ` ```plantuml ` | Both |
| Network topology | PlantUML — `network` | ` ```plantuml ` | Both |
| Security architecture | PlantUML — `security` | ` ```plantuml ` | Both |
| Enterprise architecture (ArchiMate) | PlantUML — `archimate` | ` ```plantuml ` | Both |
| Business process (BPMN) | PlantUML — `bpmn` | ` ```plantuml ` | Both |
| Data pipeline / analytics | PlantUML — `data-analytics` | ` ```plantuml ` | Both |
| IoT architecture | PlantUML — `iot` | ` ```plantuml ` | Both |
| Mind map (hierarchical) | PlantUML — `mindmap` | ` ```plantuml ` | Both |
| Data charts (bar, line, scatter, heatmap) | Vega-Lite | ` ```vega-lite ` | Both |
| Advanced charts (radar, word cloud) | Vega | ` ```vega ` | Both |
| KPI dashboard, timeline, SWOT, funnel | Infographic | ` ```infographic ` | Viewer |
| Concept map, knowledge graph | Canvas (JSON) | ` ```canvas ` | Viewer |
| Layered system architecture (editable HTML) | Architecture (HTML/CSS) | direct HTML | Viewer |
| Editorial information cards | Infocard (HTML/CSS) | direct HTML | Viewer |

For GitHub-native context, generate the diagram with the engine, export a static SVG or PNG, and embed it as an image file. For Markdown Viewer enhanced context, write the code fence directly in the README. Archify is optional and requires its skill/CLI; if unavailable, fall back to PlantUML, Architecture HTML, or hand-authored SVG.

## Quality bar

- The first screen explains the project without requiring prior knowledge.
- The design looks native to this project, not to this Skill.
- The hero's visual material comes from the project and is not generic decoration.
- Generated material is optional, project-specific, and never replaces stronger real proof.
- Every visual module has a communication job.
- Real proof appears before abstract claims.
- The README becomes shorter or clearer, not merely more decorated.
- The result still works when images fail: alt text, headings, commands, and links remain meaningful.
- Removing the repository name should not make the hero reusable for an unrelated project.
- Asset-only mode leaves the README byte-for-byte unchanged unless the user explicitly approved embedding or copy edits.
- Code-fence diagrams follow the critical syntax rules in [references/diagram-engines.md](references/diagram-engines.md) and render without errors.
- Design choices pass the taste checklist in [references/design-system.md](references/design-system.md): no centered-only heroes, no equal-width tiles, no pure black, no neon gradients, no AI filler phrasing.

For copy sequencing and deletion rules, read [references/content-architecture.md](references/content-architecture.md).

## Reference files

| File | When to read |
| --- | --- |
| [references/content-architecture.md](references/content-architecture.md) | Before restructuring README content or deciding information order |
| [references/readme-canvas.md](references/readme-canvas.md) | Before building any GitHub-native visual asset |
| [references/svg-production.md](references/svg-production.md) | Before hand-authoring SVG for heroes, banners, or diagrams |
| [references/visual-direction.md](references/visual-direction.md) | Before freezing the art-direction spec |
| [references/design-system.md](references/design-system.md) | Before choosing colors, typography, layout, or checking taste |
| [references/project-native-hero.md](references/project-native-hero.md) | Before designing the hero or title system |
| [references/hybrid-svg-production.md](references/hybrid-svg-production.md) | When hybrid SVG + raster composition is selected |
| [references/motion-production.md](references/motion-production.md) | Before animating or converting to GIF |
| [references/diagram-engines.md](references/diagram-engines.md) | Before using any diagram engine, including optional Archify system maps |
| [references/output-verification.md](references/output-verification.md) | Before declaring any task complete — mandatory compliance gate |

## Invocation examples

```text
Use $beautify-readme to redesign this repository homepage around its developer-tool theme.
```

```text
Use $beautify-readme to create one SVG hero and three section headers without modifying the README.
```

```text
Use $beautify-readme to add a PlantUML architecture diagram and a Vega-Lite benchmark chart to this README for Markdown Viewer rendering.
```

```text
Use $beautify-readme to add a GitHub-native How it works diagram via Archify: validate the architecture IR, export a Share Card PNG, and keep the JSON source.
```

```text
Use $beautify-readme to create a hybrid hero: SVG typography and layout, plus an ImageGen character cutout, with a final PNG and editable source layers.
```

```text
Use $beautify-readme to beautify this repository; if the scope is unclear, ask whether I want a whole-README redesign or asset-only visuals.
```
