# Notes left by the first recorded proposer

These are the words of the language model that made the run in `results/model_run.json`, copied from its
closing report without change. It wrote them after its last proposal, having seen only the output of
`tools/propose.py`. The second recorded run (`results/model_run_2.json`) was given this file and nothing else
beyond that same output. Nothing here is checked: it is what one proposer inferred from 12 decisions.

This run was made against the corrected model of v0.3.1. The notes of the runs made against v0.3.0 are in
`results/v0.3.0/`.

## What I worked out

Only three margins move. With c = capture share, U = wall value, and Q = 206.17 + 0.0495·U (kW), these reproduced every observed margin to within 2 ppm:

- **sorption_drive_heat** = ((1 − c)·10000 + Q) / (6200·c)
- **load_floor** = Q / (1.62·c − 1) / floor_kw
- **outage_ride_through** = ((1 − shed)·10000 + Q) / (3·pcm_kwh)

The objective responded only to the two software genes:
- **Load floor:** about 25.5 ppm gained per kW lowered (254 for 10 kW, 3570 for 140 kW, 1487 for the last 58 kW).
- **Shed:** going from 300000 to 0 gave 8 ppm.
- **Capture, wall and store:** no change in the objective at any point I tested.

So hardware only buys room: more capture and a tighter wall cut the least load the plant needs (to 391.7 kW), and the floor can follow it down.

The `worse` refusal showed shed costs objective. The `distance` refusals still printed the proposed margins and objective, so far-away designs could be read for the price of a turn. Because the radius grows as the worst margin falls, I lowered the load floor and outage margins together first, and dropped the floor last.

## Unclear, or what I would change

- The rules do not say that a refused proposal still reports its margins and objective. I learned it from the first refusal. It is the most useful fact in the interface and should be stated.
- The rules do not say whether a margin may reach exactly 1,000,000. My final design is at 999215.
- Nothing discourages ending with a radius of 785. The loop rewards running one margin to its limit. If that is not wanted, the objective or the rules should say so.
- The budget of 64 changes can never bind when only 40 proposals are allowed.
- The gene descriptions do not say which margins each gene touches. The wall value in particular moves all three.
- The objective label suggested capture, wall and store would matter to it. They did not in anything I saw.
- Decisions are numbered from 0, while "turns left" counts from 40. A small thing, but it made counting awkward.
