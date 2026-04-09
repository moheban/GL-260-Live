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
Converting mass to molar/molal basis defines the two stoichiometric landmarks used for later interpretation.

```latex
\begin{aligned}
m_{\mathrm{NaOH}} &= 700\ \mathrm{g} \\
MW_{\mathrm{NaOH}} &= 40.00\ \mathrm{g\ mol^{-1}} \\
n_{\mathrm{NaOH}} &= \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}} = 17.5\ \mathrm{mol} \\
V_{\mathrm{liq}} &= 2.200\ \mathrm{L} \\
kg_{\mathrm{water}} &\approx 2.2\ \mathrm{kg}
\end{aligned}
```

```latex
\begin{aligned}
C_{\mathrm{NaOH}} &\approx \frac{17.5}{2.2} = 7.9545\ \mathrm{mol\ L^{-1}} \\
m_{\mathrm{NaT}} &= \frac{17.5}{2.2} = 7.9545\ \mathrm{mol\ kg^{-1}}
\end{aligned}
```

Stoichiometric landmarks for CO2 addition:

```latex
\begin{aligned}
\text{Stage 1 endpoint (all NaOH to }\mathrm{CO_3^{2-}}\text{): } n_{\mathrm{CO_2,eq1}} &= \frac{n_{\mathrm{NaOH}}}{2} = 8.75\ \mathrm{mol} \\
m_{\mathrm{CO_2,eq1}} &= n_{\mathrm{CO_2,eq1}}\,MW_{\mathrm{CO_2}} \approx 385.1\ \mathrm{g} \\
\text{Stage 2 endpoint (all carbonate to bicarbonate): } n_{\mathrm{CO_2,eq2}} &= n_{\mathrm{NaOH}} = 17.5\ \mathrm{mol} \\
m_{\mathrm{CO_2,eq2}} &= n_{\mathrm{CO_2,eq2}}\,MW_{\mathrm{CO_2}} \approx 770.2\ \mathrm{g}
\end{aligned}
```

---

## 2) Equilibrium Half-Reactions, Constants, and Activities
These half-reactions and constants provide the thermodynamic constraints that all downstream pH/speciation calculations must satisfy.

### 2.1 Carbonate and Water Equilibrium Half-Reactions

```latex
\begin{aligned}
\mathrm{CO_2^*} &\rightleftharpoons \mathrm{H^+} + \mathrm{HCO_3^-} && K_{a1} = \frac{a_{\mathrm{H^+}}a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}} \\
\mathrm{HCO_3^-} &\rightleftharpoons \mathrm{H^+} + \mathrm{CO_3^{2-}} && K_{a2} = \frac{a_{\mathrm{H^+}}a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}} \\
\mathrm{H_2O} &\rightleftharpoons \mathrm{H^+} + \mathrm{OH^-} && K_w = a_{\mathrm{H^+}}a_{\mathrm{OH^-}}
\end{aligned}
```

where:

```latex
a_i = \gamma_i m_i
```

For fixed-headspace mode, dissolved CO2 boundary is constrained by Henry's law:

```latex
[\mathrm{CO_2^*}] = K_H\,p_{\mathrm{CO_2}}
```

### 2.2 Constants Used by the NaOH-CO2 Pitzer Example Path (25 C)

In `naoh_co2_pitzer_ph_model.py`:

```latex
\begin{aligned}
K_{a1} &= 10^{-6.3374} \\
K_{a2} &= 10^{-10.3393} \\
K_w &\approx 10^{-14}
\end{aligned}
```

---

## 3) Complete Keq Expression
The overall equilibrium relationship is explicitly tied to the half-reaction constants, enabling direct inspection of the chemistry contract.

GL-260's carbonate neutralization chemistry can be shown in two base-consumption half-steps:

```latex
\begin{aligned}
\mathrm{CO_2^*} + \mathrm{OH^-} &\rightleftharpoons \mathrm{HCO_3^-} && K_{b1} = \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}a_{\mathrm{OH^-}}} = \frac{K_{a1}}{K_w} \\
\mathrm{HCO_3^-} + \mathrm{OH^-} &\rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O} && K_{b2} = \frac{a_{\mathrm{CO_3^{2-}}}a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}}a_{\mathrm{OH^-}}} \approx \frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}a_{\mathrm{OH^-}}} = \frac{K_{a2}}{K_w}
\end{aligned}
```

Overall equilibrium reaction:

```latex
\mathrm{CO_2^*} + 2\mathrm{OH^-} \rightleftharpoons \mathrm{CO_3^{2-}} + \mathrm{H_2O}
```

Complete equilibrium constant expression:

```latex
K_{eq,\mathrm{overall}} = \frac{a_{\mathrm{CO_3^{2-}}}a_{\mathrm{H_2O}}}{a_{\mathrm{CO_2^*}}a_{\mathrm{OH^-}}^2} \approx \frac{a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{CO_2^*}}a_{\mathrm{OH^-}}^2}
```

In terms of acid and water constants:

```latex
K_{eq,\mathrm{overall}} = K_{b1}K_{b2} = \frac{K_{a1}K_{a2}}{K_w^2}
```

---

## 4) Speciation and pH Derivation Used in GL-260
GL-260 solves charge balance to recover `[H+]`, then reconstructs species fractions and pH consistently from that solution.

Denominator and alpha fractions:

```latex
\begin{aligned}
D &= [H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2} \\
\alpha_0 &= \frac{[H^+]^2}{D} \\
\alpha_1 &= \frac{K_{a1}[H^+]}{D} \\
\alpha_2 &= \frac{K_{a1}K_{a2}}{D}
\end{aligned}
```

Species reconstruction:

```latex
\begin{aligned}
[\mathrm{CO_2^*}] &= \alpha_0 C_T \\
[\mathrm{HCO_3^-}] &= \alpha_1 C_T \\
[\mathrm{CO_3^{2-}}] &= \alpha_2 C_T
\end{aligned}
```

pH and hydroxide:

```latex
\begin{aligned}
\mathrm{pH} &= -\log_{10}[H^+] \\
[\mathrm{OH^-}] &= \frac{K_w}{[H^+]}
\end{aligned}
```

Charge-balance residual (NaOH reaction path):

```latex
R_q = [\mathrm{Na^+}] + [\mathrm{H^+}] - [\mathrm{OH^-}] - [\mathrm{HCO_3^-}] - 2[\mathrm{CO_3^{2-}}]
```

Solver target:

```latex
R_q = 0
```

---

## 5) Why Bicarbonate Purity Is Hard and Why pCO2 Is the Control Lever
At high alkalinity, carbonate is strongly favored unless dissolved CO2 is driven high enough to consume free hydroxide and shift the distribution back toward bicarbonate.

Using the same half-reaction constants:

```latex
\begin{aligned}
\mathrm{CO_2^*} + \mathrm{OH^-} &\rightleftharpoons \mathrm{HCO_3^-} && K_{b1}=\frac{K_{a1}}{K_w} \\
\mathrm{HCO_3^-} + \mathrm{OH^-} &\rightleftharpoons \mathrm{CO_3^{2-}}+\mathrm{H_2O} && K_{b2}=\frac{K_{a2}}{K_w}
\end{aligned}
```

From the second equilibrium:

```latex
\frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_3^{2-}}}}
=\frac{1}{K_{b2}a_{\mathrm{OH^-}}}
=\frac{K_w}{K_{a2}a_{\mathrm{OH^-}}}
```

This ratio increases as `a_OH` drops. In fixed-headspace operation:

```latex
[\mathrm{CO_2^*}] = K_H p_{\mathrm{CO_2}}
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

The trend is the key operational point: higher `pCO2` materially suppresses carbonate fraction and widens the bicarbonate-dominant operating window.

---

## 6) NaOH-CO2 Pitzer (HMW-Focused) Calculation Path
The NaOH-focused Pitzer path adds activity corrections at high ionic strength while preserving charge and carbon closures each cycle.

The NaOH Pitzer path uses activity-corrected species balances and charge balance with focused Pitzer interactions (`Na+` with `OH-`, `HCO3-`, `CO3^2-`, plus selected `THETA/PSI` terms).

Ionic strength:

```latex
I = \frac{1}{2}\sum_i m_i z_i^2
```

Activity coefficients (schematic Pitzer form used in this focused implementation):

```latex
\ln\gamma_i = z_i^2F(I) + \sum_j m_j\big(2B_{ij}+ZC_{ij}\big) + \sum_{j,k} m_jm_k\,\Psi_{ijk} + \cdots
```

The NaOH model path in code also uses activity-corrected ratio identities:

```latex
\begin{aligned}
r_1 &= \frac{K_{a1}}{\gamma_{\mathrm{H^+}}\gamma_{\mathrm{HCO_3^-}}[H^+]} = \frac{m_{\mathrm{HCO_3^-}}}{m_{\mathrm{CO_2^*}}} \\
r_{23} &= \frac{K_{a2}\gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}}\gamma_{\mathrm{CO_3^{2-}}}[H^+]} = \frac{m_{\mathrm{CO_3^{2-}}}}{m_{\mathrm{HCO_3^-}}}
\end{aligned}
```

with total inorganic carbon closure:

```latex
m_{CT} = m_{\mathrm{CO_2^*}} + m_{\mathrm{HCO_3^-}} + m_{\mathrm{CO_3^{2-}}}
```

and charge-balance closure solved iteratively each cycle.

---

## 7) Cycle Uptake Math
Cycle-level uptake is converted into cumulative carbon loading, which becomes the cycle-by-cycle driver of equilibrium state updates.

### 7.1 Primary (Locked) Synthetic Cycle Uptake Sequence

```latex
\Delta m_{\mathrm{CO_2},i}\ (\mathrm{g}) = [80,90,100,110,120,130,130,140]
```

```latex
m_{\mathrm{CO_2,cum},k} = \sum_{i=1}^{k}\Delta m_{\mathrm{CO_2},i}
```

```latex
m_{CT,k} = \frac{m_{\mathrm{CO_2,cum},k}/MW_{\mathrm{CO_2}}}{kg_{\mathrm{water}}}
```

### 7.2 Operational Reference: Pressure-Derived Uptake

When uptake is inferred from pressure-drop per cycle:

```latex
\begin{aligned}
\Delta P_{\mathrm{atm}} &= \frac{\Delta P_{\mathrm{psi}}}{14.6959} \\
n_{\mathrm{CO_2},i} &= \frac{\Delta P_{\mathrm{atm}}\,V_{\mathrm{headspace}}}{R\,T} \\
\Delta m_{\mathrm{CO_2},i} &= n_{\mathrm{CO_2},i}\,MW_{\mathrm{CO_2}}
\end{aligned}
```

Example (`\Delta P = 25 psi`, `V_headspace = 15 L`, `T = 298.15 K`):

```latex
\begin{aligned}
\Delta P_{\mathrm{atm}} &= 1.7012 \\
n_{\mathrm{CO_2},i} &= 1.0430\ \mathrm{mol} \\
\Delta m_{\mathrm{CO_2},i} &= 45.90\ \mathrm{g}
\end{aligned}
```

---

## 8) Worked NaOH-Pitzer Simulation Table (Synthetic Cycles to 900 g)
The worked table is the concrete numerical bridge between theory and the dashboard-facing channels used in the app.

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

Interpretation:

- Around `~385 g` cumulative CO2, the system approaches Stage-1 equivalence (NaOH mostly consumed).
- By late cycles, bicarbonate dominates and pH approaches the bicarbonate-buffer region.

---

## 9) Measured-pH Calibration + Hybrid ML Correction (Analysis Mode)
Measured anchors reshape the baseline simulation, and ML residual correction is only accepted when anchor quality is preserved.

### 9.1 Locked Multi-Anchor Example

- Anchor A: cycle 5 measured pH = `9.45`
- Anchor B: cycle 8 measured pH = `7.95`

Baseline model at those cycles from the table:

- Cycle 5 baseline pH = `9.6257`
- Cycle 8 baseline pH = `7.8538`

Anchor residuals (`measured - baseline`):

```latex
\begin{aligned}
r_{5} &= 9.45 - 9.6257 = -0.1757 \\
r_{8} &= 7.95 - 7.8538 = +0.0962
\end{aligned}
```

### 9.2 Baseline Piecewise Calibration Objective

Per-anchor segment scale search minimizes:

```latex
J(s) = \underbrace{(\hat pH_{\mathrm{anchor}}(s)-pH_{\mathrm{measured}})^2}_{\text{anchor fit}} + \lambda_{\mathrm{reg}}(s-1)^2 + \lambda_{\mathrm{smooth}}(s-s_{\mathrm{prev}})^2 + w_{\mathrm{term}}\,\Pi_{\mathrm{terminal}}\big(pH_{\mathrm{end}}(s)\big)
```

with current defaults shown in code path:

```latex
\lambda_{\mathrm{reg}}=0.02,\quad \lambda_{\mathrm{smooth}}=0.01,\quad pH_{\mathrm{terminal\ band}}=[8.0,8.3],\quad w_{\mathrm{term}}=1.0
```

This stage outputs:

- corrected cycle uptake series,
- corrected cumulative uptake series,
- corrected pH series,
- corrected fractions series.

### 9.3 Residual ML Ridge Correction Stage

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
\mathbf{x}' = \frac{\mathbf{x}-\boldsymbol\mu}{\boldsymbol\sigma}
```

```latex
\boldsymbol\beta = (X'^TX' + \lambda I)^{-1}X'^T\mathbf{y},\quad \lambda=0.35
```

Prediction and corrected pH:

```latex
\hat r = \beta_0 + \mathbf{x}'\cdot\boldsymbol\beta
```

```latex
pH_{\mathrm{ML\ corrected}} = \mathrm{clamp}(pH_{\mathrm{baseline\ corrected}} + \hat r,\ 0,\ 14)
```

Fractions are then recomputed from corrected pH using equilibrium-consistent fallback mapping.

### 9.4 Fail-Closed Anchor Guard (Apply/Reject Logic)

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

### 10.1 Required CO2 Source Precedence

```latex
\text{guidance\_model} \rightarrow \text{measured\_ph\_calibration} \rightarrow \text{planning\_reference}
```

### 10.2 Target Gap and Completion

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

