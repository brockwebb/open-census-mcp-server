# xdgov Federal Data Design Standards — Color Reference

Source: https://xdgov.github.io/data-design-standards/components/colors

These colors adhere to U.S. federal data visualization standards and are
Section 508 compliant. Any federal agency can customize from this palette.

---

## Featured Colors (Qualitative Primary)

| Name | Hex | RGB | SCSS Variable |
|------|-----|-----|---------------|
| Teal | #0095A8 | (0, 149, 168) | $census-color-teal |
| Navy | #112E51 | (17, 46, 81) | $census-color-navy |
| Orange | #FF7043 | (255, 112, 67) | $census-color-orange |
| Grey | #78909C | (120, 144, 156) | $census-color-grey |

---

## Sequential Palettes (7 steps each, light → dark)

### Teal Sequential

| Step | Name | Hex | Use |
|------|------|-----|-----|
| 1 | Lightest Teal | #D4F4F8 | Light backgrounds |
| 2 | Lighter Teal | #6BEFF9 | Light fills |
| 3 | Light Teal | #00BED6 | Mid fills |
| 4 | Teal | #0095A8 | Primary |
| 5 | Dark Teal | #006C7A | Emphasis |
| 6 | Darker Teal | #004851 | Strong emphasis |
| 7 | Darkest Teal | #00282E | Maximum contrast |

### Blue Sequential

| Step | Name | Hex | Use |
|------|------|-----|-----|
| 1 | Lightest Blue | #C1D7F2 | Light backgrounds, fills |
| 2 | Lighter Blue | #97BCE9 | Light fills |
| 3 | Light Blue | #6DA1E0 | Mid fills |
| 4 | Blue | #2E78D2 | Primary blue |
| 5 | Dark Blue | #205493 | Strong components |
| 6 | Navy | #112E51 | Authoritative, headers |
| 7 | Darkest Blue | #081627 | Maximum contrast |

### Orange Sequential

| Step | Name | Hex | Use |
|------|------|-----|-----|
| 1 | Lightest Orange | #FFE4DC | Light backgrounds |
| 2 | Lighter Orange | #FFBEA9 | Light fills |
| 3 | Light Orange | #FF9776 | Mid fills |
| 4 | Orange | #FF7043 | Primary, highlights |
| 5 | Dark Orange | #C25432 | Emphasis, borders |
| 6 | Darker Orange | #853A22 | Strong emphasis |
| 7 | Darkest Orange | #5D2818 | Maximum contrast |

### Grey Sequential

| Step | Name | Hex | Use |
|------|------|-----|-----|
| 1 | Lightest Grey | #E8EFF2 | Backgrounds |
| 2 | Lighter Grey | #C8D7DF | Light fills, borders |
| 3 | Light Grey | #A7C0CD | Mid fills, borders |
| 4 | Grey | #78909C | Neutral components |
| 5 | Dark Grey | #4B636E | Muted text, annotations |
| 6 | Darker Grey | #364850 | Strong muted |
| 7 | Darkest Grey | #222C31 | Near-black text |

---

## Qualitative Palette (for categorical data)

Use colors with enough variance in hue and brightness to differentiate categories.

| # | Name | Hex |
|---|------|-----|
| 1 | Teal | #0095A8 |
| 2 | Navy | #112E51 |
| 3 | Orange | #FF7043 |
| 4 | Grey | #78909C |
| 5 | Blue | #2E78D2 |
| 6 | Dark Teal | #006C7A |
| 7 | Lighter Orange | #FFBEA9 |

### Qualitative with Highlight

Use when one category needs emphasis. Other categories use lighter variants.

| # | Name | Hex | Role |
|---|------|-----|------|
| 1 | Lighter Orange | #FFBEA9 | Background |
| 2 | Lighter Blue | #97BCE9 | Background |
| 3 | **Orange** | **#FF7043** | **Highlight** |
| 4 | Lighter Grey | #C8D7DF | Background |
| 5 | Lightest Teal | #D4F4F8 | Background |

---

## Diverging Palette (for breakpoint data)

Neutral center, two color extremes. Lower values = blue, higher values = orange.

| Position | Name | Hex |
|----------|------|-----|
| Low extreme | Navy | #112E51 |
| Low mid | Lighter Blue | #97BCE9 |
| Neutral | Lightest Grey | #E8EFF2 |
| High mid | Lighter Orange | #FFBEA9 |
| High extreme | Darker Orange | #853A22 |

---

## Semantic Color Assignments (Project Convention)

These are the diagram-specific semantic meanings used in our method.txt specs:

| Semantic Role | Color | Hex | Example |
|---------------|-------|-----|---------|
| Novel / this paper's contribution | Orange | #FF7043 | Pragmatics components |
| Novel border | Dark Orange | #E64A19 | Pragmatics borders |
| Novel light fill | Lightest Orange | #FFE4DC | Pragmatics backgrounds |
| Authoritative / system | Navy | #112E51 | LLM, core infrastructure |
| Authoritative fill | Dark Blue | #205493 | LLM boxes |
| Source data / API | Lightest Blue | #C1D7F2 | Census API, source docs |
| Baseline / existing | Grey | #78909C | RAG components |
| Baseline border | Dark Grey | #4B636E | RAG borders |
| Baseline light fill | Lighter Grey | #C8D7DF | RAG backgrounds |
| Output / success | Light Green* | #C8E6C9 | Response boxes |
| Success border | Green* | #2E7D32 | Response borders |
| Warning / gap | Red* | #D32F2F | Error states |
| Muted text | Dark Grey | #4B636E | Annotations, arrow labels |
| Background | White | #FFFFFF | Canvas |

*Green and red are supplementary colors not in the core xdgov palette but
used sparingly for semantic state indication. Ensure adequate contrast.

---

## 508 Accessibility Rules

- Text on white: use Darkest, Darker, or Dark variants only
- White text on color: use Darkest, Darker, or Dark backgrounds only
- Avoid red/green combinations for colorblind users
- Use text labels in addition to color to encode meaning
- Minimum contrast ratio: 4.5:1 (WCAG AA)

Test combinations at: https://webaim.org/resources/contrastchecker/
