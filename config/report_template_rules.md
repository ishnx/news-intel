# Report Template Rules
## Design Principles for HTML Intelligence Reports

---

## Visual Design Philosophy
Reports should feel like premium intelligence products, not news articles.
Think: The Economist meets McKinsey — dense with meaning, beautiful in presentation.

### Color Palette
- Background: Deep dark (#08090e) — reduces eye strain for long reading
- Card surfaces: Slightly lighter (#0f1117)
- Borders: Subtle (#1e2036)
- Primary text: Soft white (#e4e6f0)
- Secondary text: Gray-blue (#8892b0)
- Accent/headings: Indigo (#6366f1)
- Bull/positive: Green (#4ade80)
- Bear/negative: Red (#f87171)
- Neutral/base: Amber (#fbbf24)
- Tags/chips: Dark with border

### Typography
- Body: System fonts (-apple-system, Segoe UI, Roboto)
- Scale: 16px base, generous line-height (1.7)
- Headings: Slightly lighter weight than bold (600)
- Maximum line width: 72 characters for readability

### Layout
- Two-column: Sticky TOC sidebar (left) + main content (right)
- TOC collapses on mobile to top navigation
- Reading progress bar at top
- Back-to-top button after scrolling

---

## Section Order
Every report follows this exact section order:

1. Header (title, metadata, tags)
2. Executive Summary (always visible, never collapsed)
3. Why This Matters
4. Strategic Incentives
5. Key Players
6. Financial Implications
7. Geopolitical Implications
8. Historical Analogies
9. Industry Impact
10. India Implications
11. Second-order Effects
12. Contrarian Perspectives
13. Future Scenarios (Bull/Base/Bear cards)
14. Important Unknowns
15. Connection to World Model
16. Related Reports
17. Follow-up Questions
18. Key Entities
19. Long-term Implications
20. Meta-patterns
21. Chatbot (floating, always accessible)

---

## Collapsible Sections
ALL sections except Executive Summary are collapsible.
Default state: EXPANDED
Rationale: Show full depth by default, allow collapse for scanning

---

## Interactive Elements

### Entity Tags
Key entities appear as clickable tags that show a tooltip with:
- Entity type (person/company/country/technology)
- Brief description
- Link to entity's world_model file (if exists)

### Scenario Cards
Bull/Base/Bear scenarios appear as side-by-side cards with:
- Color coding (green/amber/red)
- Probability indicator
- Expandable "what to watch for" signals

### Question Cards
Follow-up questions appear as cards that the user can:
- Click to ask the embedded chatbot
- Mark as "watching" (stored in localStorage)

### Citation Hover
Source URLs appear as superscript numbers.
Hovering shows a preview of the source.

---

## Chatbot Design
The embedded chatbot should:
- Float in the bottom-right corner when collapsed
- Open as a side panel (not a popup that blocks content)
- Remember conversation within the session (localStorage)
- Accept the report's full data as context
- Include suggested questions below the input
- Show a subtle pulsing indicator when thinking

The chatbot panel header should show:
- "Ask About This Report"
- Current API key status (key saved ✓ or Enter API key)

---

## Performance Requirements
- No external JavaScript dependencies
- No external CSS dependencies  
- Single HTML file, fully self-contained
- Load time < 1 second (even on slow connections)
- All content visible without JS (JS only enhances)
- Printable (CSS print media query)

---

## Accessibility
- All interactive elements keyboard-navigable
- Sufficient color contrast ratios
- ARIA labels on interactive elements
- Semantic HTML (article, section, nav, aside)
