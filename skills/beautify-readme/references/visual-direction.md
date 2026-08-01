# Theme-specific visual direction

## Derivation order

Choose the visual system in this order:

1. Real product semantics: what the repository actually helps people do.
2. Existing identity: logo, UI tokens, screenshots, diagrams, code style, or documentation tone.
3. Audience expectation: technical trust, creative energy, research clarity, or operational confidence.
4. Visual finish: palette, type scale, material, motif, and composition.

Do not start with a fashionable finish and force the project into it.

## Theme cues

| Repository type | Useful visual cues | Avoid |
| --- | --- | --- |
| CLI / developer tool | terminal rhythm, cursor, monospace accents, logs, precise grids | fake code, neon overload |
| AI product | relationships, transformations, evidence, input/output contrast | generic glowing brain imagery |
| Design resource | keylines, material samples, artboards, crop marks, specimen walls | portfolio decoration with no proof |
| Data / research | coordinates, annotations, charts, source labels, measured spacing | dashboard clichés unrelated to the data |
| Library / framework | modules, composition, API flow, dependency structure | pretending documentation is a marketing site |
| Creator project | voice, editorial imagery, sequences, human scale | generic SaaS landing-page sections |

## Monochrome technical direction

For infrastructure, security, research, systems, hardware, and other serious technical repositories, consider a black-and-white direction before adding brand color:

- Use black, warm white, and two neutral grays.
- Use a strict grid, thin rules, large numbers, mono metadata, and restrained diagrams.
- Mix sans-serif, monospace, or a sober serif only when the project supports it.
- Replace decorative cards with architecture, specifications, boundaries, results, or real interfaces.
- Avoid gradients, glossy materials, playful rounded tiles, and ornamental shadows.

Monochrome should still come from the project. A security repository may emphasize boundaries and permissions; hardware may emphasize dimensions, interfaces, and real objects; research may emphasize methods, results, and limits.

## Tone-sensing palette

When no explicit style is chosen, auto-select a color palette based on the content topic. Scan content keywords and match the closest tone. This applies to both SVG assets and code-fence diagrams.

| Content tone | Background | Accent | Trigger keywords |
| --- | --- | --- | --- |
| Philosophical | `#FAF8F4` | `#7C6853` | cognition, thinking, meaning, philosophy, essence |
| Technical | `#F5F7FA` | `#3D5A80` | architecture, algorithm, system, API, code |
| Literary | `#FBF9F1` | `#6B4E3D` | story, narrative, writing, poetry, character |
| Scientific | `#F4F8F6` | `#2D6A4F` | experiment, data, research, paper, discovery |
| Business | `#F4F3F0` | `#2D6A4F` | market, strategy, growth, finance, investment |
| Creative | `#F6F3F2` | `#B8432F` | design, art, aesthetics, inspiration, creation |
| Default | `#FAFAF8` | `#4A4A4A` | When no clear match — prefer default over wrong match |

When a style template is explicitly chosen (from the architecture or infocard style families in [design-system.md](design-system.md)), its colors take precedence over tone sensing.

## Visual grammar

Freeze five decisions before producing assets:

- **Palette** — 3 to 5 colors with explicit hex values and clear roles.
- **Type** — system font stack; one large display scale, one section scale, one body scale.
- **Shape** — one radius family, one stroke weight, one spacing unit.
- **Motif** — one small recurring project-specific cue.
- **Density** — one deliberate rhythm: sparse editorial, compact technical, or expressive gallery.

The motif is the strongest anti-template device. Repeat it lightly in the hero, section transitions, and showcase, but never as wallpaper everywhere.

## Color semantics for layered diagrams

When creating architecture or system diagrams (whether hand-authored SVG or using the `architecture` diagram engine), use consistent semantic color coding for layers. The exact palette varies by chosen style, but the semantic mapping stays stable:

| Layer | Meaning | Typical treatment |
| --- | --- | --- |
| User | user-facing interfaces and clients | lightest tier |
| Application | business logic and API services | mid tier |
| AI / Logic | intelligence, rules, processing engines | accent tier |
| Data | databases, caches, storage | deeper tier |
| Infrastructure | containers, networking, DevOps | darkest tier |
| External | third-party APIs, cloud services | dashed border |

Read [design-system.md](design-system.md) for the full style catalog and layout patterns.

## Composition patterns

- **Artifact wall** — several screenshots or outputs, slightly rotated around a shared axis. Best when visual proof is the product.
- **Before / after** — show the transformation when the mechanism matters.
- **System map** — show one source feeding several components or outputs.
- **Annotated specimen** — enlarge one real artifact and label the decisions that matter.
- **Sequence strip** — show three to six dependent stages.
- **Split panel** — title on one side, project structure or artifact on the other.
- **Integrated** — let diagrams, paths, code, or specimens share the same grid as the title.

Prefer one strong composition over several small decorative graphics.

## Restraint rules

- Use shadow only to separate overlapping artifacts; keep it soft and low-opacity.
- Do not add top borders to every screenshot or card.
- Keep decorative dots, grids, and lines subordinate to content.
- If several modules compete for attention, remove one before reducing everything.
- A README should feel designed at GitHub's content width, not like a full-screen website squeezed into Markdown.
- At least one module should feel visually heavier than the others. Avoid making every panel use the exact same treatment. Differentiate through scale, background tone, typographic weight, or accent rules.
