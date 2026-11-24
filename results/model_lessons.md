# Notes left by the first recorded proposer

These are the words of the language model that made the run in `results/model_run.json`, copied from its
closing report without change. It wrote them after its last proposal, having seen only the output of
`tools/propose.py`. The second recorded run (`results/model_run_2.json`) was given this file and nothing else
beyond that same output. Nothing here is checked: it is what one proposer inferred from 11 decisions.

## What I worked out

- **Fixed margins:** eleven margins never moved. The largest, floor_punching_collar at 801052, caps the radius at 198948.
- **Objective:** only the two software genes moved it.
  - Each kW taken off the load floor gained about 25.5 ppm.
  - Removing all shedding gained 9 ppm.
  - Capture, wall and thermal store never changed it. They only free up margin that a lower floor then uses.
- **Margins:** these forms fitted every observation to within 2 ppm.
  - outage_ride_through = (1 − shed) × 3333.33 / pcm.
  - load_floor = G / ((1.62 × capture − 1) × floor), with G ≈ 206.17 + 0.0495 × wall_u.
  - sorption_drive_heat = (10000 × (1 − capture) + G) / (6200 × capture).
- **The one refusal:** more shedding eased the outage margin but cost 2 ppm. That pointed to zero shedding, which was only feasible when paired with a larger store.
- **Wrong turn:** my wall probe (132 to 150) tightened load_floor slightly for no gain, so I reversed it to 100.
- **Radius:** letting load_floor fall while raising capture grew the radius from about 60000 to 153000. That let the final floor cut go through in one step.

## Unclear, or what I would change

- **Design sits at the limit:** load_floor is 785 ppm from the limit, and this cannot be backed out because raising the floor lowers the objective. By my fitted trend, the last 3 kW (395 to 392) were worth only about 77 ppm.
- **Store size is arbitrary:** with no shedding, any store of 3334 kWh or more should give the same objective, since the store never moved it. I took it to 5000 as a test, and it stayed there.
- **Whole numbers only:** `show` does not say genes must be whole numbers; I learned it from an error.
- **Refusals and turns:** `show` says a refused proposal "costs nothing", but it does use a turn.
- **Budget never binds:** 64 changes against 40 turns means the budget cannot run out first.
- **Verdict words:** "ok" and "worse" are not explained, and I never saw what an over-radius refusal looks like.
- **Rounding:** the objective prints in whole ppm, so the shedding effect sits at the rounding limit. I could not tell whether rule 3 compares rounded or exact values. Margins appear to be rounded up.
- **Ties:** rule 3 accepts an equal objective, which is what made objective-neutral hardware moves possible. The rules could say so plainly.
