# Notes left by the second recorded proposer

These are the words of the language model that made the run in `results/model_run_2.json`, copied from its
closing report without change. It had no memory of the first run. It was given the output of
`tools/propose.py` and the first proposer's notes in `results/model_lessons.md`. No third run has been made.
Nothing here is checked: it is what one proposer inferred from 5 decisions and the earlier notes.

This run was made against the corrected model of v0.3.1. The notes of the runs made against v0.3.0 are in
`results/v0.3.0/`.

## Earlier notes: what I relied on and how it held up

- **Three margin formulas.** I planned every move from them by hand. Every margin landed within 1 ppm of my forecast, once I used Q of about 211.122 at wall 100.
- **Objective follows only floor and shed.** Held. Shed to zero gave exactly 8 ppm. Capture, wall and store changed in four moves, and the objective matched a floor-only forecast to the ppm each time.
- **Least load 391.7 kW, final margin 999215.** Held exactly.
- **Lower the load floor and outage margins together, drop the floor last.** Right, and it was the core of my plan.
- **Slightly off:** the written Q (206.17 + 0.0495·U) gives 940337 for the starting load_floor, against 940348 shown. That is 11 ppm, not the claimed 2.
- **Slightly misleading:** "about 25.5 ppm per kW" is not constant. The rate rises as the floor falls.
- **Not tested:** that refused proposals still print margins and objective, and that raising shed is refused as worse. I had no refusals.

## Notes for a third proposer

- The earlier notes are reliable. Five moves reach 919529; my table above is a working recipe.
- Use Q of about 212.7066 at wall 100... correction: 212.7066 at wall 132 and 211.122 at wall 100. With those, forecasts were good to 1 ppm.
- One over the objective is a straight line in the floor, about 3.0374e-5 per kW (fitted from the earlier notes' totals). It forecast 914955, 915922, 918554 and 919529 exactly, with 8 ppm added for shed 0.
- Raise capture and lower the floor in the same move. Capture alone drops load_floor much further than needed and wastes distance.
- Each move, bring load_floor and outage down by similar amounts. The radius is set by the worse of the two.
- When load_floor is the worst margin and only the floor changes, the drop to 392 always fits. The spare room equals the final headroom, 785.
- Keep outage below load_floor before that last move.
- By my hand calculation, not a test, four moves cannot work: sorption must fall about 204000, and four moves allow about 187000.
- Floor 392 is the lowest possible. Nothing I saw offers more objective.

The table the first note refers to:

| # | Proposal | Moved / radius | Objective |
|---|---|---|---|
| 0 | capture 851000, wall 100, pcm 3660, shed 0 | 33671 / 38305 | 914210 -> 914218 |
| 1 | capture 870000, floor 571, pcm 3772 | 56889 / 70025 | 914218 -> 914955 |
| 2 | capture 900000, floor 533, pcm 3935 | 82730 / 96871 | 914955 -> 915922 |
| 3 | capture 950000, floor 430 | 106760 / 135017 | 915922 -> 918554 |
| 4 | floor 392 | 88303 / 89088 | 918554 -> 919529 |
