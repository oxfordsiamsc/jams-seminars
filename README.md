# JAMS seminars feed

Data for the Seminars page of the [Oxford SIAM Student Chapter website](https://people.maths.ox.ac.uk/siamsc/seminars.html).

Twice a day a GitHub Action reads the Junior Applied Mathematics Seminar listings on
<https://www.maths.ox.ac.uk/events/list/650> (and all pages of past events) and writes,
served by GitHub Pages at <https://oxfordsiamsc.github.io/jams-seminars/>:

- `seminars.json`: upcoming talks, the 12 most recent ones and talks with slides; the
  Seminars page uses it for the highlights and the upcoming list.
- `archive.json`: every talk since 2008, for the archive page. Talks are never removed
  from it, even if the department site drops them.
- `jams.ics`: the calendar people can subscribe to.

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

## Correcting a talk

If something is wrong or out of date on the department site (room, time, title...),
add an entry to `overrides.json` with the event id and the fields to replace:

```json
{ "id": "83068", "room": "L5", "note": "why, for the record" }
```

Overrides always win over the department data. Remove the entry once the department
page is fixed. Times (`start`, `end`) are ISO in UTC, e.g. `2026-11-03T12:30:00Z`.

