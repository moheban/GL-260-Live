### CIL RP Department Seminar Series

## Roadmap

Through this talk, we will:

- understand how we currently make sodium bicarbonate here at CIL
- equipment
- challenges associated with making pure sodium bicarbonate
- derive advanced equilibrium expressions
- learn how to accurately calculate speciation @ different \(CO_{2}\) uptake
- track and visualize live \(CO_{2}\) consumption while reaction is running
- calculate speciation and understand when to stop reaction
- improvements to final bicarb product QC and batch size

## So, how do we make it?

### Reactor setup

<img src="assets\equilibrium-walkthrough\bicarb reaction setup.jpg"
     alt="Reactor setup used in the synthesis of sodium bicarbonate MPT"
     style="width: 70%; display: block; margin: 1rem auto;">

*Reactor setup used in the synthesis of sodium bicarbonate MPT*

### Reaction Manifold

<img src="assets\equilibrium-walkthrough\bicarb manifold.jpg"
     alt="Manifold used in the synthesis of sodium bicarbonate MPT"
     style="width: 70%; display: block; margin: 1rem auto;">

*Manifold used in the synthesis of sodium bicarbonate MPT*

### Data Logging Equipment

<img src="assets\equilibrium-walkthrough\Sensor equipment bicarb.jpg"
     alt="Sensor equipment used in the synthesis of sodium bicarbonate MPT"
     style="width: 70%; display: block; margin: 1rem auto;">

*Sensor equipment used for data logging*

## What is the problem?

<img src="assets\equilibrium-walkthrough\bicarb scheme.png"
     alt="Sensor equipment used in the synthesis of sodium bicarbonate MPT"
     style="width: 100%; display: block; margin: 1rem auto;">

- Inconsistent batch size
- constantly failing QC
  - fail pH
  - fail ID test
  - fail titration

3 years ago I started working on improving this process. I'll present everything ive learned. 

Disclaimer: I LOVE math, so there is a lot of math. Dont worry! You wont need to think about it. We'll derive everything live and work through everything together. 

## Simple equilibrium, right?

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

- The bicarbonate equilibrium exists between \(NaHCO_{3}\), \(H_{2}CO_{3}\), & \(Na_{2}CO_{3}\)

- As we know, changing the concentration of one species shifts the equilibrium

- In a closed system, this makes making pure product a challenge. So how do we control this equilibrium to **only** make sodium bicarbonate?

## Equilibrium Reactions in the Highly Basic System

When [\(NaOH\)] is still high, absorbed \(CO_{2}\) reacts with \(NaOH\):

```latex
\mathrm{CO_2} + \mathrm{OH^-} \rightarrow \mathrm{HCO_3^-}
```

The bicarbonate then rapidly reacts with excess \(NaOH\) in solution to form carbonate \(CO_3^{2-}\) 

```latex
\mathrm{HCO_3^-} + \mathrm{OH^-} \rightarrow \mathrm{CO_3^{2-}} + \mathrm{H_2O}
```

Carbonate reaches equilibrium when excess \(NaOH\) is consumed.

```latex
2\mathrm{NaOH} + \mathrm{CO_2} \rightarrow \mathrm{Na_2CO_3} + \mathrm{H_2O}
```

Additional \(CO_{2}\) is required to convert carbonate back into bicarbonate:

```latex
\mathrm{Na_2CO_3} + \mathrm{CO_2} + \mathrm{H_2O} \rightarrow 2\mathrm{NaHCO_3}
```

The **desired** direct overall reaction for the product target is:

```latex
\mathrm{NaOH} + \mathrm{CO_2} \rightarrow \mathrm{NaHCO_3}
```

This process starts as a highly basic sodium hydroxide solution and uses absorbed \(CO_{2}\) to move the sodium-carbonate system toward sodium bicarbonate. 



## Starting Conditions

!!! note "Calculation Legend"
    - \(m_{\mathrm{NaOH}}\): NaOH mass charged to solution [\(g\)]
    - \(MW_{\mathrm{NaOH}}\): NaOH molecular weight [\(g mol^{-1}\)]
    - \(n_{\mathrm{NaOH}}\): NaOH amount [\(mol\)]
    - \(V_{\mathrm{liq}}\): liquid volume [\(L\)]
    - \(kg_{\mathrm{water}}\): water mass basis [\(Kg\)]
    - \(C_{\mathrm{NaOH}}\): NaOH molarity [\(mol L^{-1}\)]
    - \(m_{\mathrm{NaT}}\): total sodium molality [\(mol kg^{-1}\)]
    - \(n_{\mathrm{CO_2,eq1}}\), \(n_{\mathrm{CO_2,eq2}}\): \(CO_{2}\) mole endpoints [\(mol\)]
    - \(m_{\mathrm{CO_2,eq1}}\), \(m_{\mathrm{CO_2,eq2}}\): \(CO_{2}\) mass endpoints [\(g\)]


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
      <p class="basis-expression-title">Concentrations and expected \(CO_{2}\) uptake</p>
      <p class="basis-expression-copy">Start with the NaOH mass added, convert it into concentration, then determine the \(CO_{2}\) endpoints.</p>
    </div>
    <div class="basis-expression-result">
      <span>mol NaOH</span>
      <strong>17.5 mol</strong>
    </div>
  </div>

  <div class="basis-expression-grid">
    <div class="basis-expression-panel">
      <h4>Given Inputs</h4>
      <div class="basis-expression-row">
        <span>Amount NaOH</span>
        \[m_{\mathrm{NaOH}} = 700\ \mathrm{g}\]
      </div>
      <div class="basis-expression-row">
        <span>Molecular weight</span>
        \[MW_{\mathrm{NaOH}} = 40.00\ \mathrm{g\ mol^{-1}}\]
      </div>
      <div class="basis-expression-row">
        <span>Liquid volume</span>
        \[V_{\mathrm{liq}} = 2.200\ \mathrm{L}\]
        \[kg_{\mathrm{water}} \approx 2.2\ \mathrm{kg}\]
      </div>
    </div>

    <div class="basis-expression-panel">
      <h4>Converted Bases</h4>
      <div class="basis-expression-row">
        <span>Moles added</span>
        \[n_{\mathrm{NaOH}} = \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}} = \frac{700\ \mathrm{g}}{40.00\ \mathrm{g\ mol^{-1}}} = 17.5\ \mathrm{mol}\]
      </div>
      <div class="basis-expression-row">
        <span>Molarity calculation</span>
        \[C_{\mathrm{NaOH}} = \frac{n_{\mathrm{NaOH}}}{V_{\mathrm{liq}}} = \frac{17.5\ \mathrm{mol}}{2.200\ \mathrm{L}} = 7.9545\ \mathrm{mol\ L^{-1}}\]
      </div>
      <div class="basis-expression-row">
        <span>Molality calculation</span>
        \[m_{\mathrm{NaT}} = \frac{n_{\mathrm{NaOH}}}{kg_{\mathrm{water}}} = \frac{17.5\ \mathrm{mol}}{2.2\ \mathrm{kg}} = 7.9545\ \mathrm{mol\ kg^{-1}}\]
      </div>
    </div>
  </div>

  <div class="basis-expression-flow" aria-label="Stoichiometric CO2 endpoint flow">
    <div class="basis-expression-stage">
      <span>Endpoint 1</span>
      <strong>Carbonate formation</strong>
      \[n_{\mathrm{CO_2,eq1}} = \frac{n_{\mathrm{NaOH}}}{2} = 8.75\ \mathrm{mol}\]
    </div>
    <div class="basis-expression-stage">
      <span>\(CO_{2}\) required</span>
      <strong>\(CO_{2}\) to eq1</strong>
      \[m_{\mathrm{CO_2,eq1}} = 8.75\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 385.1\ \mathrm{g}\]
    </div>
    <div class="basis-expression-stage">
      <span>Bicarbonate Endpoint</span>
      <strong>Bicarbonate target</strong>
      \[n_{\mathrm{CO_2,eq2}} = n_{\mathrm{NaOH}} = 17.5\ \mathrm{mol}\]
      \[m_{\mathrm{CO_2,eq2}} = 17.5\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 770.2\ \mathrm{g}\]
    </div>
  </div>

  <p class="basis-expression-callout">The two concentration becomes the fixed sodium inventory used later by charge balance, speciation, and cycle-by-cycle pH prediction functions.</p>
</div>


<div class="inline-chart-anchor" data-inline-chart="stoich-impact"></div>

---

## Equilibrium Half-Reactions: Dipping Our Toes In
Lets derive the half-equations and constants required to make all the calculations we want.
- pH
- Speciation

### Carbonate and Water Equilibrium Half-Reactions

!!! note "Calculation Legend"
    - \(K_{a1}\), \(K_{a2}\), \(K_{w}\): equilibrium constants in activity form
    - \(a_{i}\): activity of species `i`
    - \(\gamma_i\): activity coefficient of species `i`
    - \(m_{i}\): molality of species `i` [\(mol kg^{-1}\)]
    - \(K_{H}\): Henry constant used by the model [\(mol kg^{-1} atm^{-1}\)]
    - \(p_{\mathrm{CO_2}}\): \(CO_{2}\) partial pressure \(atm\)
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


### Constants Used the NaOH-\(CO_{2}\) Calculation

!!! note "Calculation Legend"
    - \(K_{a1}\): first dissociation constant
    - \(K_{a2}\): second dissociation constant
    - \(K_{w}\): water autoionization constant


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

### Using Activity

!!! note "Calculation Legend"
    - `ideal model`: assumes \(\gamma_i = 1\), so activity equals molality.
    - `activity-corrected model`: computes \(\gamma_i\), then uses \(a_i = \gamma_i m_i\).
    - `high ionic strength`: concentrated electrolyte condition where ion-ion interactions materially change apparent equilibrium behavior.

For dilute solutions, we can often use concentration directly, \(a_i \approx m_i\).

In dilute solutions, the above approximation means each dissolved species behaves as though it were alone in water. 

The above approximation is mostly used in dilute buffer solutions. We do not have a dilute starting solution. 

At our high ionic strength starting condition, sodium, hydroxide, bicarbonate, and carbonate are **not** independent. Since we cant use the above approximation, our effective concentration is activity: \(a_i = \gamma_i \times m_i\).

The activity coefficient \(\gamma_i\) is the activity coefficient. 

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

## Equilibrium: Diving into the deep end

!!! note "Calculation Legend"
    - \(K_{b1}\), \(K_{b2}\): base-side equilibrium constants
    - \(K_{eq,\mathrm{overall}}\): overall equilibrium constant
    - \(a_{\mathrm{H_2O}}\): water activity, often approximated as `1` in concentrated electrolyte systems

Deriving the overall equilibrium expressions allows for downstream pH and speciation calculations.

### Refresher: Equilibrium

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Reaction Refresher</p>
      <p class="calculation-map-copy">In a strongly basic solution, absorbed \(CO_{2}\) forms carbonate first. The carbonate then reacts with additional \(CO_{2}\) and water to form sodium bicarbonate.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Target</span>
      <strong>NaHCO<sub>3</sub></strong>
    </div>
  </div>

  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. 14.5M NaOH</span>
      <strong>NaOH fixes sodium and hydroxide</strong>
      \[\mathrm{NaOH \rightarrow Na^{+} + OH^{-}}\]
      <p>The NaOH concentration sets the sodium inventory.</p>
    </div>
    <div class="calculation-map-step">
      <span>2. Carbonate formation</span>
      <strong>Early \(CO_{2}\) is consumed by excess hydroxide</strong>
      \[\mathrm{2NaOH + CO_{2} \rightarrow Na_{2}CO_{3} + H_{2}O}\]
      <p>At high pH, carbonate is formed first.</p>
    </div>
    <div class="calculation-map-step">
      <span>3. Bicarbonate conversion</span>
      <strong>Carbonate needs more \(CO_{2}\)</strong>
      \[\mathrm{Na_{2}CO_{3} + CO_{2} + H_{2}O \rightarrow 2NaHCO_{3}}\]
      <p>Any carbonate left behind remains as an impurity or carbonate-heavy fraction until it reacts with additional absorbed \(CO_{2}\).</p>
    </div>
  </div>

  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>4. Direct net target</span>
      <strong>The intended overall endpoint</strong>
      \[\mathrm{NaOH + CO_{2} \rightarrow NaHCO_{3}}\]
      <p>This is the clean net reaction, but isnt the whole story. We will jump into the half-reactions later</p>
    </div>
    <div class="calculation-map-step">
      <span>5. Equivalence split</span>
      <strong>Half load versus full load</strong>
      \[\mathrm{17.5\ mol\ NaOH \Rightarrow 8.75\ mol\ Na_{2}CO_{3}}\]
      <p>About 385.1 g \(CO_{2}\) reaches the carbonate midpoint; about 770.2 g \(CO_{2}\) is needed for pure bicarbonate.</p>
    </div>
    <div class="calculation-map-step">
      <span>6. Control the equilibrium</span>
      <strong>push the reaction towards bicarbonate</strong>
      \[\mathrm{CO_{3}^{2-} + CO_{2} + H_{2}O \rightarrow 2HCO_{3}^{-}}\]
      <p>The batch is not bicarbonate-rich until all carbonate has reacted with excess \(CO_{2}\).</p>
    </div>
  </div>

  <p class="calculation-map-callout">Sodium carbonate is generated first, and then bicarbonate is generated when starting from a highly basic system.</p>
</div>

### Advanced Derivation 

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

### Add Half Reactions to Get the Overall Equilibrium Expression

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
<td>Cancel the intermediate \(\mathrm{HCO_3^-}\) term.</td>
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

<div class="calculation-map">
  <div class="calculation-map-step">
    <span>6. Cancellation calculation</span>
    <strong>Reduce the substituted activity expression term by term</strong>
    \[
    K_{eq,\mathrm{overall}}
    =
    \frac{
    a_{\mathrm{H^+}} \times a_{\mathrm{HCO_3^-}}
    \times a_{\mathrm{H^+}} \times a_{\mathrm{CO_3^{2-}}}
    \times a_{\mathrm{H_2O}}
    }{
    a_{\mathrm{CO_2^*}} \times a_{\mathrm{HCO_3^-}}
    \times a_{\mathrm{H^+}}^2 \times a_{\mathrm{OH^-}}^2
    }
    \]
    \[
    =
    \left(\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{HCO_3^-}}}\right)
    \left(\frac{a_{\mathrm{H^+}}^2}{a_{\mathrm{H^+}}^2}\right)
    \left(
    \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}
    {a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
    \right)
    \]
    \[
    = 1 \times 1 \times
    \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}
    {a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
    \]
    \[
    K_{eq,\mathrm{overall}}
    \approx
    \frac{a_{\mathrm{CO_3^{2-}}}}
    {a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
    \quad\text{when}\quad a_{\mathrm{H_2O}} \approx 1
    \]
    <p>The bicarbonate and hydrogen-activity ratios each reduce to 1; applying the water-activity approximation leaves the overall base-side equilibrium expression.</p>
  </div>
</div>

## Controling bicarbonate formation

!!! note "Calculation Legend"
    - \(\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}}\): bicarbonate-to-carbonate activity ratio
    - \(a_{\mathrm{OH^-}}\): hydroxide activity
    - \(K_{a2}\), \(K_{w}\), \(K_{b2}\): equilibrium constants
    - \(p_{\mathrm{CO_2}}\): headspace \(CO_{2}\) partial pressure `[atm]`

As discussed, carbonate is strongly favored unless dissolved \(CO_{2}\) is driven high enough shift the distribution back toward bicarbonate.

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

Higher headspace \(p_{CO_2}\) facilitates bicarbonate formation, pushing the equilibrium towards bicarbonate

---

## Calculating Speciation and pH

**I dont do any of the following math by hand, i wrote a program to do it for me. Some of the following math requires soklving for quartic roots**

!!! note "Calculation Legend"
    - \([H^+]\), \([\mathrm{OH^-}]\), \([\mathrm{CO_2^*}]\), \([\mathrm{HCO_3^-}]\), \([\mathrm{CO_3^{2-}}]\), \([\mathrm{Na^+}]\): concentration/molarity-like model terms [\(mol L^{-1}\)] or model-consistent concentration basis]
    - \(C_{T}\): total inorganic carbon concentration on the same basis as reconstructed species
    - \(\alpha_0\), \(\alpha_1\), \(\alpha_2\): species fractions
    - \(D\): shared denominator in alpha-fraction identities
    - \(R_{q}\): charge-balance residual on concentration basis (target is zero)
    - \(x\): trial pH used by the numerical root search, with \([H^+] = 10^{-x}\)
    - \(\epsilon_{\mathrm{charge}}\): accepted absolute charge-residual tolerance

**We do not obtain \([H^+]\) from one isolated rearrangement because \([H^+]\) appears in water dissociation, every carbonate fraction, and charge balance at the same time. Instead, the model turns the full chemistry into one scalar function, \(R_q([H^+])\), and numerically finds the positive \([H^+]\) that makes \(R_q = 0\).**

!!! info "Derivation Walkthrough"
    **Goal:** calculate \([H^+]\) explicitly by solving charge balance, then recover pH and every carbonate species from that accepted root.

    **Step-by-step interpretation:** bracket a trial pH, convert that trial to \([H^+]\), calculate \(D\), fractions, species, and hydroxide, evaluate \(R_q\), then move the bracket and repeat until the residual is sufficiently close to zero.

    **Why this changes operation:** bicarbonate-control decisions are only trustworthy when one solved state satisfies both speciation and charge closure; otherwise purity guidance can point to the wrong operating region.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">How the Solver Finds [H+], pH, and Speciation</p>
      <p class="calculation-map-copy">Known carbon and sodium inputs define one charge-residual function. A bracketed root search changes pH until that function reaches zero.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Target</span>
      <strong>\(R_q = 0\)</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Fix the known inputs</span>
      \[
      \{C_T,\ [\mathrm{Na^+}],\ K_{a1},\ K_{a2},\ K_w\}
      \]
      <p>These values stay fixed while the solver searches for the one charge-balanced hydrogen concentration.</p>
    </div>
    <div class="calculation-map-step">
      <span>2. Choose a trial pH</span>
      \[
      x = \frac{x_{lo} + x_{hi}}{2}
      \]
      \[
      h = [H^+]_{trial} = 10^{-x}
      \]
      <p>The search is performed in pH/log space because \([H^+]\) spans many orders of magnitude.</p>
    </div>
    <div class="calculation-map-step">
      <span>3. Build the shared denominator</span>
      \[
      D(h) = h^2 + K_{a1}h + K_{a1}K_{a2}
      \]
      <p>This denominator converts the trial \(h\) into a complete carbonate distribution.</p>
    </div>
    <div class="calculation-map-step">
      <span>4. Calculate fractions and species</span>
      \[
      \alpha_0=\frac{h^2}{D},\quad
      \alpha_1=\frac{K_{a1}h}{D},\quad
      \alpha_2=\frac{K_{a1}K_{a2}}{D}
      \]
      \[
      [\mathrm{CO_2^*}]=\alpha_0C_T,\quad
      [\mathrm{HCO_3^-}]=\alpha_1C_T,\quad
      [\mathrm{CO_3^{2-}}]=\alpha_2C_T
      \]
    </div>
    <div class="calculation-map-step">
      <span>5. Calculate hydroxide and residual</span>
      \[
      [\mathrm{OH^-}] = \frac{K_w}{h}
      \]
      \[
      R_q(h)=[\mathrm{Na^+}]+h-[\mathrm{OH^-}]-[\mathrm{HCO_3^-}]-2[\mathrm{CO_3^{2-}}]
      \]
    </div>
    <div class="calculation-map-step">
      <span>6. Move the bracket and repeat</span>
      \[
      R_q(x_{lo})R_q(x_{mid}) \le 0
      \Rightarrow x_{hi}=x_{mid}
      \]
      \[
      \text{otherwise}\quad x_{lo}=x_{mid}
      \]
      <p>Each iteration halves the remaining pH interval while preserving a sign change around the root.</p>
    </div>
  </div>
  <div class="calculation-map-step">
    <span>7. Accept [H+] and report the final state</span>
    \[
    |R_q(h^*)| \le \epsilon_{\mathrm{charge}}
    \]
    \[
    [H^+] = h^*,\qquad \mathrm{pH}=-\log_{10}(h^*),\qquad
    \{\alpha_0,\alpha_1,\alpha_2\}=\{\alpha_0(h^*),\alpha_1(h^*),\alpha_2(h^*)\}
    \]
    <p>The accepted root is reused for pH, hydroxide, fractions, and species; these outputs therefore describe the same charge-balanced state.</p>
  </div>
</div>

Substituting the fraction equations directly into charge balance makes the one-variable solve explicit:

\[R_q(h) = [\mathrm{Na^+}] + h - \frac{K_w}{h} - C_T\left(\frac{K_{a1}h + 2K_{a1}K_{a2}}{h^2 + K_{a1}h + K_{a1}K_{a2}}\right) = 0\]

Everything on the right is known except \(h=[H^+]\). For each trial pH, the solver evaluates this expression. If \(R_q > 0\), the trial state has excess positive charge relative to the reconstructed anions. If \(R_q < 0\), it has excess negative charge. The sign tells the bracketed solver which half of the pH interval can still contain the zero crossing.

The ideal concentration form above is the presentation-level calculation. In the concentrated HMW/Pitzer path, the same root-search flow uses activities and updates activity coefficients around the charge-balance solve. The Python closed-system fallback uses bracketed bisection with a quartic cross-check/fallback, while the accelerated path preserves the same residual-to-root-to-speciation handoff.

### Deriving Alpha Fractions From the Equilibrium Constants

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

## Derivation Summary

<div class="inline-module-anchor" data-inline-module="derivation-stepper"></div>

## NaOH-CO2 Pitzer (HMW-Focused) Calculation Path: Even more complex

!!! note "Calculation Legend"
    - `I`: ionic strength [\(mol kg^{-1}\)]
    - \(m_{i}\), \(m_{j}\), \(m_{k}\): species molalities [\(mol kg^{-1}\)]
    - \(z_{i}\): ion charge number
    - \(\gamma_i\): activity coefficient
    - \(B_{ij}\), \(C_{ij}\), \(\Psi_{ijk}\), \(F(I)\), \(Z\): Pitzer-model terms used in the focused implementation
    - \(r_1=m_{\mathrm{HCO_3^-}}/m_{\mathrm{CO_2^*}}\): bicarbonate-to-carbonic-acid ratio [dimensionless]
    - \(r_2=m_{\mathrm{CO_3^{2-}}}/m_{\mathrm{HCO_3^-}}\): carbonate-to-bicarbonate ratio [dimensionless]
    - \(r_1r_2=m_{\mathrm{CO_3^{2-}}}/m_{\mathrm{CO_2^*}}\): derived carbonate-to-carbonic-acid ratio used in total-carbon reconstruction [dimensionless]
    - In this equilibrium section, \(r_1\) and \(r_2\) are dimensionless species ratios; they are distinct from the kinetic rate symbols introduced in Section 7.
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
      r_2 = \frac{K_{a2} \times \gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}} \times \gamma_{\mathrm{CO_3^{2-}}} \times [H^+]}
      \]
      \[
      r_2 = \frac{m_{\mathrm{CO_3^{2-}}}}{m_{\mathrm{HCO_3^-}}}
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

### Advanced Model Information: What HMW / PHREEQC-NaCO3 Pairing Means

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

Operationally, this yields more accurate calculations than an ideal model because sodium carbonate and sodium bicarbonate are not passive spectators. Sodium association changes the effective activities of the species present, and those activity changes shift the pH and fraction crossover. That is the specific error mode the HMW path is meant to avoid: a misleading carbonate-buffer plateau or incorrect pH slope when the solution is highly loaded with sodium.

---

## Reaction Kinetics
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

In this section, \(\mathrm{CO_2^*}\) is how the model treats dissolved CO2. In highly basic solution that pool is rapidly consumed by hydroxide, so the kinetic shorthand often combines hydration and bicarbonate formation into one apparent fast step.

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

### Liquid-Gas Interaction

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

### Pseudo-First-Order View at High Hydroxide Concentration

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

### Time-Scale Test for Interpreting Cycle Shape

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

### How This Connects to GL-260 Cycle Detection

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

## Cycle Uptake Math
Cycle-level uptake is converted into cumulative carbon loading, which becomes the cycle-by-cycle driver of equilibrium state updates.

!!! info "Derivation Walkthrough"
    **Goal:** convert per-cycle CO2 mass events into cumulative loading terms used by the equilibrium solver.

    **Step-by-step interpretation:** define cycle delta mass, accumulate to cumulative mass, then convert cumulative mass to molality (\(m_{CT,k}\)) using molecular weight and water basis.

    **Why this changes operation:** this conversion maps real cycle operation to carbonate chemistry state, so accurate loading is required to keep the process in the bicarbonate-dominant region needed for purer NaHCO3.

### Primary (Locked) Synthetic Cycle Uptake Sequence

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


### Pressure-Derived Uptake

!!! note "Calculation Legend"
    - \(\Delta P_{\mathrm{psi}}\), \(\Delta P_{\mathrm{atm}}\): pressure drop per cycle [`psi`, `atm`]
    - \(V_{\mathrm{headspace}}\): headspace volume [`L`]
    - \(R\): ideal gas constant [\(L atm mol^{-1} K^{-1}\)]
    - \(T\): absolute temperature [\(K\)]
    - \(n_{\mathrm{CO_2},i}\): inferred moles of CO2 transferred in cycle, \(i\) [\(mol\)]


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

## Integrated Worked Examples: From CO2 Uptake to pH and Speciation

This section brings the preceding derivations together into one repeatable calculation path. Each example starts with a measured cumulative \(CO_{2}\) uptake, converts it to the total-carbon basis, identifies the stoichiometric region, applies the focused HMW/Pitzer activity correction, closes charge balance, and reports the resulting pH and carbonate-family speciation.

!!! note "Calculation Legend"
    - \(m_{\mathrm{CO_2}}\): measured cumulative CO2 uptake [\(g\)]
    - \(n_{\mathrm{CO_2}}\): measured cumulative CO2 uptake [\(mol\)]
    - \(m_{CT,\mathrm{input}}\): total-carbon molality implied by measured uptake [\(mol\ kg^{-1}\)]
    - \(m_{CT,\mathrm{reactive}}\): reactive aqueous carbon admitted by the focused model [\(mol\ kg^{-1}\)]
    - \(m_{\mathrm{NaT}}\): fixed total sodium molality [\(mol\ kg^{-1}\)]
    - \(\gamma_i\): activity coefficient for species \(i\) [dimensionless]
    - \(a_i\): thermodynamic activity of species \(i\), calculated from \(a_i=\gamma_i m_i\)
    - \(\alpha_i\): fraction of total reactive carbon present as species \(i\) [dimensionless]; \(\alpha_i\) is a speciation fraction, not activity
    - \(r_1\): activity-corrected bicarbonate-to-carbonic-acid ratio, \(m_{\mathrm{HCO_3^-}}/m_{\mathrm{CO_2^*}}\)
    - \(r_2\): activity-corrected carbonate-to-bicarbonate ratio, \(m_{\mathrm{CO_3^{2-}}}/m_{\mathrm{HCO_3^-}}\)
    - \(r_1r_2\): derived carbonate-to-carbonic-acid ratio, \(m_{\mathrm{CO_3^{2-}}}/m_{\mathrm{CO_2^*}}\)
    - Within these worked equilibrium examples, \(r_1\) and \(r_2\) are dimensionless ratios, not the kinetic rates used later in Section 7.
    - \(R_q\): molal charge-balance residual; the accepted state requires \(R_q \approx 0\)

!!! info "Calculation Goal"
    **Given:** one measured cumulative \(CO_{2}\) uptake, \(m_{\mathrm{CO_2}}\), equal to \(250\ \mathrm{g}\), \(650\ \mathrm{g}\), or \(950\ \mathrm{g}\).

    **Solve for:** the activity-corrected hydrogen activity \(a_{\mathrm{H^+}}\), pH, and the complete reactive-carbon distribution \(\{\alpha_{\mathrm{CO_2^*}},\alpha_{\mathrm{HCO_3^-}},\alpha_{\mathrm{CO_3^{2-}}}\}\) at that uptake.

    **Why calculate it:** uptake mass alone says how much carbon entered the process, but it does not say whether residual caustic, carbonate, or bicarbonate controls the batch. pH quantifies the acid-base state; speciation identifies where the absorbed carbon resides. Both are required to decide whether the process is still caustic/carbonate-rich or has reached the bicarbonate-dominant operating region.

    **Acceptance test:** the reported pH and fractions are accepted only when carbon closure, fraction closure, and electrical charge balance are all satisfied by the same solved state.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Calculation Story</p>
      <p class="calculation-map-copy">Each block produces the input needed by the next block; no pH or fraction is introduced as an isolated lookup value.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Final outputs</span>
      <strong>pH + 3 fractions</strong>
    </div>
  </div>
  <div class="calculation-map-grid four-up">
    <div class="calculation-map-step">
      <span>1. Establish fixed inventory</span>
      \[
      m_{\mathrm{NaOH}} \longrightarrow n_{\mathrm{NaOH}} \longrightarrow m_{\mathrm{NaT}}
      \]
      <p>Why: sodium fixes the positive-charge inventory and both stoichiometric carbon endpoints.</p>
    </div>
    <div class="calculation-map-step">
      <span>2. Translate measured uptake</span>
      \[
      m_{\mathrm{CO_2}} \longrightarrow n_{\mathrm{CO_2}} \longrightarrow m_{CT}
      \]
      <p>Why: equilibrium and charge balance operate on a mole-per-water-mass basis, not grams.</p>
    </div>
    <div class="calculation-map-step">
      <span>3. Identify chemical region</span>
      \[
      m_{\mathrm{CO_2}} \lessgtr \{m_{\mathrm{CO_2,eq1}},m_{\mathrm{CO_2,eq2}}\}
      \]
      <p>Why: the region determines whether residual hydroxide, carbonate conversion, or the reactive-capacity limit governs the solve.</p>
    </div>
    <div class="calculation-map-step">
      <span>4. Solve and verify state</span>
      \[
      \{m_{CT},m_{\mathrm{NaT}},K,\gamma\} \longrightarrow \{\mathrm{pH},\alpha_0,\alpha_1,\alpha_2\}
      \]
      <p>Why: only a carbon-closed and charge-balanced state can support an operating conclusion.</p>
    </div>
  </div>
  <p class="calculation-map-callout">Flow into the next block: begin by deriving the shared sodium basis, carbon endpoints, and equilibrium constants used by all three uptake cases.</p>
</div>

### Shared Basis and Calculation Sequence

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Shared Worked-Example Basis</p>
      <p class="calculation-map-copy">Calculate the sodium inventory and thermodynamic constants once; only the measured carbon uptake changes among the three examples.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Na basis</span>
      <strong>7.9545 mol/kg</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. NaOH charge basis</span>
      \[
      n_{\mathrm{NaOH}} = \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}}
      \]
      \[
      n_{\mathrm{NaOH}} = \frac{700\ \mathrm{g}}{40.00\ \mathrm{g\ mol^{-1}}} = 17.5\ \mathrm{mol}
      \]
      \[
      m_{\mathrm{NaT}} = \frac{n_{\mathrm{NaOH}}}{kg_{\mathrm{water}}} = \frac{17.5\ \mathrm{mol}}{2.2\ \mathrm{kg}} = 7.9545\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Carbon endpoints</span>
      \[
      2\mathrm{NaOH} + \mathrm{CO_2} \rightarrow \mathrm{Na_2CO_3} + \mathrm{H_2O}
      \]
      \[
      n_{\mathrm{CO_2,eq1}} = \frac{n_{\mathrm{NaOH}}}{2},\qquad m_{\mathrm{CO_2,eq1}} = \frac{17.5}{2}\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} = 385.1\ \mathrm{g}
      \]
      \[
      \mathrm{NaOH} + \mathrm{CO_2} \rightarrow \mathrm{NaHCO_3}
      \]
      \[
      n_{\mathrm{CO_2,eq2}} = n_{\mathrm{NaOH}},\qquad m_{\mathrm{CO_2,eq2}} = 17.5\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} = 770.2\ \mathrm{g}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Equilibrium constants</span>
      \[
      K_a = 10^{-pK_a}
      \]
      \[
      K_{a1} = 10^{-6.3374} = 4.59833 \times 10^{-7}
      \]
      \[
      K_{a2} = 10^{-10.3393} = 4.57826 \times 10^{-11},\qquad K_w = 10^{-14}
      \]
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>4. Overall base-side equilibrium</span>
      \[
      K_{b1} = \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}a_{\mathrm{OH^-}}} = \frac{K_{a1}}{K_w} = 4.59833 \times 10^7
      \]
      \[
      K_{b2} = \frac{a_{\mathrm{CO_3^{2-}}}a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}}a_{\mathrm{OH^-}}} = \frac{K_{a2}}{K_w} = 4.57826 \times 10^3
      \]
      \[
      K_{eq,\mathrm{overall}} = K_{b1}K_{b2} = 2.10523 \times 10^{11}
      \]
    </div>
    <div class="calculation-map-step">
      <span>5. Uptake-to-carbon conversion</span>
      \[
      n = \frac{m}{MW}\quad\Longrightarrow\quad n_{\mathrm{CO_2}} = \frac{m_{\mathrm{CO_2}}}{44.01\ \mathrm{g\ mol^{-1}}}
      \]
      \[
      \mathrm{molality} = \frac{\mathrm{moles\ solute}}{\mathrm{kg\ solvent}}\quad\Longrightarrow\quad m_{CT,\mathrm{input}} = \frac{n_{\mathrm{CO_2}}}{2.2\ \mathrm{kg}}
      \]
      \[
      m_{CT,\mathrm{reactive}} = \min\left(m_{CT,\mathrm{input}},m_{\mathrm{NaT}}\right)
      \]
    </div>
  </div>
  <p class="calculation-map-callout">Block handoff: the fixed sodium inventory, endpoint masses, constants, and case-specific \(m_{CT}\) now become the inputs to the equilibrium derivation below. The reactive-carbon cap represents the sodium charge capacity for the bicarbonate-dominant liquid state; carbon reported above that capacity is identified separately instead of being forced into an unsupported aqueous state.</p>
</div>

!!! info "Calculation Goal: Derive the Coupled Equilibrium Solve"
    **Solve for:** the single unknown hydrogen molality \(m_{\mathrm{H^+}}\) that simultaneously determines pH, hydroxide, and all three carbonate-family species.

    **Why:** pH and speciation cannot be solved independently. Changing \(m_{\mathrm{H^+}}\) changes the acid-dissociation ratios, hydroxide inventory, ionic strength, activity coefficients, and charge residual. The accepted solution is therefore the common root of these coupled relationships.

The derivation starts from the definitions of activity, the two acid-dissociation constants, total-carbon conservation, water autoionization, and electroneutrality. The focused HMW/Pitzer model supplies \(\gamma_i\); the algebra below shows how those coefficients enter the solve.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Derive the HMW/Pitzer Solve From First Principles</p>
      <p class="calculation-map-copy">Begin with activity definitions and equilibrium laws, derive the two species ratios, substitute them into carbon conservation, then close the resulting state with water equilibrium and charge balance.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Accept when</span>
      <strong>Rq = 0</strong>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>1. Define activity and ionic strength</span>
      \[
      a_i = \gamma_i m_i
      \]
      \[
      I = \frac{1}{2}\sum_i m_i z_i^2
      \]
      \[
      I = \frac{1}{2}\left(m_{\mathrm{Na^+}}+m_{\mathrm{H^+}}+m_{\mathrm{OH^-}}+m_{\mathrm{HCO_3^-}}+4m_{\mathrm{CO_3^{2-}}}\right)
      \]
      \[
      \ln(\gamma_i) = z_i^2F(I) + \sum_j m_j\left(2B_{ij}+ZC_{ij}\right) + \sum_{j,k}m_jm_k\Psi_{ijk} + \cdots
      \]
      <p>The factor \(z_i^2\) makes divalent carbonate contribute four times its molality to ionic strength. The focused HMW pair and ternary terms then convert that ionic state into each \(\gamma_i\).</p>
    </div>
    <div class="calculation-map-step">
      <span>2. Derive the bicarbonate ratio</span>
      \[
      \mathrm{CO_2^*} \rightleftharpoons \mathrm{H^+}+\mathrm{HCO_3^-}
      \]
      \[
      K_{a1}=\frac{a_{\mathrm{H^+}}a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}}
      =\frac{(\gamma_{\mathrm{H^+}}m_{\mathrm{H^+}})(\gamma_{\mathrm{HCO_3^-}}m_{\mathrm{HCO_3^-}})}{m_{\mathrm{CO_2^*}}}
      \]
      \[
      \frac{m_{\mathrm{HCO_3^-}}}{m_{\mathrm{CO_2^*}}}
      =\frac{K_{a1}}{\gamma_{\mathrm{H^+}}\gamma_{\mathrm{HCO_3^-}}m_{\mathrm{H^+}}}
      =r_1
      \]
      <p>The neutral \(CO_2^*\) standard-state coefficient is treated as unity in this focused ratio.</p>
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>3. Derive the carbonate ratio</span>
      \[
      \mathrm{HCO_3^-} \rightleftharpoons \mathrm{H^+}+\mathrm{CO_3^{2-}}
      \]
      \[
      K_{a2}=\frac{a_{\mathrm{H^+}}a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}
      =\frac{(\gamma_{\mathrm{H^+}}m_{\mathrm{H^+}})(\gamma_{\mathrm{CO_3^{2-}}}m_{\mathrm{CO_3^{2-}}})}{\gamma_{\mathrm{HCO_3^-}}m_{\mathrm{HCO_3^-}}}
      \]
      \[
      \frac{m_{\mathrm{CO_3^{2-}}}}{m_{\mathrm{HCO_3^-}}}
      =\frac{K_{a2}\gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}}\gamma_{\mathrm{CO_3^{2-}}}m_{\mathrm{H^+}}}
      =r_2
      \]
    </div>
    <div class="calculation-map-step">
      <span>4. Derive species from carbon closure</span>
      \[
      m_{CT}=m_{\mathrm{CO_2^*}}+m_{\mathrm{HCO_3^-}}+m_{\mathrm{CO_3^{2-}}}
      \]
      \[
      m_{\mathrm{HCO_3^-}}=r_1m_{\mathrm{CO_2^*}},\qquad
      m_{\mathrm{CO_3^{2-}}}=r_2m_{\mathrm{HCO_3^-}}=r_1r_2m_{\mathrm{CO_2^*}}
      \]
      \[
      m_{CT}=m_{\mathrm{CO_2^*}}\left(1+r_1+r_1r_2\right)
      \]
      \[
      m_{\mathrm{CO_2^*}}=\frac{m_{CT}}{1+r_1+r_1r_2}
      \]
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>5. Derive hydroxide and pH</span>
      \[
      \mathrm{H_2O} \rightleftharpoons \mathrm{H^+}+\mathrm{OH^-}
      \]
      \[
      K_w=a_{\mathrm{H^+}}a_{\mathrm{OH^-}}
      =\left(\gamma_{\mathrm{H^+}}m_{\mathrm{H^+}}\right)\left(\gamma_{\mathrm{OH^-}}m_{\mathrm{OH^-}}\right)
      \]
      \[
      m_{\mathrm{OH^-}}=\frac{K_w}{\gamma_{\mathrm{H^+}}\gamma_{\mathrm{OH^-}}m_{\mathrm{H^+}}}
      \]
      \[
      \mathrm{pH}=-\log_{10}(a_{\mathrm{H^+}})=-\log_{10}(\gamma_{\mathrm{H^+}}m_{\mathrm{H^+}})
      \]
    </div>
    <div class="calculation-map-step">
      <span>6. Derive the solver equation</span>
      \[
      \mathrm{positive\ charge}=\mathrm{negative\ charge}
      \]
      \[
      m_{\mathrm{Na^+}}+m_{\mathrm{H^+}}
      =m_{\mathrm{OH^-}}+m_{\mathrm{HCO_3^-}}+2m_{\mathrm{CO_3^{2-}}}
      \]
      \[
      R_q = m_{\mathrm{Na^+}} + m_{\mathrm{H^+}} - m_{\mathrm{OH^-}} - m_{\mathrm{HCO_3^-}} - 2m_{\mathrm{CO_3^{2-}}}
      \]
      \[
      R_q(m_{\mathrm{H^+}})=0
      \]
      <p>The solver varies \(m_{\mathrm{H^+}}\), recomputes every dependent term, updates \(\gamma_i\), and repeats until both \(R_q\) and the activity coefficients converge.</p>
    </div>
  </div>
  <p class="calculation-map-callout">Block handoff: the symbolic solve is complete. Each worked example now supplies one measured uptake, calculates its \(m_{CT}\), selects the correct stoichiometric region, and substitutes the converged numerical state into these derived equations.</p>
</div>

### Worked Example A: 250 g CO2 Uptake

!!! info "Calculation Goal: 250 g Uptake"
    **What is being solved:** determine the pH and reactive-carbon fractions produced by \(250\ \mathrm{g}\) of measured uptake.

    **Why this case matters:** it tests an early batch state before first equivalence, where a large residual hydroxide inventory should keep pH very high and drive essentially all reactive carbon to carbonate.

    **Required result:** calculate \(m_{CT}\), residual \(m_{\mathrm{OH^-}}\), \(a_{\mathrm{H^+}}\), pH, all three species molalities and fractions, then prove charge closure.

Because \(250\ \mathrm{g} < 385.1\ \mathrm{g}\), this point is before first equivalence. The focused model therefore uses the dominant stoichiometric reaction \(CO_2 + 2OH^- \rightarrow CO_3^{2-} + H_2O\), then applies Pitzer activity to the residual hydroxide for pH.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">250 g Uptake: Carbon and Stoichiometric State</p>
      <p class="calculation-map-copy">Convert uptake to carbon molality, consume two moles of hydroxide per mole of carbon, and identify the pre-equivalence carbonate inventory.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Region</span>
      <strong>Pre-eq1</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Convert uptake to moles</span>
      \[
      n_{\mathrm{CO_2}} = \frac{m_{\mathrm{CO_2}}}{MW_{\mathrm{CO_2}}}
      \]
      \[
      n_{\mathrm{CO_2}} = \frac{250\ \mathrm{g}}{44.01\ \mathrm{g\ mol^{-1}}} = 5.68053\ \mathrm{mol}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Convert to total carbon</span>
      \[
      m_{CT} = \frac{n_{\mathrm{CO_2}}}{kg_{\mathrm{water}}} = \frac{5.68053\ \mathrm{mol}}{2.2\ \mathrm{kg}} = 2.58206\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Consume hydroxide</span>
      \[
      \mathrm{CO_2}+2\mathrm{OH^-}\rightarrow\mathrm{CO_3^{2-}}+\mathrm{H_2O}
      \]
      \[
      n_{\mathrm{OH^-,remaining}} = n_{\mathrm{NaOH}} - 2n_{\mathrm{CO_2}} = 17.5 - (2 \times 5.68053) = 6.13895\ \mathrm{mol}
      \]
      \[
      m_{\mathrm{OH^-}} = \frac{6.13895}{2.2} = 2.79043\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>4. Stoichiometric carbonate inventory</span>
    \[
    n_{\mathrm{CO_3^{2-}}} = n_{\mathrm{CO_2}} = 5.68053\ \mathrm{mol}
    \]
    \[
    m_{\mathrm{CO_3^{2-}}} = \frac{5.68053}{2.2} = 2.58206\ \mathrm{mol\ kg^{-1}}
    \]
  </div>
  <p class="calculation-map-callout">Block handoff: the uptake conversion produces \(m_{CT}=2.58206\), and the pre-equivalence stoichiometry produces \(m_{\mathrm{OH^-}}=2.79043\) plus \(m_{\mathrm{CO_3^{2-}}}=2.58206\). These become the ionic-state inputs for the pH and closure block.</p>
</div>

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">250 g Uptake: pH and Speciation Result</p>
      <p class="calculation-map-copy">Calculate ionic strength and hydroxide activity, then verify carbon and charge closure for the stoichiometric pre-equivalence state.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Calculated pH</span>
      <strong>14.8117</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>5. Ionic strength</span>
      \[
      I = \frac{1}{2}\left(7.95455 + 2.79043 + 4(2.58206)\right)
      \]
      \[
      I = 10.5366\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>6. Hydroxide activity</span>
      \[
      \gamma_{\mathrm{OH^-}} = 2.32269
      \]
      \[
      a_{\mathrm{OH^-}} = 2.32269 \times 2.79043 = 6.48130
      \]
    </div>
    <div class="calculation-map-step">
      <span>7. Hydrogen activity and pH</span>
      \[
      a_{\mathrm{H^+}} = \frac{10^{-14}}{6.48130} = 1.54290 \times 10^{-15}
      \]
      \[
      \mathrm{pH} = -\log_{10}(1.54290 \times 10^{-15}) = 14.8117
      \]
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>8. Species molalities</span>
      \[
      m_{\mathrm{CO_2^*}} = 0,\qquad m_{\mathrm{HCO_3^-}} = 0
      \]
      \[
      m_{\mathrm{CO_3^{2-}}} = 2.58206\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>9. Species fractions</span>
      \[
      \alpha_{\mathrm{CO_2^*}} = 0.0000,\qquad \alpha_{\mathrm{HCO_3^-}} = 0.0000
      \]
      \[
      \alpha_{\mathrm{CO_3^{2-}}} = \frac{2.58206}{2.58206} = 1.0000
      \]
    </div>
  </div>
  <div class="calculation-map-step">
    <span>10. Charge-balance check</span>
    \[
    R_q = 7.95455 - 2.79043 - 2(2.58206) = 6.22 \times 10^{-15} \approx 0
    \]
  </div>
  <p class="calculation-map-callout">Result and handoff: at 250 g uptake, substantial hydroxide remains, so the calculated \(\mathrm{pH}=14.8117\) and \(\alpha_{\mathrm{CO_3^{2-}}}=1.0000\) describe an early carbonate-forming state. The next example moves beyond first equivalence to show how the same derivation changes when bicarbonate formation becomes possible.</p>
</div>

### Worked Example B: 650 g CO2 Uptake

!!! info "Calculation Goal: 650 g Uptake"
    **What is being solved:** determine the pH and three reactive-carbon fractions after \(650\ \mathrm{g}\) uptake, using the full activity-corrected equilibrium solve.

    **Why this case matters:** it lies between first and second equivalence, where carbonate is being converted into bicarbonate. This is the transition region operators care about when deciding whether bicarbonate is dominant but carbonate impurity is still material.

    **Required result:** calculate \(m_{CT}\), form a stoichiometric species estimate, derive the converged HMW/Pitzer ratios, reconstruct every species, calculate pH, and prove carbon, fraction, and charge closure.

Because \(385.1\ \mathrm{g} < 650\ \mathrm{g} < 770.2\ \mathrm{g}\), this point is between the carbonate and bicarbonate endpoints. The stoichiometric ledger first estimates how much carbonate has converted to bicarbonate; the activity-corrected solve then refines that estimate and calculates pH.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">650 g Uptake: Loading and Stoichiometric Estimate</p>
      <p class="calculation-map-copy">Translate uptake to total carbon and use the carbon added after first equivalence to estimate carbonate-to-bicarbonate conversion.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Region</span>
      <strong>Eq1 to eq2</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Convert uptake</span>
      \[
      n_{\mathrm{CO_2}} = \frac{m_{\mathrm{CO_2}}}{MW_{\mathrm{CO_2}}} = \frac{650}{44.01} = 14.76937\ \mathrm{mol}
      \]
      \[
      m_{CT} = \frac{n_{\mathrm{CO_2}}}{kg_{\mathrm{water}}} = \frac{14.76937}{2.2} = 6.71335\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Carbon beyond eq1</span>
      \[
      n_{\mathrm{CO_2,after\ eq1}} = n_{\mathrm{CO_2}} - n_{\mathrm{CO_2,eq1}} = 14.76937 - 8.75 = 6.01937\ \mathrm{mol}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Stoichiometric estimate</span>
      \[
      \mathrm{CO_3^{2-}}+\mathrm{CO_2}+\mathrm{H_2O}\rightarrow2\mathrm{HCO_3^-}
      \]
      \[
      n_{\mathrm{HCO_3^-}} \approx 2n_{\mathrm{CO_2,after\ eq1}} = 2(6.01937) = 12.03874\ \mathrm{mol}
      \]
      \[
      n_{\mathrm{CO_3^{2-}}} \approx n_{\mathrm{CO_2,eq1}}-n_{\mathrm{CO_2,after\ eq1}} = 8.75 - 6.01937 = 2.73063\ \mathrm{mol}
      \]
    </div>
  </div>
  <p class="calculation-map-callout">Block handoff: \(m_{CT}=6.71335\) fixes total carbon, while the stoichiometric estimate supplies a chemically reasonable starting distribution. The next block replaces that estimate with the converged activity-corrected state.</p>
</div>

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">650 g Uptake: Activity-Corrected Solve</p>
      <p class="calculation-map-copy">Use the converged Pitzer coefficients to calculate activity ratios, species molalities, pH, and closure.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Calculated pH</span>
      <strong>9.1405</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>4. Converged ionic state</span>
      \[
      I = \frac{1}{2}\left(7.95455+2.75045 \times 10^{-9}+5.66403 \times 10^{-6}+5.46869+4(1.24292)\right)
      \]
      \[
      I = 9.19747\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      \gamma_{\mathrm{H^+}} = 0.263104,\quad \gamma_{\mathrm{OH^-}} = 2.43973
      \]
      \[
      \gamma_{\mathrm{HCO_3^-}} = 0.201535,\quad \gamma_{\mathrm{CO_3^{2-}}} = 0.0560991
      \]
    </div>
    <div class="calculation-map-step">
      <span>5. Solved hydrogen state</span>
      \[
      m_{\mathrm{H^+}} = 2.75045 \times 10^{-9}\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      a_{\mathrm{H^+}} = 0.263104(2.75045 \times 10^{-9}) = 7.23657 \times 10^{-10}
      \]
    </div>
    <div class="calculation-map-step">
      <span>6. Activity-corrected ratios</span>
      \[
      r_1 = \frac{4.59833 \times 10^{-7}}{(0.263104)(0.201535)(2.75045 \times 10^{-9})} = 3152.96
      \]
      \[
      r_2 = \frac{(4.57826 \times 10^{-11})(0.201535)}{(0.263104)(0.0560991)(2.75045 \times 10^{-9})} = 0.227280
      \]
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>7. Reconstruct species</span>
      \[
      m_{\mathrm{CO_2^*}} = \frac{6.71335}{1+3152.96+(3152.96)(0.227280)} = 0.00173447
      \]
      \[
      m_{\mathrm{HCO_3^-}} = 3152.96(0.00173447) = 5.46869
      \]
      \[
      m_{\mathrm{CO_3^{2-}}} = (3152.96)(0.227280)(0.00173447) = 1.24292
      \]
    </div>
    <div class="calculation-map-step">
      <span>8. Hydroxide and pH</span>
      \[
      a_{\mathrm{OH^-}} = \frac{10^{-14}}{7.23657 \times 10^{-10}} = 1.38187 \times 10^{-5}
      \]
      \[
      m_{\mathrm{OH^-}} = \frac{1.38187 \times 10^{-5}}{2.43973} = 5.66403 \times 10^{-6}
      \]
      \[
      \mathrm{pH} = -\log_{10}(7.23657 \times 10^{-10}) = 9.1405
      \]
    </div>
    <div class="calculation-map-step">
      <span>9. Species fractions</span>
      \[
      \alpha_{\mathrm{CO_2^*}} = \frac{0.00173447}{6.71335} = 0.000258
      \]
      \[
      \alpha_{\mathrm{HCO_3^-}} = \frac{5.46869}{6.71335} = 0.814600
      \]
      \[
      \alpha_{\mathrm{CO_3^{2-}}} = \frac{1.24292}{6.71335} = 0.185142
      \]
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>10. Carbon closure</span>
      \[
      0.00173447 + 5.46869 + 1.24292 = 6.71335\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      0.000258 + 0.814600 + 0.185142 = 1.000000
      \]
    </div>
    <div class="calculation-map-step">
      <span>11. Charge closure</span>
      \[
      R_q = 7.95455 + 2.75045 \times 10^{-9} - 5.66403 \times 10^{-6} - 5.46869 - 2(1.24292)
      \]
      \[
      R_q = -4.44 \times 10^{-15} \approx 0
      \]
    </div>
  </div>
  <p class="calculation-map-callout">Result and handoff: at 650 g uptake, bicarbonate is dominant at approximately \(81.46\%\), but approximately \(18.51\%\) carbonate remains and \(\mathrm{pH}=9.1405\). The next example crosses second equivalence and must first test whether the measured uptake exceeds the model's reactive-liquid capacity.</p>
</div>

### Worked Example C: 950 g CO2 Uptake

!!! info "Calculation Goal: 950 g Uptake"
    **What is being solved:** determine the pH and reactive-liquid speciation associated with a reported \(950\ \mathrm{g}\) uptake while explicitly accounting for the focused model's sodium-limited carbon capacity.

    **Why this case matters:** \(950\ \mathrm{g}\) is beyond the theoretical bicarbonate endpoint. A capacity check is required before equilibrium math so the model does not silently force excess carbon into a liquid state it was not designed to represent.

    **Required result:** calculate input carbon, reactive carbon, and excess carbon separately; solve pH and speciation only for the admitted reactive inventory; then prove closure and state the model limitation.

Because \(950\ \mathrm{g} > 770.2\ \mathrm{g}\), the measured uptake exceeds the model's \(17.5\ \mathrm{mol}\) reactive bicarbonate capacity. This example must therefore separate the measured input from the reactive aqueous inventory before calculating pH and speciation.

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">950 g Uptake: Capacity Check</p>
      <p class="calculation-map-copy">Calculate the uptake-implied carbon loading, apply the model's sodium-capacity guardrail, and quantify the carbon outside the reactive liquid inventory.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Region</span>
      <strong>Beyond eq2</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>1. Convert measured uptake</span>
      \[
      n_{\mathrm{CO_2,input}} = \frac{m_{\mathrm{CO_2,input}}}{MW_{\mathrm{CO_2}}} = \frac{950}{44.01} = 21.58600\ \mathrm{mol}
      \]
      \[
      m_{CT,\mathrm{input}} = \frac{n_{\mathrm{CO_2,input}}}{kg_{\mathrm{water}}} = \frac{21.58600}{2.2} = 9.81182\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>2. Apply reactive capacity</span>
      \[
      n_{CT,\mathrm{reactive}} = \min(21.58600,17.5) = 17.5\ \mathrm{mol}
      \]
      \[
      m_{CT,\mathrm{reactive}} = \frac{17.5}{2.2} = 7.95455\ \mathrm{mol\ kg^{-1}}
      \]
    </div>
    <div class="calculation-map-step">
      <span>3. Carbon outside reactive inventory</span>
      \[
      n_{\mathrm{CO_2,excess}} = 21.58600 - 17.5 = 4.08600\ \mathrm{mol}
      \]
      \[
      m_{\mathrm{CO_2,excess}} = 4.08600 \times 44.01 = 179.825\ \mathrm{g}
      \]
    </div>
  </div>
  <p class="calculation-map-callout">Block handoff: only \(m_{CT,\mathrm{reactive}}=7.95455\) enters the next equilibrium block; \(179.825\ \mathrm{g}\) remains outside this focused reactive inventory. It may represent headspace carbon, nonreactive reported uptake, or carbon requiring a broader phase-partition model. If all 950 g is analytically confirmed as dissolved inorganic carbon, the present model scope has been exceeded and its capped pH must not be presented as a full-liquid prediction.</p>
</div>

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">950 g Uptake: Capped Activity-Corrected Solve</p>
      <p class="calculation-map-copy">Solve the maximum reactive liquid inventory at the sodium capacity and report the resulting bicarbonate-dominant state.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Calculated pH</span>
      <strong>7.8538</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>4. Converged ionic state</span>
      \[
      I = \frac{1}{2}\left(7.95455+4.76087 \times 10^{-8}+2.74460 \times 10^{-7}+7.84889+4(0.0528252)\right)
      \]
      \[
      I = 8.00737\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      \gamma_{\mathrm{H^+}} = 0.294086,\quad \gamma_{\mathrm{OH^-}} = 2.60232
      \]
      \[
      \gamma_{\mathrm{HCO_3^-}} = 0.221041,\quad \gamma_{\mathrm{CO_3^{2-}}} = 0.107394
      \]
    </div>
    <div class="calculation-map-step">
      <span>5. Solved hydrogen state</span>
      \[
      m_{\mathrm{H^+}} = 4.76087 \times 10^{-8}\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      a_{\mathrm{H^+}} = 0.294086(4.76087 \times 10^{-8}) = 1.40011 \times 10^{-8}
      \]
    </div>
    <div class="calculation-map-step">
      <span>6. Activity-corrected ratios</span>
      \[
      r_1 = \frac{4.59833 \times 10^{-7}}{(0.294086)(0.221041)(4.76087 \times 10^{-8})} = 148.582
      \]
      \[
      r_2 = \frac{(4.57826 \times 10^{-11})(0.221041)}{(0.294086)(0.107394)(4.76087 \times 10^{-8})} = 0.00673027
      \]
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>7. Reconstruct species</span>
      \[
      m_{\mathrm{CO_2^*}} = \frac{7.95455}{1+148.582+(148.582)(0.00673027)} = 0.0528254
      \]
      \[
      m_{\mathrm{HCO_3^-}} = 148.582(0.0528254) = 7.84889
      \]
      \[
      m_{\mathrm{CO_3^{2-}}} = (148.582)(0.00673027)(0.0528254) = 0.0528252
      \]
    </div>
    <div class="calculation-map-step">
      <span>8. Hydroxide and pH</span>
      \[
      a_{\mathrm{OH^-}} = \frac{10^{-14}}{1.40011 \times 10^{-8}} = 7.14232 \times 10^{-7}
      \]
      \[
      m_{\mathrm{OH^-}} = \frac{7.14232 \times 10^{-7}}{2.60232} = 2.74460 \times 10^{-7}
      \]
      \[
      \mathrm{pH} = -\log_{10}(1.40011 \times 10^{-8}) = 7.8538
      \]
    </div>
    <div class="calculation-map-step">
      <span>9. Species fractions</span>
      \[
      \alpha_{\mathrm{CO_2^*}} = \frac{0.0528254}{7.95455} = 0.006641
      \]
      \[
      \alpha_{\mathrm{HCO_3^-}} = \frac{7.84889}{7.95455} = 0.986718
      \]
      \[
      \alpha_{\mathrm{CO_3^{2-}}} = \frac{0.0528252}{7.95455} = 0.006641
      \]
    </div>
  </div>
  <div class="calculation-map-grid">
    <div class="calculation-map-step">
      <span>10. Carbon closure</span>
      \[
      0.0528254 + 7.84889 + 0.0528252 = 7.95455\ \mathrm{mol\ kg^{-1}}
      \]
      \[
      0.006641 + 0.986718 + 0.006641 = 1.000000
      \]
    </div>
    <div class="calculation-map-step">
      <span>11. Charge closure</span>
      \[
      R_q = 7.95455 + 4.76087 \times 10^{-8} - 2.74460 \times 10^{-7} - 7.84889 - 2(0.0528252)
      \]
      \[
      R_q = -1.04 \times 10^{-15} \approx 0
      \]
    </div>
  </div>
  <p class="calculation-map-callout">Result and handoff: at the model's reactive-capacity limit, bicarbonate accounts for approximately \(98.67\%\) of reactive dissolved carbon and the calculated capped pH is \(7.8538\). Additional reported uptake does not lower this result unless a broader excess-CO2 phase-partition path is used. The final comparison block now places all three accepted states on one operating trajectory.</p>
</div>

### Worked-Example Comparison

<div class="calculation-map">
  <div class="calculation-map-heading">
    <div>
      <p class="calculation-map-title">Three Uptake States at a Glance</p>
      <p class="calculation-map-copy">Read the examples as one trajectory: residual caustic gives way to carbonate, bicarbonate becomes dominant between the endpoints, and the focused model reaches its reactive-carbon capacity beyond second equivalence.</p>
    </div>
    <div class="calculation-map-badge">
      <span>Examples</span>
      <strong>3 states</strong>
    </div>
  </div>
  <div class="calculation-map-grid three-up">
    <div class="calculation-map-step">
      <span>250 g CO2</span>
      \[
      \mathrm{pH} = 14.8117
      \]
      \[
      (\alpha_{\mathrm{CO_2^*}},\alpha_{\mathrm{HCO_3^-}},\alpha_{\mathrm{CO_3^{2-}}}) = (0.0000,0.0000,1.0000)
      \]
    </div>
    <div class="calculation-map-step">
      <span>650 g CO2</span>
      \[
      \mathrm{pH} = 9.1405
      \]
      \[
      (\alpha_{\mathrm{CO_2^*}},\alpha_{\mathrm{HCO_3^-}},\alpha_{\mathrm{CO_3^{2-}}}) = (0.000258,0.814600,0.185142)
      \]
    </div>
    <div class="calculation-map-step">
      <span>950 g CO2</span>
      \[
      \mathrm{pH}_{\mathrm{capped}} = 7.8538
      \]
      \[
      (\alpha_{\mathrm{CO_2^*}},\alpha_{\mathrm{HCO_3^-}},\alpha_{\mathrm{CO_3^{2-}}}) = (0.006641,0.986718,0.006641)
      \]
    </div>
  </div>
  <p class="calculation-map-callout">The operational pattern is the main result: increasing uptake consumes free hydroxide, drives carbonate toward bicarbonate, and lowers pH. The 950 g example also demonstrates why a model-capacity check must occur before any pH value is interpreted.</p>
</div>

---

## Worked NaOH-Pitzer Simulation Table (Synthetic Cycles to 900 g)

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

## Worked Real-World Example: PR-24304 Sodium Bicarbonate Batch 1

This section connects the derivation to a real GL-260 presentation artifact rather than the locked synthetic cycle sequence.

### Profile Basis and Stoichiometric Translation

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

### Reading the Combined Triple-Axis Plot

![PR-24304 Batch 1 Day 1-6 combined triple-axis plot](assets/equilibrium-walkthrough/pr-24304-batch-1-day-1-6-combined-triple-axis.png)

The combined triple-axis plot is the process-history view. During a live explanation, read it from left to right as the experimental record:

- Reactor pressure shows each CO2 contact/reaction event.
- The pressure derivative highlights where pressure is changing fastest, which helps identify uptake windows and cycle boundaries.
- Reactor/manifold temperature traces show whether thermal behavior could be influencing pressure, rate, or inferred gas uptake.

The equilibrium math does not replace this plot. The plot tells GL-260 where the physical events are; the equilibrium model interprets what those events imply for pH and carbonate speciation.

### Reading the Speciation Timeline Plot

![PR-24304 Batch 1 Day 1-6 cycle speciation timeline](assets/equilibrium-walkthrough/pr-24304-batch-1-cycle-speciation-timeline-day-1-6.png)

The speciation timeline maps detected cycle progression and estimated CO2 loading into sodium-basis species fractions:

- `NaOH %` indicates remaining caustic character.
- `Na2CO3 %` indicates carbonate-rich intermediate behavior.
- `NaHCO3 %` indicates the desired bicarbonate-forming endpoint.
- Measured pH anchors, when present, correct the estimated pH and speciation path rather than being treated as separate annotations.

Early in the run, high hydroxide activity drives carbonate formation. 
As CO2 loading increases and hydroxide is consumed, the system moves through the carbonate-rich region and toward bicarbonate dominance. 
The HMW Pitzer model makes that crossover more realistic by correcting sodium-carbonate activities in the concentrated electrolyte regime.

## How has Bicarb production been with all of this understanding?

<img src="assets\equilibrium-walkthrough\Screenshot 2026-06-22 143155.png"
     alt="Batch Ledger"
     style="width: 90%; display: block; margin: 1rem auto;">

- consistent batch size
- consistent pH
- QC has not failed once.
- 1,300g / week
- 100,000 data points / run
  - easily plot, analyze, and visualize collected data allowing for informed decisions on endpoint/blending
- standardized manifold
  - no more chasing leaks
  - safer and easier to operate
- GL-260 data logging
- GL-260 Data Processing program
  - can plot anything  

## Supplementary Sections

### Measured-pH Calibration + Hybrid ML Correction (Analysis Mode)
Measured anchors reshape the baseline simulation, and ML residual correction is only accepted when anchor quality is preserved.

!!! info "Derivation Walkthrough"
    **Goal:** combine anchor-grounded correction with optional ML residual learning without degrading anchor quality.

    **Step-by-step interpretation:** compute anchor residuals, optimize baseline piecewise objective, fit ridge residual model on normalized features, then apply fail-closed anchor checks.

    **Why this changes operation:** the hybrid path improves predictions without sacrificing bicarbonate-control trust; if anchor fidelity degrades, fail-closed fallback prevents purity decisions from being driven by unstable corrections.

### Optional: Locked Multi-Anchor Example

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


### Optional: Baseline Piecewise Calibration Objective

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

### Optional: Historical Anchors and Cross-Run Learning

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

### Optional: Why Prediction Accuracy Improves Every Run

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

### Optional: Residual ML Ridge Correction Stage

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

### Optional: Fail-Closed Anchor Guard (Apply/Reject Logic)

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

### How Dashboard Values Are Computed
Dashboard metrics follow strict precedence and clamp logic so operator-facing status remains consistent with analysis outputs.

!!! info "Derivation Walkthrough"
    **Goal:** make dashboard KPIs deterministic by strict precedence, gap math, and clamped completion.

    **Step-by-step interpretation:** resolve required CO2 source by precedence, compute target gap, then compute baseline/corrected completion percentages with guardrail clamps.

    **Why this changes operation:** operators receive consistent status semantics even when multiple modeling channels are present.

### Optional: Required CO2 Source Precedence

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

### Optional: Target Gap and Completion

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

### Optional: Corrected vs Baseline pH Channels

- Baseline calculated/equilibrium pH channel remains available.
- Corrected channel is produced by measured-anchor calibration.
- ML-corrected channel is additive and only promoted when anchor guard passes.
