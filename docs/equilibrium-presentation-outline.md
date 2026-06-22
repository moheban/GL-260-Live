# GL-260 Equilibrium Walkthrough Presentation Outline

## Presentation Purpose

Explain how CIL produces sodium bicarbonate, why carbonate contamination is difficult to avoid, and how GL-260 connects measured \(CO_2\) uptake to equilibrium pH, activity-corrected speciation, and an operating endpoint.

Core message:

The balanced reaction is simple, but the batch is governed by gas transfer, hydroxide consumption, carbonate-to-bicarbonate conversion, electrolyte activity, mixing, and charge balance. Increasing \(p_{\mathrm{CO_2}}\) sustains the thermodynamic and mass-transfer push toward bicarbonate, while GL-260 determines whether the resulting state is chemically consistent.

Suggested duration: 55 to 80 minutes.

## 1. Roadmap

Estimated time: 2 minutes.

### Presenter objective

Set expectations before introducing equipment or equations.

### Cover

- How sodium bicarbonate is made at CIL.
- The reactor, reaction manifold, and data-logging equipment.
- Why pure bicarbonate is difficult to produce from concentrated NaOH.
- How the equilibrium expressions are derived.
- How GL-260 calculates pH and speciation at different \(CO_2\) uptakes.
- How live \(CO_2\) consumption is measured and visualized.
- How the model supports the decision to continue or stop the reaction.

### Transition

Start with the physical process so every later equation can be tied to an actual piece of equipment or measurement.

## 2. How We Make Sodium Bicarbonate

Walkthrough sections:

- So, how do we make it?
- Reactor setup
- Reaction Manifold
- Data Logging Equipment

Estimated time: 5 to 8 minutes.

### Presenter objective

Connect the chemistry to the real apparatus before showing the model.

### Visual sequence

1. Reactor setup photograph.
2. Reaction manifold photograph.
3. Sensor and data-logging equipment photograph.

### Talking points

- The reactor provides the liquid/slurry inventory and mixing environment.
- The manifold controls the available gas pressure and repeated \(CO_2\) contact events.
- Pressure and temperature sensors provide the measurements used to identify cycles and estimate uptake.
- A gas charge is not automatically equivalent to absorbed \(CO_2\); transfer into the reactive phase is what matters.
- Mixing quality, temperature, gas-liquid contact, and slurry condition can make nominally similar charges behave differently.

### Transition

The apparatus tells us how \(CO_2\) reaches the batch. The next question is why the chemistry does not stop automatically at sodium bicarbonate.

## 3. Simple Equilibrium, Right?

Estimated time: 4 to 6 minutes.

### Presenter objective

Introduce the coupled carbonate-water system and challenge the single-reaction view.

### Key reactions

\[
\mathrm{CO_2^* \rightleftharpoons H^+ + HCO_3^-}
\]

\[
\mathrm{HCO_3^- \rightleftharpoons H^+ + CO_3^{2-}}
\]

\[
\mathrm{H_2O \rightleftharpoons H^+ + OH^-}
\]

### Talking points

- Bicarbonate exists within a network containing dissolved \(CO_2^*\), bicarbonate, carbonate, hydrogen, and hydroxide.
- Changing one species shifts the rest of the network.
- High pH does not simply make more bicarbonate; it can push bicarbonate onward to carbonate.
- The production question is therefore not only “Did we add \(CO_2\)?” but “Where did the absorbed carbon end up?”

### Audience prompt

What measurement would distinguish a bicarbonate-rich batch from a carbonate-rich batch if both absorbed substantial \(CO_2\)?

Expected answer: pH helps, but pH and speciation must be interpreted together.

## 4. Equilibrium Reactions in the Highly Basic System

Estimated time: 4 to 6 minutes.

### Presenter objective

Show the two-stage chemical path from NaOH to carbonate and then bicarbonate.

### Reaction sequence

1. Absorbed \(CO_2\) reacts with hydroxide:

   \[
   \mathrm{CO_2 + OH^- \rightarrow HCO_3^-}
   \]

2. Excess hydroxide converts bicarbonate to carbonate:

   \[
   \mathrm{HCO_3^- + OH^- \rightarrow CO_3^{2-} + H_2O}
   \]

3. The early net result is carbonate formation:

   \[
   \mathrm{2NaOH + CO_2 \rightarrow Na_2CO_3 + H_2O}
   \]

4. Additional \(CO_2\) converts carbonate to bicarbonate:

   \[
   \mathrm{Na_2CO_3 + CO_2 + H_2O \rightarrow 2NaHCO_3}
   \]

### Main takeaway

Carbonate is an expected intermediate when starting from concentrated NaOH. The batch must receive enough usable \(CO_2\) to carry that carbonate forward into bicarbonate.

### Transition

Quantify the starting sodium inventory and the two carbon-loading endpoints.

## 5. Starting Conditions

Estimated time: 5 to 7 minutes.

### Presenter objective

Establish the fixed basis used by every later calculation.

### Locked basis

- NaOH charge: \(700\ \mathrm{g}\).
- NaOH amount: \(17.5\ \mathrm{mol}\).
- Liquid volume: \(2.200\ \mathrm{L}\).
- Water basis: approximately \(2.2\ \mathrm{kg}\).
- Sodium molality basis: \(7.9545\ \mathrm{mol\ kg^{-1}}\).

### Carbon endpoints

- Carbonate midpoint: \(8.75\ \mathrm{mol}\) or approximately \(385.1\ \mathrm{g}\) \(CO_2\).
- Bicarbonate stoichiometric endpoint: \(17.5\ \mathrm{mol}\) or approximately \(770.2\ \mathrm{g}\) \(CO_2\).
- Presentation operating target: approximately \(775\ \mathrm{g}\) absorbed \(CO_2\).

### Talking points

- Sodium fixes the positive-charge inventory.
- The carbonate midpoint uses one mole of \(CO_2\) per two moles of NaOH.
- The bicarbonate endpoint uses one mole of \(CO_2\) per mole of NaOH.
- Every pH and speciation result must remain consistent with this material basis.

## 6. Equilibrium Half-Reactions: Dipping Our Toes In

Walkthrough subsections:

- Carbonate and Water Equilibrium Half-Reactions
- Constants Used in the NaOH-\(CO_2\) Calculation
- Using Activity

Estimated time: 6 to 9 minutes.

### Presenter objective

Introduce the constants and explain why activity replaces raw concentration in this concentrated system.

### Key points

- \(K_{a1}\) controls the first carbonic-acid dissociation.
- \(K_{a2}\) controls the bicarbonate-to-carbonate dissociation.
- \(K_w\) couples hydrogen and hydroxide activity.
- Henry’s law connects headspace \(p_{\mathrm{CO_2}}\) to dissolved \(CO_2^*\).
- In dilute solutions, \(a_i \approx m_i\) may be acceptable.
- In concentrated sodium-carbonate solutions, \(a_i=\gamma_i m_i\) is required because ion interactions change effective chemical availability.

### Transition

Use those constants to derive the overall base-side equilibrium expression.

## 7. Equilibrium: Diving Into the Deep End

Walkthrough subsections:

- Refresher: Equilibrium
- Advanced Derivation
- Add Half Reactions to Get the Overall Equilibrium Expression

Estimated time: 8 to 12 minutes.

### Presenter objective

Show how the half-reactions combine and what cancels from the overall expression.

### Derivation path

\[
K_{b1}=\frac{K_{a1}}{K_w},\qquad K_{b2}=\frac{K_{a2}}{K_w}
\]

Adding the two base-side reactions cancels bicarbonate as an intermediate:

\[
\mathrm{CO_2^* + 2OH^- \rightleftharpoons CO_3^{2-} + H_2O}
\]

\[
K_{eq,\mathrm{overall}}=K_{b1}K_{b2}=\frac{K_{a1}K_{a2}}{K_w^2}
\]

With \(a_{\mathrm{H_2O}}\approx1\):

\[
K_{eq,\mathrm{overall}}\approx\frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{CO_2^*}}a_{\mathrm{OH^-}}^2}
\]

### Talking points

- Bicarbonate cancels algebraically because it is produced in one step and consumed in the next.
- Its cancellation does not make bicarbonate operationally unimportant; it exposes how strongly dissolved \(CO_2\) and hydroxide control the path through it.
- Residual hydroxide strongly favors continued carbonate formation.
- The water-activity simplification is a presentation approximation, not a claim that concentrated solutions are ideal.

## 8. Controlling Bicarbonate Formation

Estimated time: 5 to 8 minutes.

### Presenter objective

Make \(p_{\mathrm{CO_2}}\) the explicit equilibrium and operating control lever.

### Ratio view

From the second base equilibrium:

\[
\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}}
=\frac{1}{K_{b2}a_{\mathrm{OH^-}}}
=\frac{K_w}{K_{a2}a_{\mathrm{OH^-}}}
\]

Henry’s law provides the gas-to-liquid boundary:

\[
[\mathrm{CO_2^*}]=K_Hp_{\mathrm{CO_2}}
\]

The carbonate-to-bicarbonate conversion can also be written as:

\[
\mathrm{CO_3^{2-}+CO_2^*\rightleftharpoons2HCO_3^-}
\]

\[
\frac{a_{\mathrm{HCO_3^-}}^2}{a_{\mathrm{CO_3^{2-}}}}
\approx\frac{K_{a1}}{K_{a2}}K_Hp_{\mathrm{CO_2}}
\]

### Talking points

- At fixed temperature and solution medium, the equilibrium constants do not change when concentration changes.
- Increasing \(p_{\mathrm{CO_2}}\) raises dissolved \(CO_2^*\), consumes alkalinity, and lowers hydroxide activity.
- Lower hydroxide activity raises the bicarbonate-to-carbonate ratio.
- For the defined batch, \(p_{\mathrm{CO_2}}\) is the available equilibrium lever for sustaining the push toward bicarbonate.
- The \(775\ \mathrm{g}\) target is absorbed \(CO_2\), while pressure is the driving boundary that helps deliver it.
- The displayed bicarbonate fraction is a solution-equilibrium purity potential, not a final dried-solid assay.

### Transition

The equilibrium direction is now clear. Next show how GL-260 calculates the actual pH and species fractions without doing the algebra manually for every state.

## 9. Calculating Speciation and pH

Walkthrough subsections:

- Calculating Speciation and pH
- Deriving Alpha Fractions From the Equilibrium Constants
- Derivation Summary

Estimated time: 8 to 12 minutes.

### Presenter objective

Explain that GL-260 accepts a pH only when species reconstruction and charge balance agree.

### Solver sequence

1. Fix \(C_T\), sodium, \(K_{a1}\), \(K_{a2}\), and \(K_w\).
2. Choose a trial pH and calculate \(h=[H^+]=10^{-\mathrm{pH}}\).
3. Build the shared denominator:

   \[
   D=h^2+K_{a1}h+K_{a1}K_{a2}
   \]

4. Calculate \(\alpha_0\), \(\alpha_1\), and \(\alpha_2\), then reconstruct all carbonate species.
5. Calculate hydroxide from \(K_w/h\).
6. Evaluate charge residual \(R_q\).
7. Move the pH bracket until \(|R_q|\) meets the acceptance tolerance.

### Central equation

\[
R_q(h)=[\mathrm{Na^+}]+h-\frac{K_w}{h}-C_T\left(\frac{K_{a1}h+2K_{a1}K_{a2}}{h^2+K_{a1}h+K_{a1}K_{a2}}\right)=0
\]

### Talking points

- Alpha fractions are derived from equilibrium constants; they are not fitted percentages.
- The accepted root produces pH, hydroxide, and all three species from the same state.
- Carbon closure, fraction closure, and charge closure are required together.
- The presentation shows the ideal form; the concentrated model updates activities and coefficients around the same solve.

## 10. NaOH-CO2 Pitzer Calculation Path

Estimated time: 6 to 9 minutes.

### Presenter objective

Explain why the concentrated system needs HMW/Pitzer activity corrections.

### Talking points

- Molality alone overstates or understates effective chemical availability when ions interact strongly.
- Pitzer terms calculate activity coefficients for sodium, hydroxide, bicarbonate, carbonate, and hydrogen.
- The solver iterates between speciation, ionic strength, activity coefficients, and charge balance.
- HMW/PHREEQC Na-carbonate pairing supplies the focused interaction basis used by the walkthrough.
- Activity correction changes the calculated crossover between carbonate and bicarbonate.
- The operational conclusion remains understandable: corrected activities produce a more defensible pH and purity estimate.

### Audience-level guidance

For a general audience, explain what the correction accomplishes rather than presenting every interaction coefficient.

## 11. Reaction Kinetics

Walkthrough subsections:

- Reaction Kinetics
- Liquid-Gas Interaction
- Pseudo-First-Order View at High Hydroxide Concentration
- Time-Scale Test for Interpreting Cycle Shape
- How This Connects to GL-260 Cycle Detection

Estimated time: 8 to 12 minutes.

### Presenter objective

Separate equilibrium destination from the rate and physical path used to reach it.

### Talking points

- \(k_La\) controls gas-to-liquid transfer.
- High hydroxide causes rapid early consumption of dissolved \(CO_2\), maintaining a strong transfer gradient.
- As hydroxide is depleted, pressure decay and apparent reaction rate change.
- Mixing affects local concentration gradients, exposed interfacial area, temperature distribution, and slurry re-equilibration.
- A pressure event can end before the full slurry has reached its final equilibrium state.
- Cycle detection converts the measured pressure history into repeatable event boundaries for uptake calculations.

### Operational takeaway

The same nominal pressure charge can yield different usable uptake if transfer, mixing, temperature, or reaction time differs.

## 12. Cycle Uptake Math

Walkthrough subsections:

- Primary Synthetic Cycle Uptake Sequence
- Pressure-Derived Uptake

Estimated time: 5 to 7 minutes.

### Presenter objective

Show how measured pressure events become cumulative carbon loading.

### Talking points

- The locked synthetic sequence provides a deterministic teaching trajectory.
- Pressure, temperature, and calibrated gas volume determine the gas-mole change for a cycle.
- The calculation separates charged gas from inferred absorbed gas.
- Cycle increments accumulate into total \(CO_2\) uptake.
- Cumulative uptake is converted from grams to moles and then to total-carbon molality for the equilibrium solve.

### Transition

Apply the complete calculation chain to three deliberately different uptake regions.

## 13. Integrated Worked Examples

Walkthrough subsections:

- Shared Basis and Calculation Sequence
- Worked Example A: 250 g \(CO_2\) Uptake
- Worked Example B: 650 g \(CO_2\) Uptake
- Worked Example C: 950 g \(CO_2\) Uptake
- Worked-Example Comparison

Estimated time: 10 to 15 minutes.

### Presenter objective

Demonstrate that uptake alone is not the state; the same calculation must identify the chemical region and close all balances.

### Shared calculation chain

1. Convert measured uptake to moles and total-carbon molality.
2. Compare uptake with the carbonate and bicarbonate endpoints.
3. Apply the appropriate stoichiometric-region logic.
4. Solve the activity-corrected equilibrium state.
5. Verify carbon, fraction, and charge closure.

### Example A: 250 g

- Region: before first equivalence.
- Significant hydroxide remains.
- Calculated pH: approximately \(14.8117\).
- Reactive carbon is effectively carbonate-dominant in the focused example.
- Message: early uptake does not imply bicarbonate formation.

### Example B: 650 g

- Region: between first and second equivalence.
- Calculated pH: approximately \(9.1405\).
- Bicarbonate fraction: approximately \(81.46\%\).
- Carbonate fraction: approximately \(18.51\%\).
- Message: bicarbonate can dominate while carbonate impurity remains material.

### Example C: 950 g

- Region: beyond the focused model’s sodium-limited reactive capacity.
- Input uptake exceeds the approximately \(770.2\ \mathrm{g}\) bicarbonate endpoint.
- The model caps reactive carbon at \(17.5\ \mathrm{mol}\) and reports excess separately.
- Capped pH: approximately \(7.8538\).
- Capped bicarbonate fraction: approximately \(98.67\%\).
- Message: excess measured uptake must not be forced silently into a model that lacks the required phase-partition scope.

### Comparison takeaway

Increasing uptake consumes free hydroxide, moves the system from carbonate toward bicarbonate, and lowers pH. Capacity checks are required before interpreting beyond-endpoint results.

## 14. Worked NaOH-Pitzer Simulation Table

Estimated time: 4 to 6 minutes.

### Presenter objective

Read the synthetic cycle table as one continuous operating trajectory.

### Talking points

- Early cycles remain strongly caustic and carbonate-forming.
- Near \(385\ \mathrm{g}\), the system approaches the carbonate midpoint.
- Between the endpoints, bicarbonate increases while carbonate declines.
- Near \(760\) to \(775\ \mathrm{g}\), the modeled state becomes strongly bicarbonate-dominant.
- Read cumulative uptake, pH, hydroxide, bicarbonate fraction, and carbonate fraction together.

## 15. Worked Real-World Example: PR-24304

Walkthrough subsections:

- Profile Basis and Stoichiometric Translation
- Reading the Combined Triple-Axis Plot
- Reading the Speciation Timeline Plot
- How To Narrate the Real-Data Chain

Estimated time: 7 to 10 minutes.

### Presenter objective

Connect the theoretical chain to actual process evidence.

### Profile basis

- Saved NaOH charge: \(702.0\ \mathrm{g}\).
- Implied NaOH amount: \(17.55\ \mathrm{mol}\).
- Ideal one-to-one bicarbonate requirement: approximately \(772.4\ \mathrm{g}\) \(CO_2\).

### Plot narration

1. Use reactor pressure to identify gas-contact events.
2. Use pressure derivative to show the strongest uptake windows and cycle boundaries.
3. Use temperature traces to identify thermal effects on pressure and rate interpretation.
4. Compare cumulative inferred uptake with the stoichiometric target.
5. Use the speciation timeline to explain the transition from caustic/carbonate-rich to bicarbonate-rich conditions.
6. Use measured pH anchors, when available, to align the run-specific prediction.

### Main takeaway

The plot provides physical evidence; stoichiometry defines the target; the Pitzer equilibrium model interprets the chemical state.

## 16. Measured-pH Calibration and Hybrid ML Correction

Walkthrough subsections:

- Locked Multi-Anchor Example
- Baseline Piecewise Calibration Objective
- Historical Anchors and Cross-Run Learning
- Why Prediction Accuracy Improves Every Run
- Residual ML Ridge Correction Stage
- Fail-Closed Anchor Guard

Estimated time: 7 to 10 minutes.

### Presenter objective

Explain how measured evidence improves the trajectory without replacing the chemistry.

### Talking points

- Measured pH anchors quantify the difference between the baseline equilibrium trajectory and the observed batch.
- Piecewise calibration bends the baseline toward trusted anchors.
- Historical anchors can improve later runs when their contexts are comparable.
- Ridge residual learning is a secondary correction layer, not the primary equilibrium model.
- Anchor-quality checks compare corrected and baseline errors.
- If the learned correction degrades anchor fidelity or violates its guardrails, runtime fails closed to the baseline corrected series.

### Main takeaway

Calibration improves alignment while equilibrium, material balance, and charge balance remain the governing structure.

## 17. How Dashboard Values Are Computed

Walkthrough subsections:

- Required \(CO_2\) Source Precedence
- Target Gap and Completion
- Corrected vs Baseline pH Channels

Estimated time: 4 to 6 minutes.

### Presenter objective

Show that dashboard values are deterministic summaries rather than disconnected indicators.

### Talking points

- Required \(CO_2\) follows a defined source-precedence chain.
- Target gap is calculated from required minus corrected cumulative uptake and is clamped at zero.
- Completion is bounded so the interface does not report nonsensical negative or unbounded states.
- Baseline equilibrium pH and corrected pH remain separate channels.
- Operators should be able to trace every KPI back to its source, correction status, and fallback path.

## 18. Closing Summary

Estimated time: 3 to 5 minutes.

### Final narrative

GL-260 links the complete process chain:

- physical equipment and sensor evidence,
- sodium inventory,
- cycle-level \(CO_2\) uptake,
- carbonate-water equilibrium,
- \(p_{\mathrm{CO_2}}\) control,
- Pitzer activity correction,
- charge-balanced pH and speciation,
- kinetics and mixing interpretation,
- measured-pH calibration,
- and deterministic dashboard guidance.

### Closing line

The endpoint is not defined by pressure, uptake, or pH alone. It is the point where sufficient absorbed \(CO_2\), bicarbonate-dominant speciation, charge balance, and process evidence agree.

## Presenter Guardrails

- Do not describe gas charged to the manifold as automatically absorbed by the liquid.
- Do not describe the modeled bicarbonate fraction as a measured final solid-purity assay.
- Do not interpret the 950 g capped solution as proof that all 950 g exists in the reactive liquid phase.
- Do not present pH as independent of speciation and charge balance.
- Do not imply that calibration or ML replaces the equilibrium model.
- State that temperature, solution medium, activity coefficients, and phase behavior define the limits of simplified equations.

## Backup Discussion Prompts

- Why is carbonate formed first in a strongly basic NaOH batch?
- Why can two batches with similar charged \(CO_2\) reach different pH values?
- What is the difference between headspace \(p_{\mathrm{CO_2}}\) and absorbed \(CO_2\) mass?
- Why does increasing \(p_{\mathrm{CO_2}}\) favor bicarbonate?
- Why is pH insufficient without a species distribution?
- What does charge closure prove?
- Why do concentrated solutions require activity corrections?
- How can mixing change the observed pressure-decay curve?
- Why must the model cap or separate carbon beyond reactive capacity?
- When should measured-pH calibration be rejected?

## Condensed 25-Minute Version

1. Equipment and process setup: 3 minutes.
2. Highly basic reaction sequence and starting basis: 4 minutes.
3. Overall equilibrium and \(p_{\mathrm{CO_2}}\) control: 5 minutes.
4. Charge-balanced pH/speciation and Pitzer correction: 5 minutes.
5. Uptake examples and real PR-24304 plots: 5 minutes.
6. Calibration, dashboard meaning, and close: 3 minutes.

## One-Slide Takeaway

Starting from concentrated NaOH produces carbonate first. Additional absorbed \(CO_2\), sustained by sufficient \(p_{\mathrm{CO_2}}\), consumes alkalinity and moves the equilibrium toward bicarbonate. GL-260 combines measured uptake, activity-corrected equilibrium, charge balance, and measured-pH evidence to determine whether the batch has actually reached a defensible bicarbonate-rich endpoint.
