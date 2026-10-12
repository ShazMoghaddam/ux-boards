# Spec reference

One YAML file describes the whole set of boards. Only `project.name` and `ia.sections` are required; leave out `breakpoints`, `screens` or `visual` and those boards are skipped.

Any string containing the word `TODO` is treated as an unfilled placeholder.

## Top level

| Key | Purpose |
| --- | --- |
| `project` | `name` (required), `short` (two letters for the tablet rail), `tagline` |
| `release_labels` | Map of release number to label, shown in the IA legend |
| `ia` | Information architecture board |
| `breakpoints` | Navigation by screen size board |
| `shell` | `nav_foot`: lines shown at the foot of the desktop sidebar |
| `screens` | One board per entry, wireframe or styled |
| `visual` | Visual system board, and the colours used by styled screens |

## `ia`

```yaml
ia:
  eyebrow: optional, defaults to "<name> · Step 1 of 3 · Structure"
  intro: one or two sentences
  sections:
    - route: /orders
      name: Orders              # also used as the navigation label
      question: what this section answers
      pages:
        - name: Order
          route: /orders/:id    # optional
          note: optional
          release: 2            # optional, default 1; 2+ is drawn dashed
  journeys:
    - name: Fill an order
      paths:                    # several paths are joined with "or"
        - [Step, Step, Outcome] # the last step is drawn filled
        - [{label: Upload, release: 2}, {label: Confirm, release: 2, end: false}]
  notes:
    - {title: Cross-links, body: ...}
```

## `breakpoints`

```yaml
breakpoints:
  intro: ...
  devices:
    - {kind: phone | tablet | desktop, name: Phone, range: under 768, description: ...}
  columns: [Phone, Tablet, Laptop and desktop]
  patterns:
    - pattern: Filters
      cells:
        - phone answer
        - tablet answer
        - {text: shared answer, span: 2}   # spans columns
```

Tip: YAML splits unquoted flow lists on commas. If a cell contains a comma, write the cells as a block list (one `-` per line) or quote them.

## `screens`

```yaml
screens:
  - title: Today, phone and tablet
    route: /
    purpose: one sentence
    style: wire            # or styled, which uses the visual system
    eyebrow: optional
    frames:
      - device: phone      # phone 390x844, tablet 820x1180, desktop 1440x900
        width: 390         # optional overrides
        height: 844
        nav: Today         # section to highlight; omit for full-screen tasks
        appbar: {left: ‹ Back, title: Step name, right: Exit}
        blocks: [...]      # main content
        footer: [...]      # fixed action bar at the bottom
        panel: [...]       # right panel, desktop only
        caption: optional text under the frame
```

All frames on one board are scaled by the same factor so they fit side by side. Put a desktop frame on its own board if you want it large.

## Blocks

A block is a one-key mapping, with options as extra keys:

```yaml
- button: Review and submit
  kind: primary
  full: true
```

| Block | Value | Options |
| --- | --- | --- |
| `eyebrow` | text | |
| `title` | text | `small` |
| `heading` | text | `aside`, `link` |
| `text` | text | `muted`, `small`, `link` |
| `header` | title text | `eyebrow`, `text`, `actions` (list of buttons), `small` |
| `button` | label | `kind`: primary, secondary, ghost, danger, disabled, focused; `full` |
| `buttons` | list of labels or `{value, kind}` | |
| `segments` | list of `{label, range, sub, state}`; state is done, current, progress or todo | `ticks`, `marker: {at: percent, label}` |
| `rows` | list of `[label, value]` or `{label, value, cols, strong, muted, indent}` | |
| `list` | list of `{title, meta, value, warn}` or `{group: heading}` | |
| `table` | `{columns, rows, foot}`; a row can be `{group: heading}` | `align` (string like `llrr`), `highlight` (row index) |
| `filters` | list of `{label, value, select}` | |
| `search` | placeholder | `filters` (button label) |
| `chips` | list of labels or `{label, removable}` | |
| `stepper` | `{step, total, labels}` | |
| `choices` | list of `{label, desc, note, selected}` | |
| `checkbox` | label | `boxed` |
| `callout` | text | `link` |
| `field` | `{label, hint, value, error}` | |
| `fields` | list of fields, side by side | |
| `status` | list of `{label, shape}`; shape is check, dot, half, dashed or warn | |
| `checklist` | list of text | |
| `success` | anything (draws a tick) | |
| `code` | monospace text, e.g. a reference | |
| `columns` | list of block lists | |
| `divider` | `true` | |
| `spacer` | height in px | |

An unknown block type renders as a red dashed box, so typos are easy to spot.

## `visual`

```yaml
visual:
  intro: ...
  accessibility_note: ...
  colours:
    - name: Indigo
      hex: "#2F3E8F"
      on: "#FBEFD9"        # optional background, for tags
      use: Primary actions
      role: text           # text (default, contrast checked), fill or line
      token: primary       # ink, muted, primary, tint, shelf, rule, danger, warning
  rules: [one-line colour rules]
  type:
    import_url: optional stylesheet URL
    serif: {family: "Literata, Georgia, serif"}
    sans: {family: "'Source Sans 3', Arial, sans-serif"}
    scale:
      - {role: Page title, font: serif, size: 32, line: 38, weight: 600, sample: ..., tabular: true, muted: true, label: optional}
  signature:
    name: The order trail
    description: ...
    segments: [...]        # same shape as the segments block
    ticks: optional
    marker: optional
  components: [blocks]     # rendered in the visual system
  tokens:
    - [Spacing, "4, 8, 12, 16 px"]
```

Colours with a `token` drive styled screens. Text on the primary colour is white when white passes 4.5:1, otherwise the ink colour.
