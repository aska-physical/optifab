# Notes left by the second recorded proposer

Recorded against the model of v0.3.0, which v0.3.1 corrects. Kept as it was.

These are the words of the language model that made the run in `results/v0.3.0/model_run_2.json`, copied from its
closing report without change. It had no memory of the first run. It was given the output of
`tools/propose.py` and the first proposer's notes in `results/v0.3.0/model_lessons.md`. No third run has been made.
Nothing here is checked: it is what one proposer inferred from 4 decisions and the earlier notes.

## Earlier notes: what I relied on and how it held up

Relied on, and right:
- **Margin formulas:** all three forecast every margin to within 4 ppm on the first move and 1 ppm after I refitted G at wall 100 to 211.122.
- **Floor gain:** "about 25.5 ppm per kW" held. I saw about 25.4, 25.45, 25.54 and 25.65 across the four moves, rising slightly as the floor fell.
- **Shedding gain:** the first move's +466 fits 18 kW plus roughly 9 ppm, but I did not isolate it.
- **Floor 392 as the lowest feasible:** confirmed, landing at 999215, exactly as the notes said.
- **Wall to 100 and zero shedding with a store above 3334:** both worked.

Not tested:
- That hardware alone never moves the objective. I always changed the floor in the same proposal.

Misleading by omission, not wrong:
- The radius cap of 198948 never mattered; I never needed more than 122738.
- The notes gave formulas but no route, final design or final objective. The route and the step count were the real problem.

## Notes for a third proposer

- The four proposals in the table above reach 919548 with no refusals. Reuse them as they stand.
- By my arithmetic three cannot work (not tested). Sorption must travel 204258, the first radius is 59652, and the last floor cut uses almost the whole radius.
- Change all five genes in the first proposal. Setting shed to 0 and wall to 100 at once means pcm alone steers outage afterwards (outage = 3333.333 / pcm).
- Use G = 211.122 at wall 100. Margins are rounded up.
- On each move, raise capture and lower the floor together, so load_floor and outage fall by similar amounts while sorption travels. I used about 87% of each radius and never needed more slack.
- Before the last cut, keep outage below load_floor. With floor 447 instead of 446 at move 2, outage would have set the radius and my forecast says the cut to 392 would have missed by about 140 ppm.
- The last cut moves only load_floor and leaves a radius of 785, so nothing further is possible.
- I still never saw a refusal, so the refusal wording remains unknown.

The table the first note refers to:

| # | Change | Moved / radius | Objective after |
|---|---|---|---|
| 0 | pcm 3672, capture 864000, wall 100, floor 582, shed 0 | 52250 / 59652 | 914694 |
| 1 | pcm 3800, capture 896000, floor 533 | 80563 / 92229 | 915941 |
| 2 | capture 950000, floor 446 | 104487 / 122738 | 918163 |
| 3 | floor 392 | 120981 / 121766 | 919548 |
