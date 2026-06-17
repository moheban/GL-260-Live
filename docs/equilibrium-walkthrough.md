# GL-260 Equilibrium and Simulation Walkthrough (700 g NaOH Case)

## Purpose
This walkthrough will be used to understand the sodium bicarbonate reaction and all the challenges associated with it.

This walkthrough will show you how i compute:

- equilibrium pH,
- carbonate speciation,
- cycle CO2 uptake,
- reaction kinetics and uptake-rate interpretation,
- measured-pH anchored calibration,
- residual ML pH correction in Analysis mode.
- real PR-24304 presentation data,
- HMW/PHREEQC Na-carbonate Pitzer pairing.

We will discuss how cycles are identified, uptake is calculated, reaction kinetics are interpreted, pH is predicted for each cycle, and we will derive detailed equilibrium expressions that are used to calculate pH with +/- 0.5 accuracy.

We will go through a simulation and then ill show a real world example with real data in the program.

## Locked Assumptions for This Walkthrough
All values in this document are locked to one deterministic scenario so intermediate results are reproducible during live explanation.

- Temperature: `Average temp used for each cycle`
- Water basis: `2,200 mL` pure water (`2.2 kg` water approximation)
- NaOH charge: `700 g`
- NaOH purity: `100%` (for this worked example)
- Synthetic fixed cycle uptake sequence (g CO2 per cycle):
  - `[80, 90, 100, 110, 120, 130, 130, 140]`
  - Total cumulative CO2: `900 g`
- Measured pH anchors (multi-anchor example):
  - Cycle 5: `pH = 9.74`
  - Cycle 9: `pH = 9.34`
- Real-world worked example profile:
  - `profiles/PR-24304 CLM-441-MPT Sodium Bicarbonate Batch 1 of 2.json`
  - reaction basis: `NaOH + CO2 -> NaHCO3`
  - starting NaOH basis in profile: `702.0 g`
  - product: sodium bicarbonate (`NaHCO3`)

---

## 1) Basis Setup (700 g NaOH in 2,200 mL Water)

!!! note "Calculation Legend"
    - \(m_{\mathrm{NaOH}}\): NaOH mass charged to solution [`g`]
    - \(MW_{\mathrm{NaOH}}\): NaOH molecular weight [\(g mol^{-1}\)]
    - \(n_{\mathrm{NaOH}}\): NaOH amount [`mol`]
    - \(V_{\mathrm{liq}}\): liquid volume [`L`]
    - \(kg_{\mathrm{water}}\): water mass basis [`kg`]
    - \(C_{\mathrm{NaOH}}\): NaOH molarity [\(mol L^{-1}\)]
    - \(m_{\mathrm{NaT}}\): total sodium molality [\(mol kg^{-1}\)]
    - \(n_{\mathrm{CO_2,eq1}}\), \(n_{\mathrm{CO_2,eq2}}\): CO2 mole endpoints [`mol`]
    - \(m_{\mathrm{CO_2,eq1}}\), \(m_{\mathrm{CO_2,eq2}}\): CO2 mass endpoints [`g`]

Converting mass to molarity/molality defines the two stoichiometric constants used for later calculations.

!!! info "Derivation Walkthrough"
    **Goal:** Convert NaOH mass into concentration terms that is used in every later equilibrium equation.

    **Step-by-step interpretation:** first compute \(n_{\mathrm{NaOH}}\), then normalize by liquid volume (\(C_{\mathrm{NaOH}}\)) and water mass (\(m_{\mathrm{NaT}}\)), then convert the two stoichiometric CO2 endpoints to grams.

    **Why this changes operation:** these endpoint masses define where bicarbonate formation can be maximized.

<style>
.basis-expression-map {
  margin: 1rem 0 1.2rem;
  border: 1px solid #cfe3ec;
  border-radius: 12px;
  background: linear-gradient(135deg, #fcfeff 0%, #f5fbff 60%, #fffaf0 100%);
  padding: 14px;
  display: grid;
  gap: 14px;
  overflow: hidden;
}
.basis-expression-map p {
  margin: 0;
}
.basis-expression-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
}
.basis-expression-title {
  color: #19384a;
  font-family: var(--heading-font);
  font-size: 0.86rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.basis-expression-copy {
  margin-top: 4px;
  color: #345468;
}
.basis-expression-result {
  min-width: 118px;
  border: 1px solid #d7e8ec;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  padding: 8px 10px;
  text-align: right;
}
.basis-expression-result span {
  display: block;
  color: #5f7888;
  font-size: 0.74rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.basis-expression-result strong {
  display: block;
  color: #102839;
  font-family: var(--heading-font);
  font-size: 1.35rem;
  line-height: 1;
}
.basis-expression-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.8fr) minmax(260px, 1.2fr);
  gap: 12px;
}
.basis-expression-panel {
  border: 1px solid #d8e8ee;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.76);
  padding: 12px;
  display: grid;
  gap: 10px;
}
.basis-expression-panel h4 {
  margin: 0;
  color: #19384a;
  font-family: var(--heading-font);
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.basis-expression-row {
  border: 1px solid #d9e9f3;
  border-radius: 9px;
  background: #ffffff;
  padding: 9px 10px;
  display: grid;
  gap: 5px;
  overflow-x: auto;
}
.basis-expression-row span {
  color: #5f7888;
  font-size: 0.76rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.basis-expression-row .math-inline-display {
  margin: 0;
  color: #000000;
  font-size: 1.08rem;
}
.basis-expression-flow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.basis-expression-stage {
  border: 1px solid #d8e8ee;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.76);
  padding: 10px;
  min-height: 104px;
  display: grid;
  align-content: start;
  gap: 6px;
  position: relative;
}
.basis-expression-stage::after {
  content: "";
  position: absolute;
  right: -8px;
  top: 50%;
  width: 8px;
  height: 2px;
  background: #bdd7e2;
}
.basis-expression-stage:last-child::after {
  display: none;
}
.basis-expression-stage span {
  color: #5f7888;
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.basis-expression-stage strong {
  color: #102839;
  font-family: var(--heading-font);
  font-size: 1.02rem;
}
.basis-expression-stage .math-inline-display {
  margin: 0;
  color: #000000;
  font-size: 1.08rem;
}
.basis-expression-callout {
  border-left: 3px solid #1fb8cb;
  border-radius: 8px;
  background: rgba(239, 248, 250, 0.74);
  padding: 8px 10px;
  color: #345468;
}
.calculation-map {
  margin: 1rem 0 1.2rem;
  border: 1px solid #cfe3ec;
  border-radius: 12px;
  background: linear-gradient(135deg, #fcfeff 0%, #f5fbff 60%, #fffaf0 100%);
  padding: 14px;
  display: grid;
  gap: 14px;
  overflow: hidden;
}
.calculation-map p {
  margin: 0;
}
.calculation-map-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
}
.calculation-map-title {
  color: #19384a;
  font-family: var(--heading-font);
  font-size: 0.86rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.calculation-map-copy {
  margin-top: 4px;
  color: #345468;
}
.calculation-map-badge {
  min-width: 108px;
  border: 1px solid #d7e8ec;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  padding: 8px 10px;
  text-align: right;
}
.calculation-map-badge span {
  display: block;
  color: #5f7888;
  font-size: 0.74rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.calculation-map-badge strong {
  display: block;
  color: #102839;
  font-family: var(--heading-font);
  font-size: 1.2rem;
  line-height: 1;
}
.calculation-map-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.calculation-map-grid.three-up {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.calculation-map-grid.four-up {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.calculation-map-step {
  border: 1px solid #d9e9f3;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  padding: 10px;
  display: grid;
  align-content: start;
  gap: 6px;
  min-width: 0;
  overflow-x: auto;
}
.calculation-map-step span {
  color: #5f7888;
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.calculation-map-step strong {
  color: #102839;
  font-family: var(--heading-font);
  font-size: 1rem;
}
.calculation-map-step .math-inline-display {
  margin: 0;
  color: #000000;
  font-size: 1.08rem;
}
.basis-expression-row .math-inline,
.basis-expression-row .math-inline math,
.basis-expression-stage .math-inline,
.basis-expression-stage .math-inline math,
.calculation-map-step .math-inline,
.calculation-map-step .math-inline math {
  color: #000000;
}
.calculation-map-callout {
  border-left: 3px solid #1fb8cb;
  border-radius: 8px;
  background: rgba(239, 248, 250, 0.74);
  padding: 8px 10px;
  color: #345468;
}
@media (max-width: 760px) {
  .basis-expression-heading,
  .basis-expression-grid,
  .basis-expression-flow,
  .calculation-map-heading,
  .calculation-map-grid,
  .calculation-map-grid.three-up,
  .calculation-map-grid.four-up {
    grid-template-columns: 1fr;
  }
  .basis-expression-result,
  .calculation-map-badge {
    text-align: left;
  }
  .basis-expression-stage::after {
    display: none;
  }
}
</style>

<div class="basis-expression-map">
  <div class="basis-expression-heading">
    <div>
      <p class="basis-expression-title">Section 1 Calculation Map</p>
      <p class="basis-expression-copy">Start with the charged NaOH mass, convert it into concentration bases, then mark the CO2 endpoints that frame carbonate and bicarbonate formation.</p>
    </div>
    <div class="basis-expression-result">
      <span>NaOH basis</span>
      <strong>17.5 mol</strong>
    </div>
  </div>

  <div class="basis-expression-grid">
    <div class="basis-expression-panel">
      <h4>Given Inputs</h4>
      <div class="basis-expression-row">
        <span>NaOH charge</span>
        \[m_{\mathrm{NaOH}} = 700\ \mathrm{g}\]
      </div>
      <div class="basis-expression-row">
        <span>Molecular weight</span>
        \[MW_{\mathrm{NaOH}} = 40.00\ \mathrm{g\ mol^{-1}}\]
      </div>
      <div class="basis-expression-row">
        <span>Liquid basis</span>
        \[V_{\mathrm{liq}} = 2.200\ \mathrm{L}\]
        \[kg_{\mathrm{water}} \approx 2.2\ \mathrm{kg}\]
      </div>
    </div>

    <div class="basis-expression-panel">
      <h4>Converted Bases</h4>
      <div class="basis-expression-row">
        <span>Moles charged</span>
        \[n_{\mathrm{NaOH}} = \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}} = \frac{700\ \mathrm{g}}{40.00\ \mathrm{g\ mol^{-1}}} = 17.5\ \mathrm{mol}\]
      </div>
      <div class="basis-expression-row">
        <span>Molarity basis</span>
        \[C_{\mathrm{NaOH}} = \frac{n_{\mathrm{NaOH}}}{V_{\mathrm{liq}}} = \frac{17.5\ \mathrm{mol}}{2.200\ \mathrm{L}} = 7.9545\ \mathrm{mol\ L^{-1}}\]
      </div>
      <div class="basis-expression-row">
        <span>Molality sodium basis</span>
        \[m_{\mathrm{NaT}} = \frac{n_{\mathrm{NaOH}}}{kg_{\mathrm{water}}} = \frac{17.5\ \mathrm{mol}}{2.2\ \mathrm{kg}} = 7.9545\ \mathrm{mol\ kg^{-1}}\]
      </div>
    </div>
  </div>

  <div class="basis-expression-flow" aria-label="Stoichiometric CO2 endpoint flow">
    <div class="basis-expression-stage">
      <span>Endpoint 1</span>
      <strong>Carbonate-rich midpoint</strong>
      \[n_{\mathrm{CO_2,eq1}} = \frac{n_{\mathrm{NaOH}}}{2} = 8.75\ \mathrm{mol}\]
    </div>
    <div class="basis-expression-stage">
      <span>Mass equivalent</span>
      <strong>CO2 to eq1</strong>
      \[m_{\mathrm{CO_2,eq1}} = 8.75\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 385.1\ \mathrm{g}\]
    </div>
    <div class="basis-expression-stage">
      <span>Endpoint 2</span>
      <strong>Bicarbonate target</strong>
      \[n_{\mathrm{CO_2,eq2}} = n_{\mathrm{NaOH}} = 17.5\ \mathrm{mol}\]
      \[m_{\mathrm{CO_2,eq2}} = 17.5\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 770.2\ \mathrm{g}\]
    </div>
  </div>

  <p class="basis-expression-callout">The two concentration bases, \(C_{\mathrm{NaOH}}\) and \(m_{\mathrm{NaT}}\), become the fixed sodium inventory used later by charge balance, speciation, and cycle-by-cycle pH prediction.</p>
</div>

!!! tip "Approximation Note"
    Approximation note: \(kg_{\mathrm{water}} \approx 2.2\ \mathrm{kg}\) assumes pure-water density near \(1.0\ \mathrm{kg\ L^{-1}}\).


<div class="inline-chart-anchor" data-inline-chart="stoich-impact"></div>


---

## 2) Equilibrium Half-Reactions, Constants, and Activities
These half-reactions and constants provide the thermodynamic constraints that all downstream pH/speciation calculations must satisfy.

### 2.1 Carbonate and Water Equilibrium Half-Reactions

!!! note "Calculation Legend"
    - \(K_{a1}\), \(K_{a2}\), \(K_{w}\): equilibrium constants in activity form
    - \(a_{i}\): activity of species `i`
    - \(\gamma_i\): activity coefficient of species `i`
    - \(m_{i}\): molality of species `i` [\(mol kg^{-1}\)]
    - \(K_{H}\): Henry constant used by the model [\(mol kg^{-1} atm^{-1}\)]
    - \(p_{\mathrm{CO_2}}\): \(CO_{2}\) partial pressure `[atm]`
    - \([\mathrm{CO_2^*}]\): dissolved molecular \(CO_{2}\) plus hydrated carbonic acid basis [\(mol kg^{-1}\)]


<table class="reaction-map">
<thead>
<tr>
<th>Half Reaction</th>
<th>Equilibrium Expression</th>
</tr>
</thead>
<tbody>
<tr>
<td>\[\mathrm{CO_2^*} \rightleftharpoons \mathrm{H^+} + \mathrm{HCO_3^-}\]</td>
<td>\[K_{a1} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}}\]</td>
</tr>
<tr>
<td>\[\mathrm{HCO_3^-} \rightleftharpoons \mathrm{H^+} + \mathrm{CO_3^{2-}}\]</td>
<td>\[K_{a2} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}\]</td>
</tr>
<tr>
<td>\[\mathrm{H_2O} \rightleftharpoons \mathrm{H^+} + \mathrm{OH^-}\]</td>
<td>\[K_w = a_{\mathrm{H^+}} \times a_{\mathrm{OH^-}}\]</td>
</tr>
</tbody>
</table>

<div class="calculation-map">
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Activity definition</span>
      \[
      a_i = \gamma_i \times m_i
      \]
    </div>
    <div class="calculation-map-step">
      <span>Fixed-headspace CO2 boundary</span>
      \[
      [\mathrm{CO_2^*}] = K_H \times p_{\mathrm{CO_2}}
      \]
    </div>
  </div>
</div>

### 2.2 Constants Used by the NaOH-CO2 Pitzer Example Path (25 C)

!!! note "Calculation Legend"
    - \(K_{a1}\): first dissociation constant
    - \(K_{a2}\): second dissociation constant
    - \(K_{w}\): water autoionization constant


In `naoh_co2_pitzer_ph_model.py`:

<div class="calculation-map">
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>First dissociation</span>
      \[
      K_{a1} = 10^{-6.3374}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Second dissociation</span>
      \[
      K_{a2} = 10^{-10.3393}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Water autoionization</span>
      \[
      K_w \approx 10^{-14}
      \]
    </div>
  </div>
</div>

### 2.3 What Activities Change Compared With Concentrations

!!! note "Calculation Legend"
    - `ideal model`: assumes \(\gamma_i = 1\), so activity equals molality.
    - `activity-corrected model`: computes \(\gamma_i\), then uses \(a_i = \gamma_i m_i\).
    - `high ionic strength`: concentrated electrolyte condition where ion-ion interactions materially change apparent equilibrium behavior.

For dilute solutions, we can often use concentration directly, \(a_i \approx m_i\).

In dilute solutions, that approximation means each dissolved species behaves as though it were alone in water. Starting conditions when synthesizing sodium bicarbonate is not dilute: a 700 g NaOH charge in 2.2 kg water gives roughly `7.95 mol/kg` molality before CO2 loading. 

At that ionic strength, sodium, hydroxide, bicarbonate, and carbonate are **not** independent. Each ion is surrounded by an ionic atmosphere, and the thermodynamic effective concentration is activity: \(a_i = \gamma_i \times m_i\).

The activity coefficient \(\gamma_i\) is the correction term. 

If \(\gamma_i < 1\), the species is less thermodynamically active than its molality alone would imply. If \(\gamma_i > 1\), it is more active. Pitzer terms are used because they are designed for concentrated electrolyte solutions where Debye-Huckel-style dilute corrections are not enough.

For pH this distinction matters directly:

<div class="calculation-map">
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Activity-correct pH</span>
      \[
      \mathrm{pH} = -\log_{10}(a_{\mathrm{H^+}})
      \]
    </div>
    <div class="calculation-map-step">
      <span>Ideal-only shortcut</span>
      \[
      \mathrm{pH} = -\log_{10}(m_{\mathrm{H^+}})
      \]
    </div>
  </div>
  <p class="calculation-map-callout">The activity-corrected expression is the safer path for concentrated sodium-carbonate systems.</p>
</div>

The difference is why we treat the Pitzer path as the best sodium bicarbonate prediction path instead of just relying only on ideal alpha fractions.

---

## 3) Complete Keq Expression

!!! note "Calculation Legend"
    - \(K_{b1}\), \(K_{b2}\): base-side equilibrium constants
    - \(K_{eq,\mathrm{overall}}\): overall equilibrium constant
    - \(a_{\mathrm{H_2O}}\): water activity, often approximated as `1` in concentrated electrolyte systems

The overall equilibrium relationship is explicitly tied to the half-reaction constants, enabling direct calculation of the species involved and subsequently the pH.

!!! info "Derivation Walkthrough"
    **Goal:** show the derivation of the overall equilibrium expression.

    **Step-by-step interpretation:** define each half reaction, write \(K_{b1}\) and \(K_{b2}\) in activity form, then multiply them to recover the overall expression and map to \({K_{a1}, K_{a2}, K_{w}}\).

    **Why this matters:** this will be the expression later calculations will be based on

The overall equilibrium expression can be shown in two half-steps:

<table class="reaction-map">
<thead>
<tr>
<th>Half Reaction</th>
<th>Equilibrium Expression / Calculation</th>
</tr>
</thead>
<tbody>
<tr>
<td>\[\mathrm{CO_2^*} + \mathrm{OH^-} \rightleftharpoons \mathrm{HCO_3^-}\]</td>
<td>\[K_{b1} = \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}}\]<br>\[K_{b1} = \frac{K_{a1}}{K_w}\]</td>
</tr>
<tr>
<td>\[\mathrm{HCO_3^-} + \mathrm{OH^-} \rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O}\]</td>
<td>\[K_{b2} = \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}}\]<br>\[K_{b2} \approx \frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}}\]<br>\[K_{b2} = \frac{K_{a2}}{K_w}\]</td>
</tr>
</tbody>
</table>

### 3.1 Add Half Reactions to Recover the Overall Reaction
The overall carbonate-neutralization chemistry is the direct sum of the two half reactions above.

<table class="reaction-map">
<thead>
<tr>
<th>Reaction Expression</th>
<th>Resulting Expression</th>
</tr>
</thead>
<tbody>
<tr>
<td>\[\left(\mathrm{CO_2^*} + \mathrm{OH^-} \rightleftharpoons \mathrm{HCO_3^-}\right) + \left(\mathrm{HCO_3^-} + \mathrm{OH^-} \rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O}\right)\]</td>
<td>Add the two half reactions and cancel the intermediate \(\mathrm{HCO_3^-}\) term.</td>
</tr>
<tr>
<td>\[\mathrm{CO_2^*} + 2\mathrm{OH^-} \rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O}\]</td>
<td>\[K_{eq,\mathrm{overall}} = K_{b1} \times K_{b2}\]</td>
</tr>
</tbody>
</table>

The \(\mathrm{HCO_3^-}\) term cancels in the algebra because it is an intermediate produced in the first half-step and consumed in the second. 

**This means bicarbonate quality is controlled by how strongly each half-step is driven in practice: we want to favor \(\mathrm{CO_2^*} + \mathrm{OH^-} \rightarrow \mathrm{HCO_3^-}\) while suppressing \(\mathrm{HCO_3^-} + \mathrm{OH^-} \rightarrow \mathrm{CO_3^{2-}} + \mathrm{H_2O}\), achieved by increasing dissolved \(CO_{2}\) (\(p_{\mathrm{CO_2}}\)), reducing effective \(\mathrm{OH^-}\) through loading stage progression, and avoiding excessive residual alkalinity.**

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Overall Keq Calculation Map</p>
      <p class="calculation-map-copy">Multiply the two base-side half-reaction constants, cancel the bicarbonate intermediate, then substitute the acid and water constants to recover the full activity expression.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Result</span>
      <strong>\(K_{eq}\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Multiply half-steps</span>
      \[
      K_{eq,\mathrm{overall}}
      =
      \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}}
      \times
      \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Cancel intermediate</span>
      \[
      K_{eq,\mathrm{overall}} = \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Water activity simplification</span>
      \[
      K_{eq,\mathrm{overall}} \approx \frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
      \quad\text{when}\quad a_{\mathrm{H_2O}} \approx 1
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Constant relationship</span>
      \[
      K_{eq,\mathrm{overall}} = \frac{K_{a1} \times K_{a2}}{K_w^2}
      \]
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Acid constant 1</span>
      \[
      K_{a1} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Acid constant 2</span>
      \[
      K_{a2} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Water constant</span>
      \[
      K_w = a_{\mathrm{H^+}} \times a_{\mathrm{OH^-}}
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>5. Full substitution before cancellation</span>
    \[
    K_{eq,\mathrm{overall}}
    =
    \frac{
    \left(\frac{a_{\mathrm{H^+}} \times a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}}\right)
    \times
    \left(\frac{a_{\mathrm{H^+}} \times a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}\right)
    }{
    \left(a_{\mathrm{H^+}} \times a_{\mathrm{OH^-}}\right)^2
    }
    \]
  </div>
  <p class="calculation-map-callout">Canceling \(a_{\mathrm{HCO_3^-}}\) and \(a_{\mathrm{H^+}}^2\) recovers \(K_{eq,\mathrm{overall}} = a_{\mathrm{CO_3^{2-}}}/(a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2)\) when \(a_{\mathrm{H_2O}} \approx 1\).</p>
</div>

!!! tip "Approximation Note"
    Approximation note: terms with \(\approx\) follow the common \(a_{\mathrm{H_2O}} \approx 1\) simplification used for interpretability.


---

## 4) Speciation and pH Derivation Used in GL-260

!!! note "Calculation Legend"
    - \([H^+]\), \([\mathrm{OH^-}]\), \([\mathrm{CO_2^*}]\), \([\mathrm{HCO_3^-}]\), \([\mathrm{CO_3^{2-}}]\), \([\mathrm{Na^+}]\): concentration/molarity-like model terms [\(mol L^{-1}\)] or model-consistent concentration basis]
    - \(C_{T}\): total inorganic carbon concentration on the same basis as reconstructed species
    - \(\alpha_0\), \(\alpha_1\), \(\alpha_2\): species fractions
    - \(D\): shared denominator in alpha-fraction identities
    - \(R_{q}\): charge-balance residual on concentration basis (target is zero)

GL-260 solves charge balance to recover \([H^+]\), then reconstructs species fractions and pH consistently from that solution.

!!! info "Derivation Walkthrough"
    **Goal:** recover all carbonate species and pH from one consistent solution variable (\([H^+]\)).

    **Step-by-step interpretation:** compute the shared denominator \(D\), derive \(\alpha_0/\alpha_1/\alpha_2\), reconstruct species with \(C_{T}\), then close with charge-balance residual \(R_{q}\) = 0.

    **Why this changes operation:** bicarbonate-control decisions are only trustworthy when one solved state satisfies both speciation and charge closure; otherwise purity guidance can point to the wrong operating region.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">pH and Speciation Solver Map</p>
      <p class="calculation-map-copy">Choose a trial \([H^+]\), build the carbonate fractions, reconstruct species from total carbon, then close charge balance.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Target</span>
      <strong>\(R_q = 0\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Shared denominator</span>
      \[
      D = [H^+]^2 + (K_{a1} \times [H^+]) + (K_{a1} \times K_{a2})
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Alpha fractions</span>
      \[
      \alpha_0 = \frac{[H^+]^2}{D}
      \]
      \[
      \alpha_1 = \frac{K_{a1} \times [H^+]}{D}
      \]
      \[
      \alpha_2 = \frac{K_{a1} \times K_{a2}}{D}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Reconstruct species</span>
      \[
      [\mathrm{CO_2^*}] = \alpha_0 \times C_T
      \]
      \[
      [\mathrm{HCO_3^-}] = \alpha_1 \times C_T
      \]
      \[
      [\mathrm{CO_3^{2-}}] = \alpha_2 \times C_T
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. pH and hydroxide</span>
      \[
      \mathrm{pH} = -\log_{10}([H^+])
      \]
      \[
      [\mathrm{OH^-}] = \frac{K_w}{[H^+]}
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>5. Charge-balance residual and solver target</span>
    \[
    R_q = [\mathrm{Na^+}] + [\mathrm{H^+}] - [\mathrm{OH^-}] - [\mathrm{HCO_3^-}] - (2 \times [\mathrm{CO_3^{2-}}])
    \]
    \[
    R_q = 0
    \]
  </div>
</div>

The charge residual is important because it is the numerical test that the proposed pH and species distribution are chemically self-consistent. The left side of \(R_q\) counts positive charge from sodium and hydrogen; the right side counts negative charge from hydroxide, bicarbonate, and carbonate. If \(R_q > 0\), the trial state has too much positive charge or too little anion charge. If \(R_q < 0\), it has too much anion charge or too little positive charge.

GL-260 uses this residual as the solver objective. During the pH solve, the model changes \([H^+]\), recomputes \([\mathrm{OH^-}]\), carbonate fractions, and species concentrations, then evaluates \(R_q\). The accepted solution is the point where the residual is close enough to zero, \(|R_q| \le \epsilon_{\mathrm{charge}}\), where \(\epsilon_{\mathrm{charge}}\) is the solver tolerance. This matters operationally because the pH value is only useful if the accompanying carbonate distribution also conserves charge. A low residual means the displayed pH, bicarbonate fraction, carbonate fraction, hydroxide inventory, and sodium basis all describe the same feasible solution state.

<div class="inline-module-anchor" data-inline-module="charge-balance-visual"></div>

### 4.1 Deriving the Alpha Fractions From the Equilibrium Constants

The alpha fractions are not fitted fractions. They fall directly out of the carbonate acid equilibria once \([H^+]\) is known.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Alpha Fraction Derivation Map</p>
      <p class="calculation-map-copy">Express bicarbonate and carbonate relative to the carbonic-acid basis, substitute those ratios into total carbon, then recover the shared denominator.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Closure</span>
      <strong>\(\sum \alpha = 1\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. First dissociation</span>
      \[
      K_{a1} = \frac{[H^+] [\mathrm{HCO_3^-}]}{[\mathrm{CO_2^*}]}
      \]
      \[
      [\mathrm{HCO_3^-}] = \frac{K_{a1}}{[H^+]} [\mathrm{CO_2^*}]
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Second dissociation</span>
      \[
      K_{a2} = \frac{[H^+] [\mathrm{CO_3^{2-}}]}{[\mathrm{HCO_3^-}]}
      \]
      \[
      [\mathrm{CO_3^{2-}}] = \frac{K_{a2}}{[H^+]} [\mathrm{HCO_3^-}]
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Substitute bicarbonate ratio</span>
      \[
      [\mathrm{CO_3^{2-}}] = \frac{K_{a1}K_{a2}}{[H^+]^2} [\mathrm{CO_2^*}]
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Total carbon closure</span>
      \[
      C_T = [\mathrm{CO_2^*}] + [\mathrm{HCO_3^-}] + [\mathrm{CO_3^{2-}}]
      \]
      \[
      C_T = [\mathrm{CO_2^*}] \left(1 + \frac{K_{a1}}{[H^+]} + \frac{K_{a1}K_{a2}}{[H^+]^2}\right)
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>5. Shared denominator and fraction closure</span>
    \[
    D = [H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}
    \]
    \[
    \alpha_0 + \alpha_1 + \alpha_2 = 1
    \]
  </div>
</div>

The pH solver is therefore doing one central job: find the \([H^+]\) value where these fractions, hydroxide from \(K_w\), sodium charge, and total carbon all agree at the same time.

<div class="inline-module-anchor" data-inline-module="derivation-stepper"></div>

---

## 5) Why Bicarbonate Purity Is Hard and Why pCO2 Is the Control Lever

!!! note "Calculation Legend"
    - \(\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}}\): bicarbonate-to-carbonate activity ratio
    - \(a_{\mathrm{OH^-}}\): hydroxide activity
    - \(K_{a2}\), \(K_{w}\), \(K_{b2}\): equilibrium constants
    - \(p_{\mathrm{CO_2}}\): headspace \(CO_{2}\) partial pressure `[atm]`

At high alkalinity, carbonate is strongly favored unless dissolved \(CO_{2}\) is driven high enough to consume free hydroxide and shift the distribution back toward bicarbonate.

!!! info "Derivation Walkthrough"
    **Goal:** make the bicarbonate-to-carbonate ratio dependence explicit in terms of hydroxide activity and \(p_{\mathrm{CO_2}}\).

    **Step-by-step interpretation:** start with the second base equilibrium, rearrange into \(a_{\mathrm{HCO_3^-}}/a_{\mathrm{CO_3^{2-}}}\), then substitute Henry's law to connect dissolved \(CO_{2}\) directly to \(p_{\mathrm{CO_2}}\).

    **Why this changes operation:** increasing \(p_{\mathrm{CO_2}}\) is the practical purity lever because it promotes bicarbonate-forming chemistry and suppresses the over-conversion pathway that creates excess carbonate.

Using the same half-reaction constants:

<table class="reaction-map">
<thead>
<tr>
<th>Half Reaction</th>
<th>Equilibrium Expression</th>
</tr>
</thead>
<tbody>
<tr>
<td>\[\mathrm{CO_2^*} + \mathrm{OH^-} \rightleftharpoons \mathrm{HCO_3^-}\]</td>
<td>\[K_{b1} = \frac{K_{a1}}{K_w}\]</td>
</tr>
<tr>
<td>\[\mathrm{HCO_3^-} + \mathrm{OH^-} \rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O}\]</td>
<td>\[K_{b2} = \frac{K_{a2}}{K_w}\]</td>
</tr>
</tbody>
</table>

From the second equilibrium:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">pCO2 Purity Lever Map</p>
      <p class="calculation-map-copy">Rearrange the carbonate-forming equilibrium to show why lower hydroxide activity and higher dissolved CO2 favor bicarbonate.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Ratio</span>
      <strong>\(\mathrm{HCO_3^-}/\mathrm{CO_3^{2-}}\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Base-side ratio</span>
      \[
      \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}} = \frac{1}{K_{b2} \times a_{\mathrm{OH^-}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Acid/water constants</span>
      \[
      \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}} = \frac{K_w}{K_{a2} \times a_{\mathrm{OH^-}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Fixed-headspace boundary</span>
      \[
      [\mathrm{CO_2^*}] = K_H \times p_{\mathrm{CO_2}}
      \]
    </div>
  </div>
  <p class="calculation-map-callout">This ratio increases as \(a_{OH}\) drops. Increasing \(p_{CO_{2}}\) raises dissolved \(CO_{2}\), consumes alkalinity, lowers \(a_{OH}\), and therefore raises the bicarbonate-to-carbonate ratio.</p>
</div>

<div class="inline-module-anchor" data-inline-module="equilibrium-interplay"></div>

Under the locked walkthrough assumptions (25 C, 700 g NaOH, 2,200 mL water), a compact sensitivity sweep is:

| \(p_{CO_{2}}\) (atm) | pH | \(\mathrm{H_2CO_3^*}\) frac | \(\mathrm{HCO_3^-}\) frac | \(\mathrm{CO_3^2-}\) frac |
| --- | ---: | ---: | ---: | ---: |
| 0.10 | 10.25 | 0.0002 | 0.1820 | 0.8178 |
| 0.50 | 9.85 | 0.0008 | 0.4107 | 0.5885 |
| 1.00 | 9.45 | 0.0025 | 0.6928 | 0.3047 |
| 2.00 | 9.05 | 0.0086 | 0.8409 | 0.1505 |
| 4.00 | 8.65 | 0.0272 | 0.8952 | 0.0776 |

<div class="inline-chart-anchor" data-inline-chart="pco2-sensitivity"></div>

The trend is the key operational point: higher `pCO2` materially suppresses carbonate fraction and widens the bicarbonate-dominant operating window.

---

## 6) NaOH-CO2 Pitzer (HMW-Focused) Calculation Path

!!! note "Calculation Legend"
    - `I`: ionic strength [\(mol kg^{-1}\)]
    - \(m_{i}\), \(m_{j}\), \(m_{k}\): species molalities [\(mol kg^{-1}\)]
    - \(z_{i}\): ion charge number
    - \(\gamma_i\): activity coefficient
    - \(B_{ij}\), \(C_{ij}\), \(\Psi_{ijk}\), \(F(I)\), \(Z\): Pitzer-model terms used in the focused implementation
    - \(r_{1}\), \(r_{2}\), \(r_{3}\): dimensionless species ratio identities
    - \(m_{CT}\): total inorganic carbon molality [\(mol kg^{-1}\)]

The NaOH-focused Pitzer path adds activity corrections at high ionic strength while preserving charge and carbon closures each cycle.

The NaOH Pitzer path uses activity-corrected species balances and charge balance with focused Pitzer interactions (\(Na^+\) with \(OH^-\), \(CO_{3}^2^-\), \(CO_{3}^2^-\), plus selected \(\theta\)/\(\Psi\) terms).

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Focused Pitzer Solver Map</p>
      <p class="calculation-map-copy">Compute ionic strength, correct activities, use activity-corrected species ratios, then enforce total-carbon and charge closure each cycle.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Path</span>
      <strong>HMW</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Ionic strength</span>
      \[
      I = \frac{1}{2} \sum_i (m_i \times z_i^2)
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Activity coefficients</span>
      \[
      \ln(\gamma_i) = (z_i^2 \times F(I)) + \sum_j \left(m_j \times (2 \times B_{ij} + Z \times C_{ij})\right) + \sum_{j,k} \left(m_j \times m_k \times \Psi_{ijk}\right) + \cdots
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Bicarbonate ratio</span>
      \[
      r_1 = \frac{K_{a1}}{\gamma_{\mathrm{H^+}} \times \gamma_{\mathrm{HCO_3^-}} \times [H^+]}
      \]
      \[
      r_1 = \frac{m_{\mathrm{HCO_3^-}}}{m_{\mathrm{CO_2^*}}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Carbonate ratio</span>
      \[
      r_{23} = \frac{K_{a2} \times \gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}} \times \gamma_{\mathrm{CO_3^{2-}}} \times [H^+]}
      \]
      \[
      r_{23} = \frac{m_{\mathrm{CO_3^{2-}}}}{m_{\mathrm{HCO_3^-}}}
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>5. Total carbon closure</span>
    \[
    m_{CT} = m_{\mathrm{CO_2^*}} + m_{\mathrm{HCO_3^-}} + m_{\mathrm{CO_3^{2-}}}
    \]
  </div>
  <p class="calculation-map-callout">The charge-balance closure is then solved iteratively each cycle using the corrected activities.</p>
</div>

### 6.1 What HMW / PHREEQC-NaCO3 Pairing Means

!!! note "Calculation Legend"
    - `HMW`: Harvie-Moller-Weare Pitzer parameter family for concentrated electrolyte solutions.
    - `PHREEQC pitzer.dat`: database source for the Pitzer interaction parameters used by the focused GL-260 path.
    - `Na-CO3 pairing`: shorthand for explicitly correcting sodium interactions with carbonate-family ions.
    - \(B^0\), \(B^1\), \(C^0\): pair-interaction terms for a cation-anion pair.
    - \(Θ\), \(Ψ\): same-charge and ternary interaction terms that capture higher-order electrolyte behavior.

The phrase **HMW / PHREEQC-NaCO3 Pairing** means GL-260 is not just solving carbonate acid-base equations in isolation. It reads the focused Pitzer parameter set from `pitzer.dat` and applies the sodium-carbonate interaction terms that dominate this chemistry:

- \(Na^+\) with \(OH^-\)
- \(Na^+\) with \(HCO_{3}^-\)
- \(Na^+\) with \(CO_{3}^{2-}\)
- \(Θ_{\mathrm{CO_3^{2-},OH^-}}\)
- \(Ψ_{\mathrm{CO_3^{2-},Na^+,OH^-}}\)
- \(Ψ_{\mathrm{CO_3^{2-},OH^-,Na^+}}\)

The model converts these database terms into the compact parameters used by the Rust and Python solver cores:

```latex
\{B^0_{\mathrm{Na,OH}}, B^1_{\mathrm{Na,OH}}, C^0_{\mathrm{Na,OH}}, B^0_{\mathrm{Na,HCO_3}}, B^1_{\mathrm{Na,HCO_3}}, C^0_{\mathrm{Na,HCO_3}}, B^0_{\mathrm{Na,CO_3}}, B^1_{\mathrm{Na,CO_3}}, C^0_{\mathrm{Na,CO_3}}, \Theta_{\mathrm{CO_3,OH}}, \Psi_{\mathrm{CO_3,Na,OH}}, \Psi_{\mathrm{CO_3,HCO_3,Na}}\}
```

Operationally, this is more accurate for GL-260 than an ideal model because sodium carbonate and sodium bicarbonate are not passive spectators. Sodium association changes the effective activities of carbonate-family species, and those activity changes shift the pH and fraction crossover. That is the specific error mode the HMW path is meant to avoid: a misleading carbonate-buffer plateau or incorrect pH slope when the solution is highly loaded with sodium.

---

## 7) Reaction Kinetics and Uptake-Rate Interpretation
Equilibrium tells us where the chemistry can settle after a cycle. Kinetics explains how quickly the process moves toward that state while CO2 is being contacted with the alkaline liquid.

!!! note "Calculation Legend"
    - \(r_{\mathrm{CO_2}}\): volumetric CO2 absorption/reaction rate [\(mol L^{-1} s^{-1}\)] or model-consistent rate basis
    - \(k_La\): gas-liquid volumetric mass-transfer coefficient [\(s^{-1}\)]
    - \(C^*_{\mathrm{CO_2}}\): dissolved CO2 concentration at gas-liquid equilibrium [\(mol L^{-1}\)]
    - \(C_{\mathrm{CO_2}}\): bulk dissolved CO2 concentration [\(mol L^{-1}\)]
    - \(r_1\), \(r_2\): bicarbonate-forming and carbonate-forming reaction rates [\(mol L^{-1} s^{-1}\)]
    - \(k_1\), \(k_2\): effective kinetic rate constants on the selected concentration/activity basis
    - \(E\): enhancement factor showing how fast reaction increases apparent CO2 absorption
    - \(\tau_{\mathrm{mix}}\), \(\tau_{\mathrm{rxn}}\), \(\tau_{\mathrm{mt}}\): mixing, reaction, and mass-transfer time scales [seconds]

!!! info "Derivation Walkthrough"
    **Goal:** separate the thermodynamic endpoint from the rate path that gets the batch there.

    **Step-by-step interpretation:** write the two liquid reaction rates, connect them to the gas-liquid CO2 supply term, then compare characteristic time scales to decide whether the observed cycle is mass-transfer-limited, reaction-limited, or mixing-limited.

    **Why this changes operation:** equilibrium pH and speciation are the final state calculation, but cycle duration, pressure-decay shape, and heat release depend on kinetics; a batch can have the right endpoint target while still being operated too quickly or unevenly to reach it cleanly.

The same carbonate chemistry discussed earlier can be read as a hydrated carbonic-acid pool followed by two forward base-consumption steps when CO2 enters caustic solution. In this walkthrough, \(\mathrm{CO_2^*}\) means the model's dissolved carbonic-acid basis: dissolved molecular \(\mathrm{CO_2(aq)}\) plus hydrated \(\mathrm{H_2CO_3}\). In highly basic solution that pool is rapidly consumed by hydroxide, so the kinetic shorthand often combines hydration and bicarbonate formation into one apparent fast step.

<table class="reaction-map">
<thead>
<tr>
<th>Kinetic Step</th>
<th>Rate Expression / Interpretation</th>
</tr>
</thead>
<tbody>
<tr>
<td>\[\mathrm{CO_2(aq)} + \mathrm{H_2O} \rightleftharpoons \mathrm{H_2CO_3}\]</td>
<td>\[\mathrm{CO_2^*} \equiv \mathrm{CO_2(aq)} + \mathrm{H_2CO_3}\]<br>Hydration creates the carbonic-acid basis used by the equilibrium and kinetics notation.</td>
</tr>
<tr>
<td>\[\mathrm{CO_2^*} + \mathrm{OH^-} \rightarrow \mathrm{HCO_3^-}\]</td>
<td>\[r_1 = k_1 \times a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}\]<br>Apparent fast bicarbonate-forming step: hydrated carbonic-acid basis is pulled toward bicarbonate by free hydroxide.</td>
</tr>
<tr>
<td>\[\mathrm{HCO_3^-} + \mathrm{OH^-} \rightarrow \mathrm{CO_3^{2-}} + \mathrm{H_2O}\]</td>
<td>\[r_2 = k_2 \times a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}\]<br>Over-conversion step that is favored while hydroxide activity remains high.</td>
</tr>
<tr>
<td>\[\mathrm{CO_3^{2-}} + \mathrm{H^+} \rightleftharpoons \mathrm{HCO_3^-}\]</td>
<td>\[\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}} = \frac{a_{\mathrm{H^+}}}{K_{a2}}\]<br>Carbonate is converted back to bicarbonate when additional dissolved CO2 lowers pH and increases proton availability.</td>
</tr>
<tr>
<td>\[\mathrm{CO_3^{2-}} + \mathrm{H_2CO_3} \rightleftharpoons 2\mathrm{HCO_3^-}\]</td>
<td>\[\mathrm{CO_3^{2-}} + \mathrm{CO_2(aq)} + \mathrm{H_2O} \rightleftharpoons 2\mathrm{HCO_3^-}\]<br>Net CO2-driven bicarbonate formation: carbonic-acid basis supplies the proton demand that pulls carbonate back toward bicarbonate.</td>
</tr>
</tbody>
</table>

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Liquid-Phase Kinetic Balance Map</p>
      <p class="calculation-map-copy">Track how gas-liquid supply, bicarbonate formation, carbonate formation, and hydroxide consumption move during a cycle.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Rates</span>
      <strong>\(r_1,r_2\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Dissolved CO2 pool</span>
      \[
      \frac{dC_{\mathrm{CO_2}}}{dt}
      =
      k_La \times \left(C^*_{\mathrm{CO_2}} - C_{\mathrm{CO_2}}\right)
      - r_1
      \]
    </div>
    <div class="calculation-map-step">
      <span>Bicarbonate pool</span>
      \[
      \frac{dC_{\mathrm{HCO_3^-}}}{dt}
      =
      r_1 - r_2
      \]
    </div>
    <div class="calculation-map-step">
      <span>Carbonate pool</span>
      \[
      \frac{dC_{\mathrm{CO_3^{2-}}}}{dt}
      =
      r_2
      \]
    </div>
    <div class="calculation-map-step">
      <span>Hydroxide pool</span>
      \[
      \frac{dC_{\mathrm{OH^-}}}{dt}
      =
      -r_1 - r_2
      \]
    </div>
  </div>
</div>

These balances describe a moving cycle, not the final equilibrium solve. CO2 must first cross from gas to liquid, hydrate into the \(\mathrm{CO_2^*}\) carbonic-acid basis, react in the liquid, and then mix through the batch. GL-260's equilibrium model consumes the cycle-level uptake after the event has been identified; the kinetic interpretation explains the pressure and temperature shape during the event.

### 7.1 Gas-Liquid Supply Term

The physical supply of dissolved CO2 is controlled by the driving force between the gas-equilibrium concentration and the current bulk concentration:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Gas-Liquid Supply Map</p>
      <p class="calculation-map-copy">Translate headspace CO2 pressure into dissolved CO2 driving force, then into an effective absorption rate.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Lever</span>
      <strong>\(p_{CO_2}\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Transfer driving force</span>
      \[
      N_{\mathrm{CO_2}} = k_La \times \left(C^*_{\mathrm{CO_2}} - C_{\mathrm{CO_2}}\right)
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Henry boundary</span>
      \[
      C^*_{\mathrm{CO_2}} \approx K_H \times p_{\mathrm{CO_2}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Pressure-explicit supply</span>
      \[
      N_{\mathrm{CO_2}} = k_La \times \left(K_H \times p_{\mathrm{CO_2}} - C_{\mathrm{CO_2}}\right)
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Fast-reaction limit</span>
      \[
      C_{\mathrm{CO_2}} \rightarrow 0
      \]
      \[
      N_{\mathrm{CO_2}} \approx k_La \times K_H \times p_{\mathrm{CO_2}}
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>5. Absorption enhancement</span>
    \[
    N_{\mathrm{CO_2,eff}} = E \times k_La \times \left(C^*_{\mathrm{CO_2}} - C_{\mathrm{CO_2}}\right)
    \]
  </div>
</div>

This equation is the kinetic version of the pCO2 control lever. Higher \(p_{\mathrm{CO_2}}\) does not only shift the equilibrium distribution toward bicarbonate; it also raises the instantaneous driving force for absorption. Better agitation, gas dispersion, and interfacial contact increase \(k_La\), which lets the same headspace pressure produce faster usable CO2 transfer.

where \(E > 1\) means the liquid reaction is consuming dissolved CO2 fast enough to increase the apparent absorption rate.

That is the mass-transfer-limited regime: the chemistry is ready to react, but the gas-liquid interface controls how quickly carbon can enter the solution.

### 7.2 Pseudo-First-Order View at High Hydroxide

During early caustic-rich cycles, hydroxide is abundant compared with dissolved CO2. Over a short interval, \(a_{\mathrm{OH^-}}\) can be treated as locally high and slowly varying, which collapses the first rate expression into a pseudo-first-order form:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Pseudo-First-Order Rate Map</p>
      <p class="calculation-map-copy">Fold the high, slowly varying hydroxide activity into an apparent rate constant for early caustic-rich cycles.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Early run</span>
      <strong>\(k'_1\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Original rate</span>
      \[
      r_1 = k_1 \times a_{\mathrm{OH^-}} \times a_{\mathrm{CO_2^*}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Apparent constant</span>
      \[
      k'_1 = k_1 \times a_{\mathrm{OH^-}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Simplified rate</span>
      \[
      r_1 = k'_1 \times a_{\mathrm{CO_2^*}}
      \]
    </div>
  </div>
</div>

The interpretation is direct: early in the run, high hydroxide activity makes CO2 consumption very fast, so pressure can fall sharply after a charge. As hydroxide is consumed, \(k'_1\) falls, pressure decay slows, and the batch becomes less able to instantly pull CO2 out of the headspace.

This same logic explains the carbonate-rich middle region. If hydroxide remains high while bicarbonate has already been formed, the second step \(r_2 = k_2 \times a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}\) can keep running. Lowering \(a_{\mathrm{OH^-}}\) through additional CO2 loading suppresses \(r_2\), which is why the process eventually moves away from carbonate dominance and toward the bicarbonate-rich endpoint.

### 7.3 Time-Scale Test for Interpreting Cycle Shape

For operations, the useful question is which time scale is slowest:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Cycle Shape Time-Scale Map</p>
      <p class="calculation-map-copy">Compare reaction, mass-transfer, and mixing time scales to decide what controls the pressure-decay shape.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Question</span>
      <strong>slowest?</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Reaction time</span>
      \[
      \tau_{\mathrm{rxn}} \sim \frac{1}{k'_1}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Mass-transfer time</span>
      \[
      \tau_{\mathrm{mt}} \sim \frac{1}{k_La}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Mixing time</span>
      \[
      \tau_{\mathrm{mix}} = \text{time required to distribute CO2 and heat through the liquid}
      \]
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Mass-transfer limited</span>
      \[
      \tau_{\mathrm{rxn}} \ll \tau_{\mathrm{mt}}
      \]
      <p>Reaction is fast; pressure falls as quickly as CO2 crosses the interface.</p>
    </div>
    <div class="calculation-map-step">
      <span>Reaction limited</span>
      \[
      \tau_{\mathrm{mt}} \ll \tau_{\mathrm{rxn}}
      \]
      <p>Transfer is not the bottleneck; liquid chemistry controls consumption.</p>
    </div>
    <div class="calculation-map-step">
      <span>Mixing affected</span>
      \[
      \tau_{\mathrm{mix}} \gtrsim \tau_{\mathrm{rxn}}
      \]
      <p>Local high-pH pockets can temporarily overproduce carbonate before homogenization.</p>
    </div>
  </div>
</div>

### 7.4 How This Connects to GL-260 Cycle Detection

GL-260 does not need to solve a full kinetic ODE model to use kinetics operationally. The detected cycle provides an integrated uptake event, and the equilibrium solver uses that event as the carbon-loading increment:

<div class="calculation-map">
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Detected cycle event</span>
      \[
      \Delta n_{\mathrm{CO_2},i}
      =
      \int_{t_{i,start}}^{t_{i,end}} N_{\mathrm{CO_2}}(t)\ dt
      \]
    </div>
    <div class="calculation-map-step">
      <span>Cumulative loading input</span>
      \[
      m_{\mathrm{CO_2,cum},k}
      =
      \sum_{i=1}^{k} \Delta m_{\mathrm{CO_2},i}
      \]
    </div>
  </div>
</div>

Kinetics still matters because it explains whether the integrated event is trustworthy and complete. A sharp pressure drop followed by a stable tail suggests the cycle may have approached its local endpoint. A slow decay, reheating, or unstable derivative can indicate that transfer, reaction, or mixing was still active when the event boundary was chosen.

For presentation purposes, the clean separation is:

- **Kinetics:** how quickly CO2 is absorbed and reacted during a cycle.
- **Equilibrium:** what pH and speciation the batch reaches after that uptake is accepted.
- **Calibration:** how measured pH anchors correct the cycle trajectory when the real process differs from the modeled ideal.

---

## 8) Cycle Uptake Math
Cycle-level uptake is converted into cumulative carbon loading, which becomes the cycle-by-cycle driver of equilibrium state updates.

!!! info "Derivation Walkthrough"
    **Goal:** convert per-cycle CO2 mass events into cumulative loading terms used by the equilibrium solver.

    **Step-by-step interpretation:** define cycle delta mass, accumulate to cumulative mass, then convert cumulative mass to molality (\(m_{CT,k}\)) using molecular weight and water basis.

    **Why this changes operation:** this conversion maps real cycle operation to carbonate chemistry state, so accurate loading is required to keep the process in the bicarbonate-dominant region needed for purer NaHCO3.

### 8.1 Primary (Locked) Synthetic Cycle Uptake Sequence

!!! note "Calculation Legend"
    - \(\Delta m_{\mathrm{CO_2},i}\): CO2 mass uptake during cycle `i` [`g`]
    - \(m_{\mathrm{CO_2,cum},k}\): cumulative CO2 mass through cycle `k` [`g`]
    - \(MW_{\mathrm{CO_2}}\): CO2 molecular weight [\(g mol^{-1}\)]
    - \(m_{CT,k}\): total inorganic carbon molality at cycle `k` [\(mol kg^{-1}\)]
    - \(kg_{\mathrm{water}}\): water mass basis [`kg`]

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Synthetic Cycle Loading Map</p>
      <p class="calculation-map-copy">Convert the locked per-cycle mass sequence into cumulative carbon loading for the equilibrium solver.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Total</span>
      <strong>900 g</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Cycle deltas</span>
      \[
      \Delta m_{\mathrm{CO_2},i}\ (\mathrm{g}) = [80,90,100,110,120,130,130,140]
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Cumulative mass</span>
      \[
      m_{\mathrm{CO_2,cum},k} = \sum_{i=1}^{k} \Delta m_{\mathrm{CO_2},i}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Total carbon molality</span>
      \[
      m_{CT,k} = \frac{\left(m_{\mathrm{CO_2,cum},k} / MW_{\mathrm{CO_2}}\right)}{kg_{\mathrm{water}}}
      \]
    </div>
  </div>
</div>

<div class="inline-chart-anchor" data-inline-chart="uptake-loading"></div>


### 8.2 Operational Reference: Pressure-Derived Uptake

!!! note "Calculation Legend"
    - \(\Delta P_{\mathrm{psi}}\), \(\Delta P_{\mathrm{atm}}\): pressure drop per cycle [`psi`, `atm`]
    - \(V_{\mathrm{headspace}}\): headspace volume [`L`]
    - `R`: ideal gas constant [\(L atm mol^{-1} K^{-1}\)]
    - `T`: absolute temperature [`K`]
    - \(n_{\mathrm{CO_2},i}\): inferred moles of CO2 transferred in cycle `i` [`mol`]


When uptake is inferred from pressure-drop per cycle:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Pressure-Derived Uptake Map</p>
      <p class="calculation-map-copy">Convert pressure drop into moles of CO2 transferred, then into per-cycle mass uptake.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Example</span>
      <strong>45.90 g</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Convert pressure</span>
      \[
      \Delta P_{\mathrm{atm}} = \frac{\Delta P_{\mathrm{psi}}}{14.6959}
      \]
      \[
      \Delta P_{\mathrm{atm}} = \frac{25\ \mathrm{psi}}{14.6959\ \mathrm{psi\ atm^{-1}}} = 1.7012\ \mathrm{atm}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Infer moles</span>
      \[
      n_{\mathrm{CO_2},i} = \frac{\Delta P_{\mathrm{atm}} \times V_{\mathrm{headspace}}}{R \times T}
      \]
      \[
      n_{\mathrm{CO_2},i} = \frac{1.7012\ \mathrm{atm} \times 15\ \mathrm{L}}{0.082057\ \mathrm{L\ atm\ mol^{-1}\ K^{-1}} \times 298.15\ \mathrm{K}} = 1.0430\ \mathrm{mol}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Convert to mass</span>
      \[
      \Delta m_{\mathrm{CO_2},i} = n_{\mathrm{CO_2},i} \times MW_{\mathrm{CO_2}}
      \]
      \[
      \Delta m_{\mathrm{CO_2},i} = 1.0430\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} = 45.90\ \mathrm{g}
      \]
    </div>
  </div>
</div>

<div class="inline-module-anchor" data-inline-module="cycle-flow-visual"></div>

---

## 9) Worked NaOH-Pitzer Simulation Table (Synthetic Cycles to 900 g)

!!! note "Calculation Legend"
    - `CT`: total inorganic carbon molality [\(mol kg^{-1}\)]
    - `m_OH`: hydroxide molality [\(mol kg^{-1}\)]
    - `H2CO3* frac`, `HCO3- frac`, \(CO3^2- frac\): species fractions `[-]`

The worked table is the concrete numerical bridge between theory and the dashboard-facing channels used in the app.

!!! info "Derivation Walkthrough"
    **Goal:** show where the cycle trajectory moves from caustic/carbonate-dominant behavior into bicarbonate-dominant behavior.

    **Step-by-step interpretation:** track cumulative loading, pH decline, hydroxide depletion, and fraction crossover together across cycles.

    **Why this changes operation:** this table is the operating map for bicarbonate purity because it identifies when control levers have reduced residual alkalinity enough to hold most carbon as \(\mathrm{HCO_3^-}\).

Computed with the same NaOH-CO2 Pitzer core pathway used by the app example model file.

| Cycle | Delta CO2 (g) | Cum CO2 (g) | CT (mol/kg) | pH | m_OH (mol/kg) | H2CO3* frac | HCO3- frac | CO3^2- frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0.0000 | 15.2672 | 7.9545 | 0.0000 | 0.0000 | 0.0000 |
| 1 | 80 | 80 | 0.8263 | 15.1608 | 6.3020 | 0.0000 | 0.0000 | 1.0000 |
| 2 | 90 | 170 | 1.7558 | 15.0093 | 4.4429 | 0.0000 | 0.0000 | 1.0000 |
| 3 | 100 | 270 | 2.7886 | 14.7436 | 2.3773 | 0.0000 | 0.0000 | 1.0000 |
| 4 | 110 | 380 | 3.9247 | 13.4003 | 0.1051 | 0.0000 | 0.0000 | 1.0000 |
| 5 | 120 | 500 | 5.1641 | 9.6257 | 0.000018 | 0.0000 | 0.4596 | 0.5404 |
| 6 | 130 | 630 | 6.5068 | 9.2061 | 0.000007 | 0.0002 | 0.7771 | 0.2227 |
| 7 | 130 | 760 | 7.8495 | 8.2255 | 0.000001 | 0.0028 | 0.9810 | 0.0162 |
| 8 | 140 | 900 | 9.2954 | 7.8538 | 0.000000 | 0.0066 | 0.9867 | 0.0066 |

<div class="inline-chart-anchor" data-inline-chart="cycle-trend-highlights"></div>

Interpretation:

- Around `~385 g` cumulative CO2, the system approaches Stage-1 equivalence (NaOH mostly consumed).
- By late cycles, bicarbonate dominates and pH approaches the bicarbonate-buffer region.

## 10) Worked Real-World Example: PR-24304 Sodium Bicarbonate Batch 1

This section connects the derivation to a real GL-260 presentation artifact rather than the locked synthetic cycle sequence.

### 10.1 Profile Basis and Stoichiometric Translation

!!! note "Calculation Legend"
    - `profile`: saved GL-260 analysis configuration used to reproduce plotting and reaction-basis context.
    - \(m_{\mathrm{NaOH,profile}}\): NaOH charge from the profile [`g`]
    - \(n_{\mathrm{NaOH,profile}}\): NaOH moles implied by the profile [`mol`]
    - \(m_{\mathrm{CO_2,stoich}}\): CO2 mass required for the ideal one-to-one NaOH-to-NaHCO3 endpoint [`g`]

The selected profile is:

```text
profiles/PR-24304 CLM-441-MPT Sodium Bicarbonate Batch 1 of 2.json
```

Its reaction basis is `NaOH + CO2 -> NaHCO3` with `702.0 g` sodium hydroxide starting mass.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">PR-24304 Stoichiometry Map</p>
      <p class="calculation-map-copy">Convert the saved profile NaOH charge into the ideal CO2 requirement for the bicarbonate endpoint.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Target</span>
      <strong>772.4 g</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Profile charge</span>
      \[
      m_{\mathrm{NaOH,profile}} = 702.0\ \mathrm{g}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. NaOH moles</span>
      \[
      n_{\mathrm{NaOH,profile}} = \frac{702.0\ \mathrm{g}}{40.0\ \mathrm{g\ mol^{-1}}} = 17.55\ \mathrm{mol}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Ideal CO2 endpoint</span>
      \[
      n_{\mathrm{CO_2,stoich}} = n_{\mathrm{NaOH,profile}} = 17.55\ \mathrm{mol}
      \]
      \[
      m_{\mathrm{CO_2,stoich}} = 17.55\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 772.4\ \mathrm{g}
      \]
    </div>
  </div>
</div>

This number is a presentation anchor: it is the ideal CO2 requirement for complete conversion to sodium bicarbonate before yield losses, gas holdup uncertainty, incomplete absorption, or measurement corrections are considered.

### 10.2 Reading the Combined Triple-Axis Plot

![PR-24304 Batch 1 Day 1-6 combined triple-axis plot](assets/equilibrium-walkthrough/pr-24304-batch-1-day-1-6-combined-triple-axis.png)

The combined triple-axis plot is the process-history view. During a live explanation, read it from left to right as the experimental record:

- Reactor pressure shows each CO2 contact/reaction event.
- The pressure derivative highlights where pressure is changing fastest, which helps identify uptake windows and cycle boundaries.
- Reactor/manifold temperature traces show whether thermal behavior could be influencing pressure, rate, or inferred gas uptake.

The equilibrium math does not replace this plot. The plot tells GL-260 where the physical events are; the equilibrium model interprets what those events imply for pH and carbonate speciation.

### 10.3 Reading the Speciation Timeline Plot

![PR-24304 Batch 1 Day 1-6 cycle speciation timeline](assets/equilibrium-walkthrough/pr-24304-batch-1-cycle-speciation-timeline-day-1-6.png)

The speciation timeline maps detected cycle progression and estimated CO2 loading into sodium-basis species fractions:

- `NaOH %` indicates remaining caustic character.
- `Na2CO3 %` indicates carbonate-rich intermediate behavior.
- `NaHCO3 %` indicates the desired bicarbonate-forming endpoint.
- Measured pH anchors, when present, correct the estimated pH and speciation path rather than being treated as separate annotations.

Early in the run, high hydroxide activity drives carbonate formation. 
As CO2 loading increases and hydroxide is consumed, the system moves through the carbonate-rich region and toward bicarbonate dominance. 
The HMW Pitzer model makes that crossover more realistic by correcting sodium-carbonate activities in the concentrated electrolyte regime.

### 10.4 How To Narrate the Real-Data Chain

Use this sequence when presenting the PR-24304 example:

1. Start with the saved profile basis: `702.0 g NaOH`, product `NaHCO3`, and one-to-one CO2 stoichiometry.
2. Use the combined triple-axis plot to identify where pressure events and thermal context define the cycle timeline.
3. Convert cycle events into cumulative CO2 loading and compare the trajectory against the approximate `772.4 g CO2` stoichiometric endpoint.
4. Use the Pitzer speciation timeline to explain whether the run is still caustic/carbonate-rich or moving into bicarbonate dominance.
5. If measured pH anchors exist for the run, explain that GL-260 uses them to bend the prediction path toward observed chemistry while preserving charge/speciation consistency.

Peak/trough markers define cycle events, stoichiometry defines the target, Pitzer speciation explains the chemical state, and anchors improve the run-specific pH trajectory.

---

## 11) Measured-pH Calibration + Hybrid ML Correction (Analysis Mode)
Measured anchors reshape the baseline simulation, and ML residual correction is only accepted when anchor quality is preserved.

!!! info "Derivation Walkthrough"
    **Goal:** combine anchor-grounded correction with optional ML residual learning without degrading anchor quality.

    **Step-by-step interpretation:** compute anchor residuals, optimize baseline piecewise objective, fit ridge residual model on normalized features, then apply fail-closed anchor checks.

    **Why this changes operation:** the hybrid path improves predictions without sacrificing bicarbonate-control trust; if anchor fidelity degrades, fail-closed fallback prevents purity decisions from being driven by unstable corrections.

### 11.1 Locked Multi-Anchor Example

!!! note "Calculation Legend"
    - `r_5`, `r_9`: anchor residuals (`measured - baseline`) in pH units


- Anchor A: cycle 5 measured pH = `9.74`
- Anchor B: cycle 9 measured pH = `9.34`

Baseline model at those cycles from the selected-profile pre-calibration run:

- Cycle 5 baseline pH = `9.1483`
- Cycle 9 baseline pH = `8.7016`

Anchor residuals (`measured - baseline`):

<div class="calculation-map">
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Cycle 5 residual</span>
      \[
      r_{5} = 9.74 - 9.1483 = +0.5917\ \mathrm{pH}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Cycle 9 residual</span>
      \[
      r_{9} = 9.34 - 8.7016 = +0.6384\ \mathrm{pH}
      \]
    </div>
  </div>
</div>

<div class="inline-chart-anchor" data-inline-chart="anchor-residuals"></div>


### 11.2 Baseline Piecewise Calibration Objective

!!! note "Calculation Legend"
    - `J(s)`: objective value used to score scale factor `s` `[-]`
    - \(\hat pH_{\mathrm{anchor}}(s)\): model-predicted pH at an anchor after scale `s`
    - \(pH_{\mathrm{measured}}\): measured anchor pH
    - \(\lambda_{\mathrm{reg}}\), \(\lambda_{\mathrm{smooth}}\), \(w_{\mathrm{term}}\): penalty weights `[-]`
    - \(\Pi_{\mathrm{terminal}}\): terminal-band penalty function `[-]`
    - \(s_{\mathrm{prev}}\): previous segment scale value `[-]`


Per-anchor segment scale search minimizes:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Piecewise Calibration Objective Map</p>
      <p class="calculation-map-copy">Start with anchor fit error, then add regularization, segment smoothness, and terminal-window guidance.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Search</span>
      <strong>\(J(s)\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Anchor fit</span>
      \[
      J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Regularized scale</span>
      \[
      J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Smooth segment transitions</span>
      \[
      J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2 + \lambda_{\mathrm{smooth}} \times (s - s_{\mathrm{prev}})^2
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Terminal band penalty</span>
      \[
      J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2 + \lambda_{\mathrm{smooth}} \times (s - s_{\mathrm{prev}})^2 + w_{\mathrm{term}} \times \Pi_{\mathrm{terminal}}(pH_{\mathrm{end}}(s))
      \]
    </div>
  </div>
  <div class="calculation-map-grid four-up">
    <div class="calculation-map-step">
      <span>Regularization</span>
      \[
      \lambda_{\mathrm{reg}} = 0.02
      \]
    </div>
    <div class="calculation-map-step">
      <span>Smoothness</span>
      \[
      \lambda_{\mathrm{smooth}} = 0.01
      \]
    </div>
    <div class="calculation-map-step">
      <span>Terminal band</span>
      \[
      pH_{\mathrm{terminal\ band}} = [8.0,\ 8.3]
      \]
    </div>
    <div class="calculation-map-step">
      <span>Terminal weight</span>
      \[
      w_{\mathrm{term}} = 1.0
      \]
    </div>
  </div>
</div>

This stage outputs:

- corrected cycle uptake series,
- corrected cumulative uptake series,
- corrected pH series,
- corrected fractions series.

### 11.3 Historical Anchors and Cross-Run Learning

!!! note "Calculation Legend"
    - `manual anchor`: measured pH entered for the current run/profile.
    - `global inherited anchor`: compatible measured pH anchor learned from a previous run.
    - `history row`: prior calibrated cycle-factor curve used as a soft prior for future calibration.
    - `compatibility gate`: rule that prevents chemically dissimilar runs from influencing the current prediction.

GL-260 does not treat each run as isolated when anchor learning is enabled. After a successful Analysis calibration, it stores two kinds of information:

- a global measured-pH anchor library,
- a global anchor-learning history of calibrated cycle-factor series.

On a later run, the prediction engine resolves anchors in this order:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Historical Anchor Compatibility Map</p>
      <p class="calculation-map-copy">Use current manual anchors first, then only inherit compatible historical anchors when chemistry gates pass.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Guard</span>
      <strong>strict</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Anchor precedence</span>
      \[
      \text{current manual anchors} \rightarrow \text{compatible global inherited anchors}
      \]
    </div>
    <div class="calculation-map-step">
      <span>NaOH similarity</span>
      \[
      \frac{|C_{\mathrm{NaOH,current}} - C_{\mathrm{NaOH,history}}|}{C_{\mathrm{NaOH,current}}} \le 0.25
      \]
    </div>
    <div class="calculation-map-step">
      <span>Temperature proximity</span>
      \[
      |T_{\mathrm{current}} - T_{\mathrm{history}}| \le \Delta T_{\mathrm{max}}
      \]
    </div>
  </div>
</div>

The exact temperature tolerance is controlled by the application constant, but the intent is simple: history helps only when the chemistry is close enough to be meaningful.

Historical cycle-factor curves are combined into a bounded prior, \(s_{\mathrm{prior},k} = \mathrm{mean}(s_{\mathrm{history},k})\), for cycle `k` where compatible samples exist. The calibration optimizer can then use that prior to start closer to the behavior previously observed for similar NaOH/CO2 runs.

### 11.4 Why Prediction Accuracy Improves Every Run

Each new measured pH anchor supplies a direct observation of the real batch state. The baseline Pitzer model predicts the chemistry from stoichiometry, gas uptake, and activity corrections; the anchor tells the app how the real process deviated from that baseline.

For one anchor, \(r_k = pH_{\mathrm{measured},k} - pH_{\mathrm{baseline},k}\).

For many anchors across many compatible runs, GL-260 learns repeated residual patterns:

- consistent under-prediction or over-prediction near a cycle region,
- profile-specific uptake scaling behavior,
- terminal pH behavior near the target window,
- systematic differences between charged CO2 and actually absorbed CO2.

The result is not an uncontrolled drift. The app applies guardrails:

- current manual anchors remain highest priority,
- incompatible history is ignored,
- corrected pH is constrained to physically reasonable cycle progression,
- ML correction is rejected if anchor error worsens,
- anchor cycles must stay within the configured pH tolerance.

That is why the presentation can frame historical anchors as accuracy improvement rather than curve-fitting: every accepted correction must preserve observed anchor fidelity and remain consistent with the carbonate equilibrium framework.

### 11.5 Residual ML Ridge Correction Stage

!!! note "Calculation Legend"
    - \(\mathbf{x}\): raw feature vector for one cycle
    - \(\boldsymbol\mu\), \(\boldsymbol\sigma\): feature means and standard deviations
    - \(\mathbf{x}'\): normalized feature vector `[-]`
    - `X'`: normalized design matrix
    - \(\mathbf{y}\): residual target vector (anchor-informed) in pH units
    - \(\boldsymbol\beta\), \(\beta_0\): ridge regression coefficients/intercept
    - \(\hat r\): predicted residual correction in pH units


After baseline anchor calibration, Analysis can learn residual structure using the feature vector:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Residual ML Correction Map</p>
      <p class="calculation-map-copy">Build normalized cycle features, fit a ridge residual model, predict residual correction, then clamp corrected pH.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Ridge</span>
      <strong>\(\lambda=0.35\)</strong>
    </div>
  </div>
  <div class="calculation-map-step">
    <span>1. Feature vector</span>
    \[
    \mathbf{x} = [
    \text{cycle\_index},
    \text{cycle\_ratio},
    \text{baseline\_corrected\_ph},
    \text{cycle\_uptake\_mol},
    \text{cumulative\_uptake\_mol},
    \text{anchor\_distance},
    \text{naoh\_concentration\_mol\_l},
    \text{temperature\_c}
    ]
    \]
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>2. Normalize features</span>
      \[
      \mathbf{x}' = \frac{\mathbf{x} - \boldsymbol\mu}{\boldsymbol\sigma}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Ridge fit</span>
      \[
      \boldsymbol\beta = \left((X'^T \cdot X') + (\lambda \times I)\right)^{-1} \cdot X'^T \cdot \mathbf{y}
      \]
      \[
      \lambda = 0.35
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Predict residual</span>
      \[
      \hat r = \beta_0 + (\mathbf{x}' \cdot \boldsymbol\beta)
      \]
    </div>
    <div class="calculation-map-step">
      <span>5. Correct pH</span>
      \[
      pH_{\mathrm{ML\ corrected}} = \mathrm{clamp}(pH_{\mathrm{baseline\ corrected}} + \hat r,\ 0,\ 14)
      \]
    </div>
  </div>
</div>

Fractions are then recomputed from corrected pH using equilibrium-consistent fallback mapping.

### 11.6 Fail-Closed Anchor Guard (Apply/Reject Logic)

!!! note "Calculation Legend"
    - \(\mathrm{MAE}_{\mathrm{ML,anchors}}\), \(\mathrm{MAE}_{\mathrm{baseline,anchors}}\): anchor MAE values in pH units
    - `0.10`: default per-anchor absolute error tolerance in pH units


ML-corrected pH is applied only if anchor quality is not degraded:

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Fail-Closed Anchor Guard Map</p>
      <p class="calculation-map-copy">Promote ML correction only when aggregate anchor error does not worsen and every anchor remains within tolerance.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Default</span>
      <strong>0.10 pH</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>Aggregate anchor quality</span>
      \[
      \mathrm{MAE}_{\mathrm{ML,anchors}} \le \mathrm{MAE}_{\mathrm{baseline,anchors}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>Per-anchor tolerance</span>
      \[
      |pH_{\mathrm{ML,anchor}} - pH_{\mathrm{measured,anchor}}| \le 0.10
      \]
    </div>
  </div>
  <p class="calculation-map-callout">If either check fails, runtime status is fail-closed to the baseline corrected series.</p>
</div>

---

## 12) How Dashboard Values Are Computed
Dashboard metrics follow strict precedence and clamp logic so operator-facing status remains consistent with analysis outputs.

!!! info "Derivation Walkthrough"
    **Goal:** make dashboard KPIs deterministic by strict precedence, gap math, and clamped completion.

    **Step-by-step interpretation:** resolve required CO2 source by precedence, compute target gap, then compute baseline/corrected completion percentages with guardrail clamps.

    **Why this changes operation:** operators receive consistent status semantics even when multiple modeling channels are present.

### 12.1 Required CO2 Source Precedence

!!! note "Calculation Legend"
    - Arrow direction indicates strict precedence order for the required CO2 source channel.

<div class="calculation-map">
  <div class="calculation-map-step">
    <span>Required CO2 source precedence</span>
    \[
    \text{guidance\_model} \rightarrow \text{measured\_ph\_calibration} \rightarrow \text{planning\_reference}
    \]
  </div>
</div>

### 12.2 Target Gap and Completion

!!! note "Calculation Legend"
    - \(m_{\mathrm{required}}\): required CO2 mass target [`g`]
    - \(m_{\mathrm{uptake}}\): currently achieved CO2 uptake [`g`]
    - \(\Delta m_{\mathrm{target}}\): remaining CO2 mass target gap [`g`]
    - \(C_{\mathrm{required}}\), \(C_{\mathrm{corr}}\): completion percentage [%]
    - \(m_{\mathrm{corrected\ uptake}}\): corrected uptake basis [`g`]
    - \(m_{\mathrm{planning\ reference}}\): planning reference uptake basis [`g`]

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Dashboard KPI Calculation Map</p>
      <p class="calculation-map-copy">Compute remaining CO2 gap and completion percentages with clamp logic so displayed values stay bounded.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Range</span>
      <strong>0-100%</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>Target gap</span>
      \[
      \Delta m_{\mathrm{target}} = \max(m_{\mathrm{required}} - m_{\mathrm{uptake}}, 0)
      \]
    </div>
    <div class="calculation-map-step">
      <span>Required completion</span>
      \[
      C_{\mathrm{required}} = \mathrm{clamp}\left(\frac{m_{\mathrm{uptake}}}{m_{\mathrm{required}}}, 0, 1\right)\times 100
      \]
    </div>
    <div class="calculation-map-step">
      <span>Corrected planning completion</span>
      \[
      C_{\mathrm{corr}} = \mathrm{clamp}\left(\frac{m_{\mathrm{corrected\ uptake}}}{m_{\mathrm{planning\ reference}}}, 0, 1\right)\times 100
      \]
    </div>
  </div>
</div>

### 12.3 Corrected vs Baseline pH Channels

- Baseline calculated/equilibrium pH channel remains available.
- Corrected channel is produced by measured-anchor calibration.
- ML-corrected channel is additive and only promoted when anchor guard passes.

---

## 13) Presenter Navigation and Reproducibility Notes
The artifact is fully regenerable from this markdown source with deterministic build and check commands.

For live presentation, the generated HTML includes:

- a sticky Previous/Next control bar,
- a searchable presentation rail,
- a section jump selector,
- keyboard navigation with arrow keys, Page Up/Page Down, Home, and End,
- slide mode,
- motion toggle,
- auto-advance timing,
- print/PDF export.

The recommended flow is:

1. Use **Start Walkthrough** to begin with the locked basis setup before moving into the derivation.
2. Use the section selector to jump directly to **Worked Real-World Example** when moving from theory to PR-24304 data.
3. Use **Slide Mode** for large-room presentation.
4. Use **Print/PDF** when a static handout is needed.

To regenerate the HTML presentation artifact from this Markdown source:

```bash
python scripts/build_equilibrium_walkthrough.py
python scripts/build_equilibrium_walkthrough.py --check
```

This walkthrough is documentation-only and does not change runtime chemistry behavior.

