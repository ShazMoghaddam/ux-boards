# The method

These boards come in three steps, and the order matters. Structure first, because it is the cheapest thing to change and the most expensive to get wrong. Visual style second, once the structure has stopped moving. Screens last, as proof that the first two work together.

Each step below says what the board is for, how to fill it in, and the questions to ask before calling it done.

## Step 1: Structure

### Information architecture

**Order sections by how often people need them, not by how the database is shaped.** Write each section's purpose as the question a user would ask when they open it ("Where am I, and what do I do next?"). If two sections answer the same question, merge them. If one section answers two, split it.

**Give every page a route.** Routes force decisions: is the first-run checklist its own page, or the home page in a different state? (In the original, it was the same address with a checklist until the account was usable. That kept bookmarks and links stable.)

**Mark what ships when.** The solid ① and dashed ② markers keep scope honest. A next-release page still belongs on the board, because the structure has to leave room for it.

**Draw the two or three journeys that matter.** One for the job the product exists to do, one for getting data in, one for first run. The filled step at the end of each path is the moment the user gets what they came for. If you cannot name that moment, the journey is not finished.

**Write down what lives outside the sections.** Sign in, not found, returning from a third-party sign-in, error pages. These are the screens that get designed last and badly.

**List what the backend needs.** Designing the structure almost always reveals API gaps (a list endpoint that only works per parent, a sign-in flow that ends on a JSON page). Writing them on the board turns them into tickets.

Done when: every section answers one question, every page has a route and a release, and every journey ends in a named outcome.

### Navigation by screen size

**Choose breakpoints around real devices, not a framework's defaults.** Ask where your users actually are: at a desk, at a counter, on their feet.

**Give each size its own answer.** For each pattern (page actions, tables, filters, detail and edit, forms, multi-step tasks), decide what the phone, tablet and laptop do. The rule of thumb that held up well:

- Phone: one primary action in the header, the rest in a More menu. Lists instead of tables. Filters in a bottom sheet. Detail goes full screen.
- Tablet: a rail, not a sidebar, so content keeps the width. Detail in a side sheet over the list.
- Laptop and desktop: a labelled sidebar. Detail in a right panel beside the table, so the table keeps its scroll position.
- Multi-step tasks hide navigation on every size and offer an Exit, so the task has the whole screen.

Done when: nothing in the table says "same as desktop, smaller".

### Wireframes

Wireframe the screens that carry the main journeys, at the sizes people will use them. Keep them greyscale. If a wireframe needs colour to make sense, the hierarchy is not doing its job yet.

Three habits worth copying:

- **Lead with the next action.** The home screen opens with what to do next, why, and by when, then one button.
- **One decision per step.** Multi-step tasks ask one question per screen, and the last step restates exactly what will be sent before anything is sent.
- **Show the source of every number.** Totals link to the rows behind them. Detail panels say where a record came from.

## Step 2: Visual system

**Describe the feel in a few words, then name the decisions that create it.** "Calm, exact and quiet" means nothing on its own. "A white page, ruled lists instead of cards, one colour for actions" is something a developer can build.

**Fewer colours, each with one job.** Text, secondary text, one action colour, a tint for selection, a background for navigation, a rule colour, one warning, one error. The generator works out every contrast ratio against white and flags any text colour under 4.5:1.

**Never let colour carry meaning alone.** Status always has a word and a shape as well (a tick, a filled dot, a half-filled dot, a dashed ring). Money or stock going up and down is shown by columns or signs, not green and red.

**Pick one signature element.** One visual idea that makes the product recognisable and does real work. In the project these boards came from, it was a year drawn as a ruler; in the Bindery example it is the order trail. Use it in two or three places, not everywhere.

**Write the tokens down.** Spacing steps, corner radii, where shadows are allowed, minimum touch targets. These settle more arguments than any mockup.

Done when: every colour has a job and a ratio, the type scale has real sample text, and the signature element appears in at least one screen.

## Step 3: Screens

Re-render a few of the wireframes in the visual system (set `style: styled` on a screen). Pick the screens with the most going on: the home page on a laptop, a list on a phone, the confirmation step of the main task. If the styled version needs layout changes, go back and fix the wireframe so the two stay in step.

## Writing the copy

The boards are full of real sentences on purpose. Placeholder copy hides problems that real copy exposes. A few rules that kept the original readable:

- Use the user's words, not the system's ("Ready to send", not "Pending submission").
- Say what happens next and when ("Due 7 Nov, in 29 days", "Hold until 15 Oct").
- Error messages say what to do, with an example ("Enter 13 digits, like 978 0 00 000000 0").
- Confirmations restate the outcome, and receipts give a reference the user can copy.
