# GitHub README canvas

## Reliable building blocks

GitHub README pages reliably support Markdown, tables, links, code blocks, details blocks, and embedded local images. Use HTML only for simple alignment and image sizing.

GitHub displays GIF animation but does not play animation embedded inside SVG. Keep an SVG source and static fallback for every animated visual. Read [motion-production.md](motion-production.md) before building motion.

Recommended image embed:

```html
<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Project name and plain-language value">
</p>
```

For a hybrid SVG composition, publish the rendered PNG/WebP instead of an SVG that depends on raster references:

```html
<p align="center">
  <img src="./assets/readme/hero.png" width="100%" alt="Project name and plain-language value">
</p>
```

## SVG defaults

- Use a `1200`-unit-wide `viewBox` for full-width modules.
- Typical heights: hero `300–420`, section banner `120–170`, visual explainer `320–760`.
- Include `<title>` and `<desc>` for major visual modules.
- Use system font families such as `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `PingFang SC`, and `sans-serif`.
- Judge type at its rendered size, not only by the number in the SVG. Use `900` CSS pixels as a conservative desktop acceptance width for a full-width `1200`-unit asset: essential diagram text should be at least `20` SVG units (about `15px` rendered), supporting labels at least `18` (about `13.5px`), and section titles at least `40` (about `30px`). Text below `18` units may be used only for nonessential metadata or decoration.
- Use `rx` consistently and keep all important content away from edges.

## Avoid fragile SVG features

Do not depend on:

- `<script>`
- `foreignObject`
- external stylesheets or web fonts
- essential hover states or animation
- remote image URLs inside SVG
- filters that create very large or dirty shadows

Use paths, shapes, text, patterns, gradients, clipping paths, and simple transforms.

## Markdown Viewer code fences

When the rendering context is Markdown Viewer enhanced, the README can contain code-fence diagrams that render inline:

| Fence | Renders as | Notes |
| --- | --- | --- |
| ` ```plantuml ` | SVG | PlantUML engine; supports UML, cloud, network, security, archimate, bpmn, data-analytics, iot, mindmap |
| ` ```vega-lite ` | SVG / Canvas | Vega-Lite declarative charts |
| ` ```vega ` | SVG / Canvas | Full Vega for advanced charts |
| ` ```infographic ` | HTML | Template-based infographics with YAML-like syntax |
| ` ```canvas ` | SVG | JSON Canvas spatial diagrams |
| Direct HTML (no fence) | HTML | `architecture` layer diagrams and `infocard` editorial cards |

Code-fence diagrams do not render on `github.com`. If the README must also work on GitHub, either:
1. Export the diagram as a static SVG or PNG and embed it as an image, or
2. Accept that the code fence shows as source code on GitHub and add a note pointing readers to the Markdown Viewer extension.

## Responsive behavior

GitHub scales the whole image. Preview full-width assets at both `900px` desktop and `360px` mobile widths. Small text and dense diagrams become unreadable on mobile; if required labels fail there, simplify or split the visual and keep the complete explanation in Markdown.

Avoid multi-column Markdown tables for long prose. They collapse poorly on narrow screens. Full-width visual boards can contain columns because the composition scales as one image, but text inside them must remain large.

Code-fence diagrams from PlantUML and Vega auto-layout and scale to the container width. Architecture and infocard HTML/CSS diagrams use responsive flexbox and grid layouts that adapt to content.

## Asset strategy

Store repository-specific visuals under:

```text
assets/readme/
├── hero.svg
├── hero.png
├── hero.gif
├── showcase.png
├── section-*.svg
├── workflow.svg
└── source/
    ├── hero-layout.svg
    ├── hero-subject.png
    └── hero-prompt.txt
```

Use lowercase hyphenated names. Remove discarded variants before publishing unless the user wants to retain source explorations.

## Code stats badges

When the user wants the repository homepage to show code volume, add two shields.io badges in one Markdown line directly under the hero or the language/download links. Use Markdown images, not SVG files in `assets/readme/`: the numbers must stay current without editing the README.

| Badge | Source | Setup |
| --- | --- | --- |
| Code size | `https://img.shields.io/github/languages/code-size/<owner>/<repo>` | None; shields reads the GitHub API (bytes of all detected languages) |
| Lines of code | `https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<owner>/<repo>/badges/loc.json` | A workflow that counts lines and publishes the JSON |

```markdown
![Code size](https://img.shields.io/github/languages/code-size/<owner>/<repo>) ![Lines of code](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<owner>/<repo>/badges/loc.json)
```

Translate the alt text in each language version of the README (for example `代码体积` / `代码行数`).

GitHub does not count lines of code, and no public shields service does it reliably, so the repository counts its own lines. Add `.github/workflows/code-stats.yml`, adjusting the `cloc` paths and language to the project's own source and test directories:

```yaml
name: Code stats

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  lines-of-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Count code lines (no blanks or comments) and write shields.io endpoint JSON.
      - name: Count lines of code
        run: |
          sudo apt-get update -q && sudo apt-get install -y -q cloc
          lines=$(cloc src tests --include-lang=Python --json | jq '.Python.code')
          mkdir badge
          jq -n --arg lines "$lines" \
            '{schemaVersion: 1, label: "lines of code", message: $lines, color: "blue"}' > badge/loc.json
      # Keep the badge data on its own single-commit branch instead of adding commits to main.
      - name: Publish badge data
        run: |
          cd badge
          git init -q -b badges
          git config user.name "github-actions[bot]"
          git config user.email "41898283+github-actions[bot]@users.noreply.github.com"
          git add loc.json
          git commit -q -m "Update lines of code badge"
          git push -f "https://x-access-token:${{ github.token }}@github.com/${{ github.repository }}.git" badges
```

Rules:

- Only for public repositories: shields.io and `raw.githubusercontent.com` cannot read private ones.
- The `badges` branch is generated data. Tell the user not to delete it with other merged branches, and not to protect it (the workflow force-pushes).
- Order matters. GitHub proxies README images through its camo cache, and a badge viewed before `badges/loc.json` exists is cached as `custom badge: resource not found`, which can outlive the shields `max-age`. Run the workflow first (`gh workflow run code-stats.yml` on the default branch, or merge the workflow before the README change), confirm the JSON URL returns `200`, then publish the README line.
- If the broken badge is already cached, verify the JSON URL and the direct shields URL first; if both are fine, change the badge URL (for example append `&cacheSeconds=3600`) so camo fetches it fresh.

## Accessibility and trust

- Write alt text that communicates the purpose, not merely "banner".
- Do not hide install commands or critical instructions inside images.
- Use real outputs and clearly label conceptual visuals.
- Check that text remains readable on both GitHub light and dark page backgrounds; the safest full-width SVG supplies its own background.
- For code-fence diagrams, the Markdown source text itself serves as an accessible fallback on GitHub.
