# Output verification

A mandatory compliance gate that runs before declaring any README or asset task complete. The gate checks four dimensions. Every dimension must pass before handoff. If any check fails, fix the gap and re-run the gate — do not declare success with known failures.

The goal is to prevent the most common failure mode: delivering a visual redesign (hero SVG, directory structure, table sorting) while skipping the content architecture, visual system rules, and quality bar that the skill defines.

## How to use this gate

After completing step 7 (Build the visual layer) and before step 9 (Hand off safely), walk through every checklist below. For programmatic checks, run:

```bash
python3 scripts/verify_readme.py /path/to/repository/README.md
```

Then manually verify the items the script cannot check. Report a summary table of pass/fail for each dimension.

---

## Dimension 1: Content architecture compliance

Verifies that the README content follows the sequencing and editing rules from [content-architecture.md](content-architecture.md), not just the visual layout.

### 1.1 First-screen test

- [ ] A new visitor can understand "What is this?" from the hero alone.
- [ ] A new visitor can understand "What can it do for me?" from the hero or the next module.
- [ ] A new visitor can see "What should I look at next?" without scrolling past proof.

### 1.2 Content sequence

- [ ] The reading order follows `Value → Proof → Mechanism → First use → Detail` (or a justified alternative). *(Programmatic: check 1.7 verifies relative stage order via `verify_readme.py`)*
- [ ] The README does not begin with architecture, contributor instructions, a command, or a long table of contents. *(Programmatic: check 1.4)*
- [ ] An example appears before the long explanation.

### 1.3 Editing rules

- [ ] Internal jargon is replaced with a concrete outcome.
- [ ] The mechanism is explained once; repeated promises are removed.
- [ ] The shortest working install path appears before advanced configuration.
- [ ] Limitations are visible when they affect user choice.
- [ ] At least one example succeeds end-to-end (not just disconnected snippets).
- [ ] No sentence that could appear in any README without knowing the project — cut generic filler.

### 1.4 Visual-to-text division

- [ ] Commands, links, API details, and installation steps are in Markdown, not inside SVG.
- [ ] Visuals carry hierarchy, identity, comparison, sequence, and proof — not instructions.
- [ ] If a sentence needs to be copied, searched, translated, or frequently updated, it is not inside an image.

---

## Dimension 2: Visual system compliance

Verifies that visual assets follow the production rules from [svg-production.md](svg-production.md), [readme-canvas.md](readme-canvas.md), and [design-system.md](design-system.md).

### 2.1 Visual system spec

- [ ] A visual system spec was frozen before drawing: palette (3–5 hex values), typography (font stack + scale), shape (radius + stroke + spacing), motif (one project-specific cue), composition (one rhythm).
- [ ] The palette uses at most one accent color with saturation below 80%.
- [ ] No pure black `#000000` — use off-black (`#1a1a1a`, `#333`).

### 2.2 SVG asset structure

- [ ] Every full-width SVG has a `1200`-unit `viewBox`.
- [ ] Every SVG has `<title>` and `<desc>` elements.
- [ ] Every SVG uses system font stacks (no remote fonts).
- [ ] Important content is at least `48–64` units from edges.
- [ ] No `<script>`, `foreignObject`, external stylesheets, web fonts, essential animation, or remote image URLs inside SVG.

### 2.3 Text legibility

- [ ] Hero or project title text is at least `48` SVG units.
- [ ] Section title text is at least `40` SVG units.
- [ ] Essential diagram text is at least `20` SVG units.
- [ ] Supporting labels are at least `18` SVG units.
- [ ] A `360px` mobile preview was checked; if required labels fail, density was reduced or the visual was split.

### 2.4 Diagram engine compliance

- [ ] Code-fence diagrams use the correct fence: ` ```plantuml `, ` ```vega-lite `, ` ```vega `, ` ```infographic `, ` ```canvas `.
- [ ] PlantUML diagrams start with `@startuml` and end with `@enduml` (or `@startmindmap`/`@endmindmap`).
- [ ] Vega/Vega-Lite JSON includes `$schema` and uses valid JSON (double quotes, no trailing commas).
- [ ] Infographic uses space-separated `key value` syntax (no colons), correct template names, `desc` not `description`, `items` not `steps`.
- [ ] Architecture and infocard HTML is embedded directly (no ` ```html ` fence), with no empty lines in the HTML structure.
- [ ] Archify diagrams (when used) passed `validate`/`deliver`, publish a static PNG/SVG Share Card (not HTML-only on GitHub), retain the JSON IR under source, and do not invent unsupported topology.
- [ ] Exported diagram images (for GitHub-native context) use the frozen project palette, not the engine's house theme, or an intentionally chosen Archify preset that still reads as project-native.

### 2.5 Motion compliance

- [ ] GIF is opt-in only — never produced without explicit user request.
- [ ] Static SVG source is kept alongside any GIF.
- [ ] GIF is under 5 MB; full-width hero GIF is under 2 MB.

---

## Dimension 3: Quality bar compliance

Verifies the quality standards from the SKILL.md quality bar section.

### 3.1 Project-native design

- [ ] Removing the repository name would make the hero unusable for an unrelated project.
- [ ] The hero's visual material comes from the project (real screenshots, outputs, diagrams, code) — not generic decoration.
- [ ] The design looks native to this project, not to this skill.

### 3.2 Proof and clarity

- [ ] Real proof appears before abstract claims.
- [ ] The README is shorter or clearer than before — not merely more decorated.
- [ ] Every visual module has a specific communication job.

### 3.3 Graceful degradation

- [ ] Alt text communicates the purpose, not merely "banner" or "image".
- [ ] When images fail to load, the README still works: headings, commands, and links remain meaningful.
- [ ] Install commands and critical instructions are not hidden inside images.

### 3.4 Taste checklist (anti-AI)

- [ ] No centered-only hero — prefer left-aligned or asymmetric.
- [ ] No equal-width tiles — three equal columns is the #1 AI signature.
- [ ] No uniform panels — at least one panel differs in scale, weight, or treatment.
- [ ] No oversized-only hierarchy — hierarchy uses weight and color, not just font-size.
- [ ] No neon gradients — no purple-blue AI glow, no gradient-filled headlines.
- [ ] No AI filler phrasing — avoid "empower", "seamless", "unleash", "next-generation".
- [ ] No filler data — avoid `99.99%`, `50%`, `1234567`; use organic numbers.
- [ ] Consistent color temperature — no mixing warm gray and cool gray.

---

## Dimension 4: Workflow compliance

Verifies that the workflow steps were actually followed, not just the final output.

### 4.1 Mode and context

- [ ] The execution mode was confirmed: README mode or asset-only mode.
- [ ] The rendering context was confirmed: GitHub-native or Markdown Viewer enhanced.
- [ ] In asset-only mode, the README was not modified unless embedding was explicitly approved.

### 4.2 Story and system

- [ ] The project story was extracted before drawing: audience, one-sentence value, primary proof, first successful action, visual theme.
- [ ] A visual system spec was frozen before producing assets.
- [ ] The motif was derived from the project, not applied from a template.

### 4.3 Verification executed

- [ ] `scripts/audit_readme.py` was run and passed (in README mode).
- [ ] `scripts/verify_readme.py` was run and all programmatic checks passed.
- [ ] Every SVG was rendered and visually inspected.
- [ ] Wide (`900px`) and narrow (`360px`) layouts were checked.
- [ ] Dark and light GitHub theme contrast was checked.

### 4.4 Reporting

- [ ] A summary of what changed was provided.
- [ ] Files deliberately left untouched were reported.
- [ ] What remains intentionally plain was explained.

---

## Summary report format

After running all checks, produce a summary like:

```text
Verification summary
=====================
Dimension 1 — Content architecture:    PASS (12/12)
Dimension 2 — Visual system:            PASS (15/15)
Dimension 3 — Quality bar:              PASS (10/10)
Dimension 4 — Workflow compliance:      PASS (10/10)

Programmatic checks:  8 passed, 0 failed
Manual checks:        39 passed, 0 failed

Overall: PASS
```

If any check fails:

```text
Dimension 1 — Content architecture:    FAIL (10/12)
  ✗ 1.2 Content sequence: README begins with a table of contents before value
  ✗ 1.3 Editing rules: install path appears after configuration options

Programmatic checks:  7 passed, 1 failed
  ✗ AI filler phrase detected: "seamless integration"

Overall: FAIL — fix the gaps above before declaring complete.
```

Do not declare the task complete until the overall result is PASS. If a check is not applicable (e.g., motion checks when no GIF was requested), mark it N/A and exclude it from the count.
