# JAMS seminars feed

Data for the Seminars page of the [Oxford SIAM Student Chapter website](https://people.maths.ox.ac.uk/siamsc/seminars.html).

Twice a day a GitHub Action reads the Junior Applied Mathematics Seminar listings on
<https://www.maths.ox.ac.uk/events/list/650> and writes `seminars.json`, which GitHub Pages
serves at <https://fhrobat.github.io/jams-seminars/seminars.json>. The website reads that
file in the browser to build the highlights and the list of upcoming talks.

## Adding slides

Add an entry to `slides.json` with the event id (the number in the event's
`maths.ox.ac.uk/node/<id>` link) and the slides URL:

```json
{ "id": "83067", "slides": "https://fhrobat.github.io/jams_talk" }
```

For a talk that is not on the department site you can also give `title`, `speaker`,
`affiliation`, `room`, `start` (ISO, UTC) and `url` directly.

Pushing a change to `slides.json` triggers a rebuild. You can also run the
**Update seminars** workflow by hand from the Actions tab.
