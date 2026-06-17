# GL-260 Equilibrium Walkthrough Presentation Aid

## Presentation Goal

Give the audience enough process context to understand why the GL-260 equilibrium walkthrough matters before opening `docs/equilibrium-walkthrough.html`.

Core message:

The bicarbonate process is not hard because the overall chemistry is unknown. It is hard because real batches are multiphase, CO2 transfer is uneven, pH is path-dependent, and carbonate/bicarbonate speciation can shift after the operator thinks the batch is finished. GL-260 turns those moving pieces into a repeatable calculation chain.

Suggested total time: 45 to 70 minutes.

## 1) Opening Context Before Showing the HTML

Estimated time: 8 to 12 minutes.

### 1.1 Start With the Traditional Sodium Bicarbonate Story

Speaker goal:

Explain that sodium bicarbonate has historically been made by bringing sodium, carbonate chemistry, water, and CO2 together, then managing crystallization or slurry formation. The chemistry is familiar, but the operating endpoint is often harder to control than the balanced reaction suggests.

Talk track:

Sodium bicarbonate has traditionally been produced through carbonate chemistry routes such as the Solvay process, natural sodium carbonate sources, or direct carbonation of alkaline sodium solutions. In the cleanest textbook version, CO2 reacts with an alkaline sodium system and the chemistry moves toward sodium bicarbonate:

```text
NaOH + CO2 -> NaHCO3
```

or, from sodium carbonate:

```text
Na2CO3 + CO2 + H2O -> 2 NaHCO3
```

Those equations are useful, but they hide the real production problem. The process does not happen in a perfectly mixed beaker at one pH, one temperature, and one CO2 concentration. It happens through gas-liquid transfer, hydration, acid-base equilibrium, ion activity effects, slurry formation, heat release, and changing solids behavior.

Audience takeaway:

The reaction is simple on paper. The process is not simple in the vessel.

### 1.2 Explain Common Traditional Inconsistencies

Estimated time: 4 to 6 minutes.

Use this as a problem framing slide or whiteboard list.

Common issues:

- Inconsistent CO2 uptake: the same charge pressure does not always produce the same usable absorbed CO2.
- Variable endpoint pH: batches may reach similar uptake numbers but different measured pH values.
- Carbonate contamination: under-loaded or locally high-pH regions can leave too much carbonate.
- Over-carbonation or endpoint drift: continued CO2 contact can keep shifting pH and speciation after the apparent reaction event.
- Slurry handling differences: solids can hide active chemistry because only the liquid film is directly reacting.
- Mixing limitations: local pockets of high hydroxide, carbonate, or CO2-rich liquid can exist at the same time.
- Temperature effects: heat release and cooling change rates, solubility, and pressure interpretation.
- Sampling inconsistency: pH measurements depend on when and how the sample is mixed, settled, or diluted.

Bridge line:

This is why the walkthrough is built around balances, not only one reaction equation. We need to know how much sodium we started with, how much CO2 entered, how speciation responds, and whether the resulting pH is chemically consistent.

### 1.3 Set Up the GL-260 Thesis

Estimated time: 2 to 3 minutes.

Main thesis:

GL-260 treats each cycle as a measured carbon-loading event, then uses equilibrium chemistry, activity corrections, and measured-pH anchors to produce a defensible pH and speciation timeline.

What to say:

The goal is not to make a black-box pH predictor. The goal is to make every displayed pH value traceable back to stoichiometry, carbonate equilibrium, charge balance, CO2 uptake, and calibration evidence.

## 2) Walkthrough Opening: Purpose and Locked Assumptions

HTML sections:

- Purpose
- Locked Assumptions for This Walkthrough

Estimated time: 3 to 5 minutes.

What to emphasize:

- The walkthrough is intentionally locked to one deterministic scenario.
- The example starts with `700 g` NaOH and `2.2 kg` water.
- The synthetic cycle sequence is not trying to be every possible batch. It is a controlled teaching case.
- The real-world PR-24304 section later shows how the same logic maps to actual data.

Presenter cues:

- Point out that locked assumptions make every intermediate number reproducible.
- Tell the audience that reproducibility is more important than perfect realism in the first pass.
- Explain that the real-data section comes later after the math is established.

Transition:

Before we discuss pH, we need to know the sodium inventory and the CO2 target range.

## 3) Section 1: Basis Setup

Estimated time: 5 to 7 minutes.

Primary message:

The sodium inventory controls the maximum amount of bicarbonate that can be formed and sets the charge-balance burden for the pH solver.

Talk track:

The first calculation converts `700 g` NaOH into moles, molarity, and molality. This is not just bookkeeping. Sodium is the positive charge pool. Every later carbonate, bicarbonate, hydroxide, and hydrogen concentration has to be consistent with this sodium basis.

Key points:

- `n_NaOH` fixes the sodium inventory.
- `m_NaT` is the molality basis used by later equilibrium calculations.
- The two CO2 endpoints show the difference between carbonate and bicarbonate stoichiometry.
- The bicarbonate endpoint requires enough CO2 to move the system away from carbonate dominance.

Useful audience question:

If the sodium basis is wrong, what later values become unreliable?

Expected answer:

Everything downstream: CO2 target, pH, bicarbonate fraction, carbonate fraction, and completion.

Transition:

Once the material basis is fixed, the next question is how carbon distributes among carbonate species.

## 4) Section 2: Equilibrium Half-Reactions, Constants, and Activities

Estimated time: 6 to 8 minutes.

Primary message:

The pH and species distribution come from coupled equilibrium constraints, not independent knobs.

Talk track:

Carbon dioxide does not simply become bicarbonate and stay there. It sits in an equilibrium network: dissolved CO2 and carbonic acid, bicarbonate, carbonate, hydrogen, hydroxide, and water. The position of that network changes with pH, CO2 pressure, ionic strength, and activity coefficients.

Key points:

- Henry's law connects headspace CO2 to dissolved CO2.
- `Ka1`, `Ka2`, and `Kw` define the carbonate-water equilibrium network.
- Activity corrections matter because concentrated sodium systems are not ideal dilute solutions.
- Activity is the effective chemical availability, not just raw concentration.

Presenter cue:

Use the activity equation as the first bridge from textbook chemistry into why this app needs a Pitzer path.

Transition:

Now that we have the half-reactions, we can combine them into the overall bicarbonate/carbonate control expression.

## 5) Section 3: Complete Keq Expression

Estimated time: 5 to 7 minutes.

Primary message:

The overall expression shows why hydroxide and CO2 pressure control whether the batch favors bicarbonate or carbonate.

Talk track:

The combined equation explains the operating problem. Bicarbonate is an intermediate path between dissolved CO2 and carbonate. If hydroxide remains high, the system can keep pushing bicarbonate toward carbonate. If CO2 pressure and contact are strong enough, the chemistry can move back toward bicarbonate.

Key points:

- `HCO3-` cancels as an intermediate in the algebra.
- Residual hydroxide drives over-conversion toward carbonate.
- Increasing dissolved CO2 helps suppress carbonate dominance.
- This is the mathematical reason pCO2 is a purity lever.

Transition:

The next section turns those equilibrium relationships into the actual pH solve.

## 6) Section 4: Speciation and pH Derivation Used in GL-260

Estimated time: 7 to 10 minutes.

Primary message:

GL-260 accepts a pH only when the carbonate distribution and charge balance agree.

Talk track:

The solver tries a hydrogen concentration, computes hydroxide, distributes total carbon into CO2, bicarbonate, and carbonate fractions, then checks charge balance. A pH is only meaningful if the corresponding species distribution conserves charge.

Key points:

- Alpha fractions distribute total inorganic carbon.
- `R_q` is the charge-balance residual.
- The accepted pH is the point where residual charge is close enough to zero.
- pH without charge consistency is not a reliable process value.

Presenter cue:

This is a good place to use the live derivation slider. Emphasize that each slider step removes one degree of freedom until pH, hydroxide, and speciation become one coupled state.

Transition:

Now we can explain why bicarbonate purity is hard even when the pH looks close.

## 7) Section 5: Why Bicarbonate Purity Is Hard and Why pCO2 Is the Control Lever

Estimated time: 4 to 6 minutes.

Primary message:

pCO2 is both an equilibrium lever and an operational lever.

Talk track:

At high pH, carbonate is favored. To favor bicarbonate, the process has to reduce effective hydroxide and maintain enough dissolved CO2. Higher headspace CO2 raises the dissolved CO2 boundary condition and changes the bicarbonate-to-carbonate ratio.

Key points:

- High alkalinity favors carbonate.
- Dissolved CO2 helps pull carbonate back toward bicarbonate.
- pCO2 affects both endpoint chemistry and absorption rate.
- A low pCO2 or poorly mixed batch can appear finished while still being carbonate-heavy.

Transition:

The ideal equations are still incomplete because this is a concentrated sodium system.

## 8) Section 6: NaOH-CO2 Pitzer Calculation Path

Estimated time: 6 to 8 minutes.

Primary message:

The Pitzer path improves the model by correcting activities in a concentrated electrolyte slurry.

Talk track:

In dilute chemistry, concentration is often close enough. In a concentrated sodium carbonate/bicarbonate system, ions interact strongly. Sodium, hydroxide, bicarbonate, and carbonate are not passive spectators. Their interactions change effective activities and shift the pH/speciation result.

Key points:

- Pitzer corrections turn raw molality into activity.
- Sodium-carbonate interactions affect the apparent equilibrium position.
- HMW/PHREEQC terms provide a focused parameter basis.
- The model still preserves the Python fallback path and Rust acceleration path conceptually, but the important presentation point is activity-corrected chemistry.

Presenter cue:

Do not over-explain every Pitzer term unless the audience is technical. The practical takeaway is: concentrated electrolyte behavior changes the effective chemistry.

Transition:

Equilibrium tells us where the batch can settle. Kinetics explains whether it gets there during the actual cycle.

## 9) Section 7: Reaction Kinetics and Uptake-Rate Interpretation

Estimated time: 7 to 10 minutes.

Primary message:

The batch endpoint depends on transfer, reaction, mixing, and time, not only equilibrium math.

Talk track:

CO2 has to move from gas to liquid, hydrate, react, distribute through the batch, and continue exchanging with solids in the slurry. If any step is slow, the pressure curve and final pH can look different even with the same nominal charge.

Key points:

- `kLa` controls how quickly CO2 crosses into the liquid.
- High hydroxide creates fast early CO2 consumption.
- As hydroxide falls, pressure decay slows and bicarbonate becomes more stable.
- Mixing prevents local high-pH regions from overproducing carbonate.
- Slurry re-equilibration means the batch can keep changing after it looks visually thick.

Operational note to include verbally:

When the reaction is removed from the shaker and physically blended until a smooth homogeneous slurry is observed, that is not just cosmetic. It refreshes surface area, breaks up concentration pockets, redistributes heat, and improves usable CO2 uptake.

Transition:

The next step is how GL-260 converts each pressure event into a carbon-loading increment.

## 10) Section 8: Cycle Uptake Math

Estimated time: 4 to 6 minutes.

Primary message:

Each cycle becomes a quantified CO2 increment, and cumulative CO2 loading drives the predicted pH/speciation path.

Talk track:

The model does not only ask whether CO2 was added. It asks how much CO2 was absorbed per cycle, then accumulates that into total carbon loading. That accumulated loading is what the equilibrium solver consumes.

Key points:

- Synthetic cycles provide a clean teaching sequence.
- Pressure-derived uptake is the operational path.
- Temperature, headspace volume, and pressure change affect calculated moles.
- Cumulative loading is the bridge between the cycle detector and chemistry model.

Transition:

Now we can look at the synthetic simulation table and see the chemistry move cycle by cycle.

## 11) Section 9: Worked NaOH-Pitzer Simulation Table

Estimated time: 5 to 8 minutes.

Primary message:

The synthetic table shows the expected pH/speciation trajectory as CO2 loading increases.

Talk track:

Early cycles are high pH and high hydroxide. As CO2 accumulates, hydroxide falls, carbonate and bicarbonate shift, and the pH approaches the bicarbonate-rich region. The trend matters more than any single row.

Key points:

- Watch cumulative CO2, pH, bicarbonate fraction, and carbonate fraction together.
- The pH trajectory is a consequence of charge-balanced speciation.
- The charts are there to make the transition visible.
- This section is the bridge from equations to operator-facing interpretation.

Transition:

The synthetic case teaches the mechanism. The real PR-24304 example shows how the same logic reads actual process data.

## 12) Section 10: Worked Real-World Example

Estimated time: 6 to 10 minutes.

Primary message:

The same chain applies to real batch data: profile basis, pressure/temperature events, uptake, pH, and speciation.

Talk track:

The real-world example is where the model becomes operational. We are no longer only proving the equations. We are using the measured process profile to interpret what happened in the batch.

Key points:

- Start with the profile basis and stoichiometric translation.
- Use the combined triple-axis plot to connect pressure, temperature, and pH.
- Use the speciation timeline to explain what the chemistry is doing.
- Emphasize that the model is a structured interpretation of process evidence.

Transition:

Real process data will never perfectly match the baseline model. That is why measured pH calibration exists.

## 13) Section 11: Measured-pH Calibration and Hybrid ML Correction

Estimated time: 6 to 9 minutes.

Primary message:

Measured pH anchors correct the modeled trajectory without throwing away the chemistry.

Talk track:

Calibration is not a replacement for equilibrium chemistry. It is a correction layer that uses measured anchors to align the modeled trajectory with the actual batch. The model still needs the stoichiometry and charge balance underneath.

Key points:

- Anchors correct cycle-level pH drift.
- The baseline piecewise correction handles known measured points.
- Historical anchors improve future predictions.
- ML residual correction is a secondary correction, not the primary chemistry.
- Fail-closed logic prevents bad anchors from corrupting the result.

Transition:

After chemistry and calibration, the dashboard values are just deterministic summaries of the same chain.

## 14) Section 12: Dashboard Values

Estimated time: 3 to 5 minutes.

Primary message:

Dashboard numbers should be traceable, not decorative.

Talk track:

The dashboard is useful only if every value has a clear source and precedence. Required CO2, target gap, completion, corrected pH, and baseline pH all come from defined inputs and fallback rules.

Key points:

- Required CO2 source precedence prevents ambiguous targets.
- Target gap is clamped so the dashboard does not show nonsensical negative demand.
- Corrected pH and baseline pH are separate channels.
- The dashboard should help the operator decide what to do next.

Transition:

Close by restating the complete chain.

## 15) Closing Summary

Estimated time: 3 to 5 minutes.

Final narrative:

Traditional sodium bicarbonate production is inconsistent because the process is controlled by more than the balanced reaction. CO2 transfer, slurry behavior, mixing, temperature, pH sampling, electrolyte activity, and endpoint timing all affect what the batch actually becomes.

GL-260 makes the process auditable by chaining together:

- sodium basis,
- CO2 uptake,
- carbonate equilibrium,
- activity correction,
- charge balance,
- kinetic interpretation,
- measured-pH calibration,
- and dashboard completion logic.

Closing line:

The value of the walkthrough is that every displayed pH and speciation value can be explained from the process evidence instead of treated as a black-box output.

## Backup Discussion Prompts

Use these if the audience asks questions or if you need to slow down.

- Why can two batches with similar CO2 uptake have different pH?
- What does pH miss if speciation is not shown?
- Why does carbonate persist even when bicarbonate is the desired product?
- Why does mixing change the apparent reaction rate?
- What happens if the pressure event ends before the slurry has re-equilibrated?
- Why are measured pH anchors helpful but not sufficient by themselves?
- What values should an operator trust first when dashboard values disagree?

## Short Version for a 20-Minute Presentation

1. Traditional process and inconsistency problem: 4 minutes.
2. Basis setup and CO2 target: 3 minutes.
3. Equilibrium, pH, and charge balance: 5 minutes.
4. pCO2, Pitzer activity, and slurry kinetics: 4 minutes.
5. Real-data example and calibration: 3 minutes.
6. Closing chain and dashboard meaning: 1 minute.

## One-Slide Takeaway

Sodium bicarbonate production is traditionally described by simple reactions, but real batches are governed by CO2 transfer, slurry mixing, electrolyte activity, charge balance, and measured endpoint behavior. GL-260 connects those pieces into one reproducible pH and speciation workflow.
