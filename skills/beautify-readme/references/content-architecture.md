# README content architecture

## The first-screen test

Without scrolling, a new visitor should understand:

1. What is this?
2. What can it do for me?
3. What should I look at next?

The hero should answer the first two. The next module should provide proof.

## Plain-language sequence

Use this sequence unless the repository has a stronger information need:

```text
Value → Proof → Mechanism → First use → Detail
```

Do not begin with architecture, contributor instructions, a command, or a long table of contents when the project is unfamiliar.

## Editing rules

- Replace internal jargon with a concrete outcome.
- Explain the mechanism once; remove repeated versions of the same promise.
- Put the shortest working install path before advanced configuration.
- Keep limitations visible when they affect user choice.
- Prefer one example that succeeds end-to-end over many disconnected snippets.
- Use "we" or direct language when it reduces distance, but do not fake community size.
- Cut any sentence that a reader could write without knowing the project. If it could appear in any README, it does not belong in this one.

## Visual-to-text division

Use visuals for hierarchy, identity, comparison, sequence, and proof. Use Markdown for explanation, commands, API details, links, compatibility, and contribution instructions.

If a sentence needs to be copied, searched, translated, or frequently updated, keep it out of SVG.

## Section-by-section guidance

### Hero

One image that carries the project name, a plain-language value, and real proof. Do not separate title and proof by habit — let proof legibility decide whether they share one board or sit as two adjacent modules.

### Proof wall

Screenshots, outputs, or live results arranged with controlled scale and overlap. If several artifacts compete, remove one before reducing everything. Real proof beats decorative mockups.

### What it is

One or two sentences. If the hero already communicates this, omit the section rather than restating it.

### Why it is different

Explain the mechanism — not adjectives. A diagram, a before/after, or a compact architecture view works better than a feature list.

### How to use

The shortest path from zero to a successful first run. Put the install command and the first action before configuration options, environment variables, or advanced flags.

### Limitations and context

Keep compatibility, known issues, and contribution details visible when they affect the user's decision to adopt. Move them below the fold, not into a hidden appendix, when they matter.

## When to use code-fence diagrams in the body

Code-fence diagrams (PlantUML, Vega, infographic, canvas, architecture, infocard) belong in the body, not the hero. Use them where a structured visual explains a mechanism, flow, or relationship more clearly than prose. They are editable in the Markdown source and re-render on every view in a Markdown Viewer.

Archify system maps also belong in the body (typically under "How it works" / mechanism), never as a replacement for the hero title system. For GitHub-native readers, embed the exported Share Card or static PNG/SVG; optionally link the interactive HTML companion. Keep the Archify JSON IR as source.

Do not replace a hero SVG with a code-fence diagram or an Archify HTML file — the hero must render on github.com, and code fences / interactive HTML only work outside GitHub's image embeds. If a body diagram must also work on GitHub, export it as a static SVG or PNG and embed the image file instead.
