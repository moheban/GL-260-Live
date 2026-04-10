# GL-260 Equilibrium and Simulation Walkthrough (700 g NaOH Case)

## Purpose
This walkthrough traces the exact computational chain from NaOH basis through calibrated pH outputs used in GL-260 Analysis mode.

This standalone technical document is presentation-focused and explains how GL-260 computes:

- equilibrium pH,
- carbonate speciation,
- cycle CO2 uptake,
- measured-pH anchored calibration,
- residual ML pH correction in Analysis mode.

The walkthrough is aligned to the current NaOH-CO2 Pitzer pathway and Analysis calibration contracts in the application.

## Locked Assumptions for This Walkthrough
All values in this document are locked to one deterministic scenario so intermediate results are reproducible during live explanation.

- Temperature: `25 C`
- Water basis: `2,200 mL` pure water (`2.2 kg` water approximation)
- NaOH charge: `700 g`
- NaOH purity: `100%` (for this worked example)
- Synthetic fixed cycle uptake sequence (g CO2 per cycle):
  - `[80, 90, 100, 110, 120, 130, 130, 140]`
  - Total cumulative CO2: `900 g`
- Measured pH anchors (multi-anchor example):
  - Cycle 5: `pH = 9.45`
  - Cycle 8: `pH = 7.95`
- ML correction mode: enabled, with fail-closed anchor guard enforced.

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

Converting mass to molar/molal basis defines the two stoichiometric landmarks used for later interpretation.

!!! info "Derivation Walkthrough"
    **Goal:** translate the charged NaOH mass into concentration terms that drive every later equilibrium equation.

    **Step-by-step interpretation:** first compute \(n_{\mathrm{NaOH}}\), then normalize by liquid volume (\(C_{\mathrm{NaOH}}\)) and water mass (\(m_{\mathrm{NaT}}\)), then convert the two stoichiometric CO2 endpoints to grams.

    **Why this changes operation:** these endpoint masses define where bicarbonate formation can be maximized versus where carbonate carryover or leftover caustic are expected, so they are the first control landmarks for high-purity NaHCO3.

```latex
m_{\mathrm{NaOH}} = 700\ \mathrm{g}
```

```latex
MW_{\mathrm{NaOH}} = 40.00\ \mathrm{g\ mol^{-1}}
```

```latex
n_{\mathrm{NaOH}} = \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}}
```

```latex
n_{\mathrm{NaOH}} = \frac{700\ \mathrm{g}}{40.00\ \mathrm{g\ mol^{-1}}} = 17.5\ \mathrm{mol}
```

```latex
V_{\mathrm{liq}} = 2.200\ \mathrm{L}
```

```latex
kg_{\mathrm{water}} \approx 2.2\ \mathrm{kg}
```

```latex
C_{\mathrm{NaOH}} = \frac{n_{\mathrm{NaOH}}}{V_{\mathrm{liq}}}
```

```latex
C_{\mathrm{NaOH}} = \frac{17.5\ \mathrm{mol}}{2.200\ \mathrm{L}} = 7.9545\ \mathrm{mol\ L^{-1}}
```

```latex
m_{\mathrm{NaT}} = \frac{n_{\mathrm{NaOH}}}{kg_{\mathrm{water}}}
```

```latex
m_{\mathrm{NaT}} = \frac{17.5\ \mathrm{mol}}{2.2\ \mathrm{kg}} = 7.9545\ \mathrm{mol\ kg^{-1}}
```

Stoichiometric landmarks for CO2 addition:

```latex
n_{\mathrm{CO_2,eq1}} = \frac{n_{\mathrm{NaOH}}}{2} = 8.75\ \mathrm{mol}
```

```latex
m_{\mathrm{CO_2,eq1}} = n_{\mathrm{CO_2,eq1}} \times MW_{\mathrm{CO_2}}
```

```latex
m_{\mathrm{CO_2,eq1}} = 8.75\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 385.1\ \mathrm{g}
```

```latex
n_{\mathrm{CO_2,eq2}} = n_{\mathrm{NaOH}} = 17.5\ \mathrm{mol}
```

```latex
m_{\mathrm{CO_2,eq2}} = n_{\mathrm{CO_2,eq2}} \times MW_{\mathrm{CO_2}}
```

```latex
m_{\mathrm{CO_2,eq2}} = 17.5\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} \approx 770.2\ \mathrm{g}
```

!!! tip "Approximation Note"
    Approximation note: \(kg_{\mathrm{water}} \approx 2.2\ \mathrm{kg}\) assumes pure-water density near \(1.0\ \mathrm{kg\ L^{-1}}\).


<div class="inline-chart-anchor" data-inline-chart="stoich-impact"></div>


---

## 2) Equilibrium Half-Reactions, Constants, and Activities
These half-reactions and constants provide the thermodynamic constraints that all downstream pH/speciation calculations must satisfy.

### 2.1 Carbonate and Water Equilibrium Half-Reactions

!!! note "Calculation Legend"
    - \(K_{a1}\), \(K_{a2}\), `K_w`: equilibrium constants in activity form `[-]`
    - `a_i`: activity of species `i` `[-]`
    - \(\gamma_i\): activity coefficient of species `i` `[-]`
    - `m_i`: molality of species `i` [\(mol kg^{-1}\)]
    - `K_H`: Henry constant in the convention used by the model [\(mol kg^{-1} atm^{-1}\)]
    - \(p_{\mathrm{CO_2}}\): CO2 partial pressure [`atm`]
    - \([\mathrm{CO_2^*}]\): dissolved molecular CO2 plus hydrated carbonic acid basis [\(mol kg^{-1}\)]


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

```latex
a_i = \gamma_i \times m_i
```

For fixed-headspace mode, dissolved CO2 boundary is constrained by Henry's law:

```latex
[\mathrm{CO_2^*}] = K_H \times p_{\mathrm{CO_2}}
```

### 2.2 Constants Used by the NaOH-CO2 Pitzer Example Path (25 C)

!!! note "Calculation Legend"
    - \(K_{a1}\): first dissociation constant of carbonic system `[-]`
    - \(K_{a2}\): second dissociation constant of carbonic system `[-]`
    - `K_w`: water autoionization constant `[-]`


In `naoh_co2_pitzer_ph_model.py`:

```latex
K_{a1} = 10^{-6.3374}
```

```latex
K_{a2} = 10^{-10.3393}
```

```latex
K_w \approx 10^{-14}
```

---

## 3) Complete Keq Expression

!!! note "Calculation Legend"
    - \(K_{b1}\), \(K_{b2}\): base-side equilibrium constants `[-]`
    - \(K_{eq,\mathrm{overall}}\): overall equilibrium constant `[-]`
    - \(a_{\mathrm{H_2O}}\): water activity `[-]`, often approximated as `1` in concentrated electrolyte simplifications

The overall equilibrium relationship is explicitly tied to the half-reaction constants, enabling direct inspection of the chemistry contract.

!!! info "Derivation Walkthrough"
    **Goal:** show that the full carbonate neutralization contract is exactly the product of the two base-consumption half steps.

    **Step-by-step interpretation:** define each half reaction, write \(K_{b1}\) and \(K_{b2}\) in activity form, then multiply them to recover the overall expression and map to \({K_{a1}, K_{a2}, K_w}\).

    **Why this changes operation:** this is the control bridge from chemistry theory to bicarbonate purity; if either half-step is unintentionally over-driven, the net pathway shifts away from NaHCO3 and toward carbonate.

GL-260's carbonate neutralization chemistry can be shown in two base-consumption half-steps:

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
<th>Reaction Assembly</th>
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

Operational implication for bicarbonate purity: the \(\mathrm{HCO_3^-}\) term cancels in the algebra because it is an intermediate produced in the first half-step and consumed in the second. This means bicarbonate quality is controlled by how strongly each half-step is driven in practice: we want to favor \(\mathrm{CO_2^*} + \mathrm{OH^-} \rightarrow \mathrm{HCO_3^-}\) while suppressing \(\mathrm{HCO_3^-} + \mathrm{OH^-} \rightarrow \mathrm{CO_3^{2-}} + \mathrm{H_2O}\), achieved by increasing dissolved CO2 (\(p_{\mathrm{CO_2}}\)), reducing effective \(\mathrm{OH^-}\) through loading stage progression, and avoiding excessive residual alkalinity.

The equilibrium constants multiply when reactions are added:

```latex
K_{eq,\mathrm{overall}}
=
\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}}
\times
\frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}}
```

```latex
K_{eq,\mathrm{overall}} = \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
```

```latex
K_{eq,\mathrm{overall}} \approx \frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2}
\quad\text{when}\quad a_{\mathrm{H_2O}} \approx 1
```

In terms of acid and water constants:

```latex
K_{eq,\mathrm{overall}} = \frac{K_{a1} \times K_{a2}}{K_w^2}
```

!!! tip "Approximation Note"
    Approximation note: terms with \(\approx\) follow the common \(a_{\mathrm{H_2O}} \approx 1\) simplification used for interpretability.


---

## 4) Speciation and pH Derivation Used in GL-260

!!! note "Calculation Legend"
    - \([H^+]\), \([\mathrm{OH^-}]\), \([\mathrm{CO_2^*}]\), \([\mathrm{HCO_3^-}]\), \([\mathrm{CO_3^{2-}}]\), \([\mathrm{Na^+}]\): concentration/molarity-like model terms [\(mol L^{-1}\) or model-consistent concentration basis]
    - `C_T`: total inorganic carbon concentration on the same basis as reconstructed species
    - \(\alpha_0\), \(\alpha_1\), \(\alpha_2\): species fractions `[-]`
    - `D`: shared denominator in alpha-fraction identities
    - `R_q`: charge-balance residual on concentration basis (target is zero)

GL-260 solves charge balance to recover `[H+]`, then reconstructs species fractions and pH consistently from that solution.

!!! info "Derivation Walkthrough"
    **Goal:** recover all carbonate species and pH from one consistent solution variable (\([H^+]\)).

    **Step-by-step interpretation:** compute the shared denominator `D`, derive \(\alpha_0/\alpha_1/\alpha_2\), reconstruct species with `C_T`, then close with charge-balance residual `R_q = 0`.

    **Why this changes operation:** bicarbonate-control decisions are only trustworthy when one solved state satisfies both speciation and charge closure; otherwise purity guidance can point to the wrong operating region.

Denominator and alpha fractions:

```latex
D = [H^+]^2 + (K_{a1} \times [H^+]) + (K_{a1} \times K_{a2})
```

```latex
\alpha_0 = \frac{[H^+]^2}{D}
```

```latex
\alpha_1 = \frac{K_{a1} \times [H^+]}{D}
```

```latex
\alpha_2 = \frac{K_{a1} \times K_{a2}}{D}
```

Species reconstruction:

```latex
[\mathrm{CO_2^*}] = \alpha_0 \times C_T
```

```latex
[\mathrm{HCO_3^-}] = \alpha_1 \times C_T
```

```latex
[\mathrm{CO_3^{2-}}] = \alpha_2 \times C_T
```

pH and hydroxide:

```latex
\mathrm{pH} = -\log_{10}([H^+])
```

```latex
[\mathrm{OH^-}] = \frac{K_w}{[H^+]}
```

Charge-balance residual (NaOH reaction path):

```latex
R_q = [\mathrm{Na^+}] + [\mathrm{H^+}] - [\mathrm{OH^-}] - [\mathrm{HCO_3^-}] - (2 \times [\mathrm{CO_3^{2-}}])
```

Solver target:

```latex
R_q = 0
```

---

## 5) Why Bicarbonate Purity Is Hard and Why pCO2 Is the Control Lever

!!! note "Calculation Legend"
    - \(\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}}\): bicarbonate-to-carbonate activity ratio `[-]`
    - \(a_{\mathrm{OH^-}}\): hydroxide activity `[-]`
    - \(K_{a2}\), `K_w`, \(K_{b2}\): equilibrium constants `[-]`
    - \(p_{\mathrm{CO_2}}\): headspace CO2 partial pressure [`atm`]

At high alkalinity, carbonate is strongly favored unless dissolved CO2 is driven high enough to consume free hydroxide and shift the distribution back toward bicarbonate.

!!! info "Derivation Walkthrough"
    **Goal:** make the bicarbonate-to-carbonate ratio dependence explicit in terms of hydroxide activity and pCO2.

    **Step-by-step interpretation:** start with the second base equilibrium, rearrange into \(a_{\mathrm{HCO_3^-}}/a_{\mathrm{CO_3^{2-}}}\), then substitute Henry's law to connect dissolved CO2 directly to \(p_{\mathrm{CO_2}}\).

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

```latex
\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}} = \frac{1}{K_{b2} \times a_{\mathrm{OH^-}}}
```

```latex
\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}} = \frac{K_w}{K_{a2} \times a_{\mathrm{OH^-}}}
```

This ratio increases as `a_OH` drops. In fixed-headspace operation:

```latex
[\mathrm{CO_2^*}] = K_H \times p_{\mathrm{CO_2}}
```

so increasing `pCO2` raises dissolved CO2, which consumes alkalinity, lowers `a_OH`, and therefore raises the bicarbonate-to-carbonate ratio.

Under the locked walkthrough assumptions (25 C, 700 g NaOH, 2,200 mL water), a compact sensitivity sweep is:

| pCO2 (atm) | pH | H2CO3* frac | HCO3- frac | CO3^2- frac |
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
    - `m_i`, `m_j`, `m_k`: species molalities [\(mol kg^{-1}\)]
    - `z_i`: ion charge number `[-]`
    - \(\gamma_i\): activity coefficient `[-]`
    - \(B_{ij}\), \(C_{ij}\), \(\Psi_{ijk}\), `F(I)`, `Z`: Pitzer-model terms used in the focused implementation
    - `r_1`, \(r_{23}\): dimensionless species ratio identities `[-]`
    - \(m_{CT}\): total inorganic carbon molality [\(mol kg^{-1}\)]

The NaOH-focused Pitzer path adds activity corrections at high ionic strength while preserving charge and carbon closures each cycle.

The NaOH Pitzer path uses activity-corrected species balances and charge balance with focused Pitzer interactions (`Na+` with `OH-`, `HCO3-`, \(CO3^2-\), plus selected `THETA/PSI` terms).

Ionic strength:

```latex
I = \frac{1}{2} \sum_i (m_i \times z_i^2)
```

Activity coefficients (schematic Pitzer form used in this focused implementation):

```latex
\ln(\gamma_i) = (z_i^2 \times F(I)) + \sum_j \left(m_j \times (2 \times B_{ij} + Z \times C_{ij})\right) + \sum_{j,k} \left(m_j \times m_k \times \Psi_{ijk}\right) + \cdots
```

The NaOH model path in code also uses activity-corrected ratio identities:

```latex
r_1 = \frac{K_{a1}}{\gamma_{\mathrm{H^+}} \times \gamma_{\mathrm{HCO_3^-}} \times [H^+]}
```

```latex
r_1 = \frac{m_{\mathrm{HCO_3^-}}}{m_{\mathrm{CO_2^*}}}
```

```latex
r_{23} = \frac{K_{a2} \times \gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}} \times \gamma_{\mathrm{CO_3^{2-}}} \times [H^+]}
```

```latex
r_{23} = \frac{m_{\mathrm{CO_3^{2-}}}}{m_{\mathrm{HCO_3^-}}}
```

with total inorganic carbon closure:

```latex
m_{CT} = m_{\mathrm{CO_2^*}} + m_{\mathrm{HCO_3^-}} + m_{\mathrm{CO_3^{2-}}}
```

and charge-balance closure solved iteratively each cycle.

---

## 7) Cycle Uptake Math
Cycle-level uptake is converted into cumulative carbon loading, which becomes the cycle-by-cycle driver of equilibrium state updates.

!!! info "Derivation Walkthrough"
    **Goal:** convert per-cycle CO2 mass events into cumulative loading terms used by the equilibrium solver.

    **Step-by-step interpretation:** define cycle delta mass, accumulate to cumulative mass, then convert cumulative mass to molality (\(m_{CT,k}\)) using molecular weight and water basis.

    **Why this changes operation:** this conversion maps real cycle operation to carbonate chemistry state, so accurate loading is required to keep the process in the bicarbonate-dominant region needed for purer NaHCO3.

### 7.1 Primary (Locked) Synthetic Cycle Uptake Sequence

!!! note "Calculation Legend"
    - \(\Delta m_{\mathrm{CO_2},i}\): CO2 mass uptake during cycle `i` [`g`]
    - \(m_{\mathrm{CO_2,cum},k}\): cumulative CO2 mass through cycle `k` [`g`]
    - \(MW_{\mathrm{CO_2}}\): CO2 molecular weight [\(g mol^{-1}\)]
    - \(m_{CT,k}\): total inorganic carbon molality at cycle `k` [\(mol kg^{-1}\)]
    - \(kg_{\mathrm{water}}\): water mass basis [`kg`]


```latex
\Delta m_{\mathrm{CO_2},i}\ (\mathrm{g}) = [80,90,100,110,120,130,130,140]
```

```latex
m_{\mathrm{CO_2,cum},k} = \sum_{i=1}^{k} \Delta m_{\mathrm{CO_2},i}
```

```latex
m_{CT,k} = \frac{\left(m_{\mathrm{CO_2,cum},k} / MW_{\mathrm{CO_2}}\right)}{kg_{\mathrm{water}}}
```

<div class="inline-chart-anchor" data-inline-chart="uptake-loading"></div>


### 7.2 Operational Reference: Pressure-Derived Uptake

!!! note "Calculation Legend"
    - \(\Delta P_{\mathrm{psi}}\), \(\Delta P_{\mathrm{atm}}\): pressure drop per cycle [`psi`, `atm`]
    - \(V_{\mathrm{headspace}}\): headspace volume [`L`]
    - `R`: ideal gas constant [\(L atm mol^{-1} K^{-1}\)]
    - `T`: absolute temperature [`K`]
    - \(n_{\mathrm{CO_2},i}\): inferred moles of CO2 transferred in cycle `i` [`mol`]


When uptake is inferred from pressure-drop per cycle:

```latex
\Delta P_{\mathrm{atm}} = \frac{\Delta P_{\mathrm{psi}}}{14.6959}
```

```latex
n_{\mathrm{CO_2},i} = \frac{\Delta P_{\mathrm{atm}} \times V_{\mathrm{headspace}}}{R \times T}
```

```latex
\Delta m_{\mathrm{CO_2},i} = n_{\mathrm{CO_2},i} \times MW_{\mathrm{CO_2}}
```

Example (\(\Delta P = 25 psi\), `V_headspace = 15 L`, `T = 298.15 K`):

```latex
\Delta P_{\mathrm{atm}} = \frac{25\ \mathrm{psi}}{14.6959\ \mathrm{psi\ atm^{-1}}} = 1.7012\ \mathrm{atm}
```

```latex
n_{\mathrm{CO_2},i} = \frac{1.7012\ \mathrm{atm} \times 15\ \mathrm{L}}{0.082057\ \mathrm{L\ atm\ mol^{-1}\ K^{-1}} \times 298.15\ \mathrm{K}} = 1.0430\ \mathrm{mol}
```

```latex
\Delta m_{\mathrm{CO_2},i} = 1.0430\ \mathrm{mol} \times 44.01\ \mathrm{g\ mol^{-1}} = 45.90\ \mathrm{g}
```

---

## 8) Worked NaOH-Pitzer Simulation Table (Synthetic Cycles to 900 g)

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

---

## 9) Measured-pH Calibration + Hybrid ML Correction (Analysis Mode)
Measured anchors reshape the baseline simulation, and ML residual correction is only accepted when anchor quality is preserved.

!!! info "Derivation Walkthrough"
    **Goal:** combine anchor-grounded correction with optional ML residual learning without degrading anchor quality.

    **Step-by-step interpretation:** compute anchor residuals, optimize baseline piecewise objective, fit ridge residual model on normalized features, then apply fail-closed anchor checks.

    **Why this changes operation:** the hybrid path improves predictive smoothness without sacrificing bicarbonate-control trust; if anchor fidelity degrades, fail-closed fallback prevents purity decisions from being driven by unstable corrections.

### 9.1 Locked Multi-Anchor Example

!!! note "Calculation Legend"
    - `r_5`, `r_8`: anchor residuals (`measured - baseline`) in pH units


- Anchor A: cycle 5 measured pH = `9.45`
- Anchor B: cycle 8 measured pH = `7.95`

Baseline model at those cycles from the table:

- Cycle 5 baseline pH = `9.6257`
- Cycle 8 baseline pH = `7.8538`

Anchor residuals (`measured - baseline`):

```latex
r_{5} = 9.45 - 9.6257 = -0.1757\ \mathrm{pH}
```

```latex
r_{8} = 7.95 - 7.8538 = +0.0962\ \mathrm{pH}
```

<div class="inline-chart-anchor" data-inline-chart="anchor-residuals"></div>


### 9.2 Baseline Piecewise Calibration Objective

!!! note "Calculation Legend"
    - `J(s)`: objective value used to score scale factor `s` `[-]`
    - \(\hat pH_{\mathrm{anchor}}(s)\): model-predicted pH at an anchor after scale `s`
    - \(pH_{\mathrm{measured}}\): measured anchor pH
    - \(\lambda_{\mathrm{reg}}\), \(\lambda_{\mathrm{smooth}}\), \(w_{\mathrm{term}}\): penalty weights `[-]`
    - \(\Pi_{\mathrm{terminal}}\): terminal-band penalty function `[-]`
    - \(s_{\mathrm{prev}}\): previous segment scale value `[-]`


Per-anchor segment scale search minimizes:

```latex
J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2
```

```latex
J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2
```

```latex
J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2 + \lambda_{\mathrm{smooth}} \times (s - s_{\mathrm{prev}})^2
```

```latex
J(s) = (\hat pH_{\mathrm{anchor}}(s) - pH_{\mathrm{measured}})^2 + \lambda_{\mathrm{reg}} \times (s - 1)^2 + \lambda_{\mathrm{smooth}} \times (s - s_{\mathrm{prev}})^2 + w_{\mathrm{term}} \times \Pi_{\mathrm{terminal}}(pH_{\mathrm{end}}(s))
```

with current defaults shown in code path:

```latex
\lambda_{\mathrm{reg}} = 0.02
```

```latex
\lambda_{\mathrm{smooth}} = 0.01
```

```latex
pH_{\mathrm{terminal\ band}} = [8.0,\ 8.3]
```

```latex
w_{\mathrm{term}} = 1.0
```

This stage outputs:

- corrected cycle uptake series,
- corrected cumulative uptake series,
- corrected pH series,
- corrected fractions series.

### 9.3 Residual ML Ridge Correction Stage

!!! note "Calculation Legend"
    - \(\mathbf{x}\): raw feature vector for one cycle
    - \(\boldsymbol\mu\), \(\boldsymbol\sigma\): feature means and standard deviations
    - \(\mathbf{x}'\): normalized feature vector `[-]`
    - `X'`: normalized design matrix
    - \(\mathbf{y}\): residual target vector (anchor-informed) in pH units
    - \(\boldsymbol\beta\), \(\beta_0\): ridge regression coefficients/intercept
    - \(\hat r\): predicted residual correction in pH units


After baseline anchor calibration, Analysis can learn residual structure using the feature vector:

```latex
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
```

Feature normalization and ridge fit:

```latex
\mathbf{x}' = \frac{\mathbf{x} - \boldsymbol\mu}{\boldsymbol\sigma}
```

```latex
\boldsymbol\beta = \left((X'^T \cdot X') + (\lambda \times I)\right)^{-1} \cdot X'^T \cdot \mathbf{y}
```

```latex
\lambda = 0.35
```

Prediction and corrected pH:

```latex
\hat r = \beta_0 + (\mathbf{x}' \cdot \boldsymbol\beta)
```

```latex
pH_{\mathrm{ML\ corrected}} = \mathrm{clamp}(pH_{\mathrm{baseline\ corrected}} + \hat r,\ 0,\ 14)
```

Fractions are then recomputed from corrected pH using equilibrium-consistent fallback mapping.

### 9.4 Fail-Closed Anchor Guard (Apply/Reject Logic)

!!! note "Calculation Legend"
    - \(\mathrm{MAE}_{\mathrm{ML,anchors}}\), \(\mathrm{MAE}_{\mathrm{baseline,anchors}}\): anchor MAE values in pH units
    - `0.10`: default per-anchor absolute error tolerance in pH units


ML-corrected pH is applied only if anchor quality is not degraded:

```latex
\mathrm{MAE}_{\mathrm{ML,anchors}} \le \mathrm{MAE}_{\mathrm{baseline,anchors}}
```

and each anchor remains within tolerance (`default = 0.10 pH`):

```latex
|pH_{\mathrm{ML,anchor}} - pH_{\mathrm{measured,anchor}}| \le 0.10
```

If either check fails, runtime status is fail-closed to baseline corrected series.

---

## 10) How Dashboard Values Are Computed
Dashboard metrics follow strict precedence and clamp logic so operator-facing status remains consistent with analysis outputs.

!!! info "Derivation Walkthrough"
    **Goal:** make dashboard KPIs deterministic by strict precedence, gap math, and clamped completion.

    **Step-by-step interpretation:** resolve required CO2 source by precedence, compute target gap, then compute baseline/corrected completion percentages with guardrail clamps.

    **Why this changes operation:** operators receive consistent status semantics even when multiple modeling channels are present.

### 10.1 Required CO2 Source Precedence

!!! note "Calculation Legend"
    - Arrow direction indicates strict precedence order for the required CO2 source channel.


```latex
\text{guidance\_model} \rightarrow \text{measured\_ph\_calibration} \rightarrow \text{planning\_reference}
```

### 10.2 Target Gap and Completion

!!! note "Calculation Legend"
    - \(m_{\mathrm{required}}\): required CO2 mass target [`g`]
    - \(m_{\mathrm{uptake}}\): currently achieved CO2 uptake [`g`]
    - \(\Delta m_{\mathrm{target}}\): remaining CO2 mass target gap [`g`]
    - \(C_{\mathrm{required}}\), \(C_{\mathrm{corr}}\): completion percentage [%]
    - \(m_{\mathrm{corrected\ uptake}}\): corrected uptake basis [`g`]
    - \(m_{\mathrm{planning\ reference}}\): planning reference uptake basis [`g`]


```latex
\Delta m_{\mathrm{target}} = \max(m_{\mathrm{required}} - m_{\mathrm{uptake}}, 0)
```

```latex
C_{\mathrm{required}} = \mathrm{clamp}\left(\frac{m_{\mathrm{uptake}}}{m_{\mathrm{required}}}, 0, 1\right)\times 100
```

Corrected planning completion:

```latex
C_{\mathrm{corr}} = \mathrm{clamp}\left(\frac{m_{\mathrm{corrected\ uptake}}}{m_{\mathrm{planning\ reference}}}, 0, 1\right)\times 100
```

### 10.3 Corrected vs Baseline pH Channels

- Baseline calculated/equilibrium pH channel remains available.
- Corrected channel is produced by measured-anchor calibration.
- ML-corrected channel is additive and only promoted when anchor guard passes.

---

## 11) Reproducibility Notes
The artifact is fully regenerable from this markdown source with deterministic build and check commands.

To regenerate the HTML presentation artifact from this Markdown source:

```bash
python scripts/build_equilibrium_walkthrough.py
python scripts/build_equilibrium_walkthrough.py --check
```

This walkthrough is documentation-only and does not change runtime chemistry behavior.

