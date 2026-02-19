use pyo3::prelude::*;
use pyo3::types::PyDict;

const SOL_KA1: f64 = 4.45e-7;
const SOL_KA2: f64 = 4.69e-11;
const SOL_KW: f64 = 1.0e-14;
const SOL_MW_NAOH: f64 = 39.997;
const SOL_MW_CO2: f64 = 44.0095;
const SOL_A_DEBYE: f64 = 0.509;
const SOL_B_DEBYE: f64 = 0.328;
const SOL_DAVIES_LIMIT: f64 = 0.5;
const SOL_DAVIES_COEFF: f64 = 0.3;
const SOL_PKA1_COEFFS: (f64, f64, f64) = (-1.333e-5, -0.008867, 6.58);
const SOL_PKA2_COEFFS: (f64, f64, f64) = (-3.5238e-5, -0.010719, 10.62);
const PLANNING_PLATEAU_CARBONATE_THRESHOLD: f64 = 1e-9;
const PLANNING_PLATEAU_RELATIVE_THRESHOLD: f64 = 0.02;
const PLANNING_PLATEAU_PH_MIN: f64 = 8.0;
const PLANNING_PLATEAU_PH_MAX: f64 = 8.3;

#[derive(Clone, Copy)]
struct LedgerState {
    naoh_remaining_mol: f64,
    na2co3_mol: f64,
    nahco3_mol: f64,
    co2_excess_mol: f64,
}

#[derive(Clone, Copy)]
struct AccountingState {
    co2_consumed_to_carbonate_mol: f64,
    co2_consumed_to_bicarbonate_mol: f64,
    co2_consumed_total_mol: f64,
    co2_unconsumed_mol: f64,
}

fn clamp_temperature(temp_c: f64) -> f64 {
    temp_c.clamp(-5.0, 80.0)
}

fn estimate_temperature_adjusted_pka(temp_c: f64, coeffs: (f64, f64, f64)) -> f64 {
    let (a, b, c) = coeffs;
    let t = clamp_temperature(temp_c);
    (a * t * t + b * t + c).max(0.0)
}

fn carbonate_pkw_from_temp(temp_c: f64) -> f64 {
    14.94 - 0.0137 * clamp_temperature(temp_c)
}

fn basic_carbonate_constants(
    temperature_c: Option<f64>,
    use_temp_adjusted_constants: bool,
) -> (f64, f64, f64) {
    if use_temp_adjusted_constants {
        let t = temperature_c.unwrap_or(25.0);
        let pka1 = estimate_temperature_adjusted_pka(t, SOL_PKA1_COEFFS);
        let pka2 = estimate_temperature_adjusted_pka(t, SOL_PKA2_COEFFS);
        let pkw = carbonate_pkw_from_temp(t);
        (10f64.powf(-pka1), 10f64.powf(-pka2), 10f64.powf(-pkw))
    } else {
        (SOL_KA1, SOL_KA2, SOL_KW)
    }
}

fn resolve_pka2_value(temp_c: Option<f64>, use_temp_adjusted_constants: bool) -> f64 {
    if use_temp_adjusted_constants {
        estimate_temperature_adjusted_pka(temp_c.unwrap_or(25.0), SOL_PKA2_COEFFS).max(0.0)
    } else {
        -SOL_KA2.max(1e-30).log10()
    }
}

fn clamp_ph_value(ph: f64) -> f64 {
    ph.clamp(0.0, 14.3)
}

fn solubility_extended_debye_huckel(ionic_strength: f64, charge: i32, ion_size_nm: f64) -> f64 {
    if ionic_strength <= 1e-12 || charge == 0 {
        return 1.0;
    }
    let sqrt_i = ionic_strength.sqrt();
    let mut denom = 1.0 + SOL_B_DEBYE * ion_size_nm * sqrt_i;
    if denom.abs() <= 1e-18 {
        denom = 1e-12;
    }
    let exponent = -SOL_A_DEBYE * f64::from(charge * charge) * sqrt_i / denom;
    10f64.powf(exponent)
}

fn solubility_activity_coefficient(ionic_strength: f64, charge: i32, ion_size_nm: f64) -> f64 {
    if ionic_strength <= SOL_DAVIES_LIMIT {
        let sqrt_i = ionic_strength.max(1e-12).sqrt();
        let log_gamma = -SOL_A_DEBYE
            * f64::from(charge * charge)
            * ((sqrt_i / (1.0 + sqrt_i)) - SOL_DAVIES_COEFF * ionic_strength);
        return 10f64.powf(log_gamma);
    }
    solubility_extended_debye_huckel(ionic_strength, charge, ion_size_nm)
}

fn solubility_ionic_state(
    na_conc: f64,
    h_conc: f64,
    hco3_conc: f64,
    co3_conc: f64,
    kw_value: f64,
    ionic_strength_cap: Option<f64>,
) -> (f64, [f64; 5], f64) {
    let mut ionic_strength = (0.5 * (na_conc + h_conc + hco3_conc + 4.0 * co3_conc)).max(1e-12);
    if let Some(cap) = ionic_strength_cap {
        ionic_strength = ionic_strength.min(cap);
    }
    let mut gammas = [1.0_f64; 5];
    let mut oh_conc = 1e-7_f64;
    for _ in 0..24 {
        gammas = [
            solubility_activity_coefficient(ionic_strength, 1, 0.90),
            solubility_activity_coefficient(ionic_strength, 1, 0.90),
            solubility_activity_coefficient(ionic_strength, -1, 0.43),
            solubility_activity_coefficient(ionic_strength, -2, 0.40),
            solubility_activity_coefficient(ionic_strength, -1, 0.35),
        ];
        oh_conc = kw_value / (gammas[1] * gammas[4] * h_conc).max(1e-18);
        let mut new_i = 0.5 * (na_conc + h_conc + hco3_conc + 4.0 * co3_conc + oh_conc);
        if let Some(cap) = ionic_strength_cap {
            new_i = new_i.min(cap);
        }
        if (new_i - ionic_strength).abs() < 1e-12 {
            ionic_strength = new_i;
            break;
        }
        ionic_strength = new_i;
    }
    (ionic_strength, gammas, oh_conc)
}

fn solve_linear_system(matrix: &[Vec<f64>], rhs: &[f64]) -> Result<Vec<f64>, String> {
    let n = matrix.len();
    if rhs.len() != n {
        return Err("RHS shape mismatch".to_string());
    }
    let mut aug: Vec<Vec<f64>> = matrix
        .iter()
        .zip(rhs.iter())
        .map(|(row, b)| {
            let mut out = row.clone();
            out.push(*b);
            out
        })
        .collect();
    for col in 0..n {
        let mut pivot_row = col;
        let mut pivot_abs = aug[col][col].abs();
        for row in (col + 1)..n {
            if aug[row][col].abs() > pivot_abs {
                pivot_abs = aug[row][col].abs();
                pivot_row = row;
            }
        }
        if aug[pivot_row][col].abs() < 1e-14 {
            return Err("Singular matrix".to_string());
        }
        if pivot_row != col {
            aug.swap(col, pivot_row);
        }
        let pivot = aug[col][col];
        for j in col..=n {
            aug[col][j] /= pivot;
        }
        for row in 0..n {
            if row == col {
                continue;
            }
            let factor = aug[row][col];
            for j in col..=n {
                aug[row][j] -= factor * aug[col][j];
            }
        }
    }
    Ok((0..n).map(|idx| aug[idx][n]).collect())
}

fn numerical_jacobian<F>(func: &F, point: &[f64], step_scale: f64) -> Vec<Vec<f64>>
where
    F: Fn(&[f64]) -> Vec<f64>,
{
    let n = point.len();
    let mut jacobian = vec![vec![0.0_f64; n]; n];
    for j in 0..n {
        let mut delta = step_scale * point[j].abs().max(1.0);
        delta = delta.max(1e-8);
        let mut forward = point.to_vec();
        let mut backward = point.to_vec();
        forward[j] += delta;
        backward[j] -= delta;
        let fwd = func(&forward);
        let back = func(&backward);
        for i in 0..n {
            jacobian[i][j] = (fwd[i] - back[i]) / (2.0 * delta);
        }
    }
    jacobian
}

fn newton_system_solve<F>(
    func: &F,
    mut x: Vec<f64>,
    tol: f64,
    max_iter: usize,
) -> Result<Vec<f64>, String>
where
    F: Fn(&[f64]) -> Vec<f64>,
{
    for _ in 0..max_iter {
        let residual = func(&x);
        if residual.iter().any(|v| !v.is_finite()) {
            return Err("Non-finite residual".to_string());
        }
        if residual.iter().fold(0.0_f64, |acc, v| acc.max(v.abs())) < tol {
            return Ok(x);
        }
        let jacobian = numerical_jacobian(&func, &x, 1e-6);
        let delta = solve_linear_system(
            &jacobian,
            &residual.iter().map(|value| -*value).collect::<Vec<f64>>(),
        )?;
        if delta.iter().any(|v| !v.is_finite()) {
            return Err("Non-finite Newton increment".to_string());
        }
        x = x
            .iter()
            .zip(delta.iter())
            .map(|(value, step)| (*value + *step).clamp(-25.0, 5.0))
            .collect();
        if delta.iter().fold(0.0_f64, |acc, v| acc.max(v.abs())) < tol {
            if func(&x).iter().fold(0.0_f64, |acc, v| acc.max(v.abs())) < tol {
                return Ok(x);
            }
        }
    }
    Err("Newton solver did not converge".to_string())
}

fn solve_carbonate_state(
    total_carbon_m: f64,
    na_conc: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    initial_ph_guess: f64,
) -> Result<(f64, f64, f64, f64, f64, [f64; 5], f64), String> {
    let total_carbon_m = total_carbon_m.max(1e-16);
    let na_conc = na_conc.max(0.0);
    let residuals = |log_vars: &[f64]| -> Vec<f64> {
        let h = 10f64.powf(log_vars[0]);
        let hco3 = 10f64.powf(log_vars[1]);
        let co3 = 10f64.powf(log_vars[2]);
        let h2co3 = 10f64.powf(log_vars[3]);
        let (_, gammas, oh) = solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
        let ka1_actual = (gammas[1] * gammas[2] * h * hco3) / h2co3.max(1e-16);
        let ka2_actual = (gammas[1] * gammas[3] * h * co3) / (gammas[2] * hco3);
        vec![
            (ka1_actual / ka1).log10(),
            (ka2_actual / ka2).log10(),
            h2co3 + hco3 + co3 - total_carbon_m,
            na_conc + h - hco3 - 2.0 * co3 - oh,
        ]
    };
    let guesses = [
        (initial_ph_guess, 0.85_f64, 0.12_f64),
        (8.8_f64, 0.80_f64, 0.19_f64),
        (7.5_f64, 0.95_f64, 0.03_f64),
        (9.2_f64, 0.70_f64, 0.29_f64),
    ];
    for (ph_guess, hco3_frac, co3_frac) in guesses {
        let h = 10f64.powf(-ph_guess);
        let hco3 = (total_carbon_m * hco3_frac).max(1e-16);
        let co3 = (total_carbon_m * co3_frac).max(1e-16);
        let remainder = total_carbon_m - (hco3 + co3);
        let h2co3 = if remainder > 0.0 {
            remainder
        } else {
            total_carbon_m * 1e-3
        }
        .max(1e-16);
        let guess = vec![h.log10(), hco3.log10(), co3.log10(), h2co3.log10()];
        if let Ok(sol) = newton_system_solve(&residuals, guess, 1e-12, 60) {
            let h = 10f64.powf(sol[0]);
            let hco3 = 10f64.powf(sol[1]);
            let co3 = 10f64.powf(sol[2]);
            let h2co3 = 10f64.powf(sol[3]);
            let (ionic_strength, gammas, oh) =
                solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
            return Ok((h, hco3, co3, h2co3, oh, gammas, ionic_strength));
        }
    }
    Err("Equilibrium solver did not converge".to_string())
}

fn estimate_ledger_ph(
    state: LedgerState,
    pka2_value: f64,
    solution_volume_l: Option<f64>,
    temperature_c: Option<f64>,
    ionic_strength_cap: Option<f64>,
    use_temp_adjusted_constants: bool,
    constants: Option<(f64, f64, f64)>,
    initial_ph_guess: Option<f64>,
) -> f64 {
    let ratio = (state.na2co3_mol / state.nahco3_mol.max(1e-12)).max(1e-12);
    let fallback_ph = clamp_ph_value(pka2_value + ratio.log10());
    let volume = solution_volume_l.unwrap_or(0.0);
    if volume <= 0.0 {
        return fallback_ph;
    }
    let total_na = state.naoh_remaining_mol.max(0.0)
        + state.nahco3_mol.max(0.0)
        + 2.0 * state.na2co3_mol.max(0.0);
    let total_carbon =
        state.nahco3_mol.max(0.0) + state.na2co3_mol.max(0.0) + state.co2_excess_mol.max(0.0);
    let total_na_conc = total_na / volume.max(1e-9);
    let total_carbon_conc = total_carbon / volume.max(1e-9);
    if total_na_conc <= 0.0 && total_carbon_conc <= 0.0 {
        return fallback_ph;
    }
    let (ka1, ka2, kw) = constants
        .unwrap_or_else(|| basic_carbonate_constants(temperature_c, use_temp_adjusted_constants));
    let pkw = -kw.max(1e-30).log10();
    let guess = initial_ph_guess.unwrap_or(fallback_ph);
    if total_carbon_conc <= 1e-12 {
        if total_na_conc <= 0.0 {
            return clamp_ph_value(pkw / 2.0);
        }
        return clamp_ph_value(pkw + total_na_conc.max(1e-16).log10());
    }
    match solve_carbonate_state(
        total_carbon_conc,
        total_na_conc,
        ka1,
        ka2,
        kw,
        ionic_strength_cap,
        guess,
    ) {
        Ok((h, _, _, _, _, _, _)) => {
            let ph = clamp_ph_value(-h.max(1e-30).log10());
            if ph < 6.0 && (state.nahco3_mol > 0.0 || state.co2_excess_mol > 0.0) {
                clamp_ph_value(fallback_ph.max(pka2_value - 2.2).max(8.0))
            } else {
                ph
            }
        }
        Err(_) => {
            if state.nahco3_mol > 0.0 || state.co2_excess_mol > 0.0 {
                clamp_ph_value(fallback_ph.max(pka2_value - 2.2).max(8.0))
            } else {
                fallback_ph
            }
        }
    }
}

fn estimate_ledger_ph_planning(
    state: LedgerState,
    pka2_value: f64,
    solution_volume_l: Option<f64>,
    temperature_c: Option<f64>,
    ionic_strength_cap: Option<f64>,
    use_temp_adjusted_constants: bool,
    constants: Option<(f64, f64, f64)>,
    initial_ph_guess: Option<f64>,
) -> f64 {
    let co3 = state.na2co3_mol.max(0.0);
    let hco3 = state.nahco3_mol.max(0.0);
    let excess = state.co2_excess_mol.max(0.0);
    let carbonate_only_equivalence =
        state.naoh_remaining_mol <= 1e-12 && co3 > 0.0 && hco3 <= 1e-12;
    let carbon_pool = co3 + hco3;
    let carbonate_depleted = co3 <= PLANNING_PLATEAU_CARBONATE_THRESHOLD
        || (carbon_pool > 0.0
            && co3 / carbon_pool.max(1e-12) <= PLANNING_PLATEAU_RELATIVE_THRESHOLD);
    let mut ph_estimate = estimate_ledger_ph(
        LedgerState {
            co2_excess_mol: excess,
            ..state
        },
        pka2_value,
        solution_volume_l,
        temperature_c,
        ionic_strength_cap,
        use_temp_adjusted_constants,
        constants,
        initial_ph_guess,
    );
    if carbonate_only_equivalence && ph_estimate.is_finite() {
        let anchor = if pka2_value.is_finite() {
            pka2_value
        } else {
            10.33
        };
        ph_estimate = clamp_ph_value(ph_estimate.max(anchor - 0.35).min(anchor + 0.35));
    }
    if carbonate_depleted && (hco3 > 0.0 || excess > 0.0) && ph_estimate.is_finite() {
        ph_estimate = ph_estimate
            .max(PLANNING_PLATEAU_PH_MIN)
            .min(PLANNING_PLATEAU_PH_MAX);
    }
    ph_estimate
}

fn simulate_reaction_state_with_accounting_impl(
    ledger: LedgerState,
    delta_mol: f64,
    pka2_value: f64,
    solution_volume_l: Option<f64>,
    temperature_c: Option<f64>,
    ionic_strength_cap: Option<f64>,
    use_temp_adjusted_constants: bool,
    initial_ph_guess: Option<f64>,
    constants: Option<(f64, f64, f64)>,
    planning_mode: bool,
) -> (LedgerState, AccountingState, f64) {
    let mut extra = delta_mol.max(0.0);
    let mut naoh_free = ledger.naoh_remaining_mol.max(0.0);
    let mut co3 = ledger.na2co3_mol.max(0.0);
    let mut hco3 = ledger.nahco3_mol.max(0.0);
    let mut excess = ledger.co2_excess_mol.max(0.0);
    let mut consumed_to_carbonate = 0.0;
    let mut consumed_to_bicarbonate = 0.0;
    if naoh_free > 0.0 {
        let needed = naoh_free / 2.0;
        let consume = extra.min(needed);
        consumed_to_carbonate = consume;
        naoh_free = (naoh_free - consume * 2.0).max(0.0);
        co3 += consume;
        extra -= consume;
    }
    if co3 > 0.0 && extra > 0.0 {
        let convert = extra.min(co3);
        consumed_to_bicarbonate = convert;
        co3 -= convert;
        hco3 += convert * 2.0;
        extra -= convert;
    }
    excess += extra;
    let state = LedgerState {
        naoh_remaining_mol: naoh_free,
        na2co3_mol: co3,
        nahco3_mol: hco3,
        co2_excess_mol: excess,
    };
    let ratio_hint = co3 / hco3.max(1e-12);
    let guess = Some(initial_ph_guess.unwrap_or(pka2_value + ratio_hint.max(1e-12).log10()));
    let ph = if planning_mode {
        estimate_ledger_ph_planning(
            state,
            pka2_value,
            solution_volume_l,
            temperature_c,
            ionic_strength_cap,
            use_temp_adjusted_constants,
            constants,
            guess,
        )
    } else {
        estimate_ledger_ph(
            state,
            pka2_value,
            solution_volume_l,
            temperature_c,
            ionic_strength_cap,
            use_temp_adjusted_constants,
            constants,
            guess,
        )
    };
    let accounting = AccountingState {
        co2_consumed_to_carbonate_mol: consumed_to_carbonate,
        co2_consumed_to_bicarbonate_mol: consumed_to_bicarbonate,
        co2_consumed_total_mol: consumed_to_carbonate + consumed_to_bicarbonate,
        co2_unconsumed_mol: extra.max(0.0),
    };
    (state, accounting, ph)
}

fn dict_float_value(dict: &Bound<'_, PyDict>, key: &str) -> f64 {
    dict.get_item(key)
        .ok()
        .flatten()
        .and_then(|value| value.extract::<f64>().ok())
        .unwrap_or(0.0)
}

#[pyfunction]
#[pyo3(signature = (ledger, delta_mol, pka2_value, solution_volume_l=None, temperature_c=None, ionic_strength_cap=None, use_temp_adjusted_constants=false, initial_ph_guess=None, constants=None, planning_mode=false))]
fn simulate_reaction_state_with_accounting(
    py: Python<'_>,
    ledger: &Bound<'_, PyDict>,
    delta_mol: f64,
    pka2_value: f64,
    solution_volume_l: Option<f64>,
    temperature_c: Option<f64>,
    ionic_strength_cap: Option<f64>,
    use_temp_adjusted_constants: bool,
    initial_ph_guess: Option<f64>,
    constants: Option<(f64, f64, f64)>,
    planning_mode: bool,
) -> PyResult<Py<PyDict>> {
    let input_state = LedgerState {
        naoh_remaining_mol: dict_float_value(ledger, "naoh_remaining_mol"),
        na2co3_mol: dict_float_value(ledger, "na2co3_mol"),
        nahco3_mol: dict_float_value(ledger, "nahco3_mol"),
        co2_excess_mol: dict_float_value(ledger, "co2_excess_mol"),
    };
    let (state, accounting, ph) = simulate_reaction_state_with_accounting_impl(
        input_state,
        delta_mol,
        pka2_value,
        solution_volume_l,
        temperature_c,
        ionic_strength_cap,
        use_temp_adjusted_constants,
        initial_ph_guess,
        constants,
        planning_mode,
    );
    let response = PyDict::new(py);
    let state_dict = PyDict::new(py);
    state_dict.set_item("naoh_remaining_mol", state.naoh_remaining_mol.max(0.0))?;
    state_dict.set_item("na2co3_mol", state.na2co3_mol.max(0.0))?;
    state_dict.set_item("nahco3_mol", state.nahco3_mol.max(0.0))?;
    state_dict.set_item("co2_excess_mol", state.co2_excess_mol.max(0.0))?;
    state_dict.set_item("ph", clamp_ph_value(ph))?;
    let accounting_dict = PyDict::new(py);
    accounting_dict.set_item(
        "co2_consumed_to_carbonate_mol",
        accounting.co2_consumed_to_carbonate_mol,
    )?;
    accounting_dict.set_item(
        "co2_consumed_to_bicarbonate_mol",
        accounting.co2_consumed_to_bicarbonate_mol,
    )?;
    accounting_dict.set_item("co2_consumed_total_mol", accounting.co2_consumed_total_mol)?;
    accounting_dict.set_item("co2_unconsumed_mol", accounting.co2_unconsumed_mol)?;
    response.set_item("state", state_dict)?;
    response.set_item("accounting", accounting_dict)?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (naoh_mass_g, co2_charged_g, solution_volume_l, measured_ph, slurry_ph, target_ph, temperature_c, use_temp_adjusted_constants, ionic_strength_cap=None, constants=None))]
fn analyze_bicarbonate_core(
    py: Python<'_>,
    naoh_mass_g: f64,
    co2_charged_g: f64,
    solution_volume_l: Option<f64>,
    measured_ph: Option<f64>,
    slurry_ph: Option<f64>,
    target_ph: Option<f64>,
    temperature_c: Option<f64>,
    use_temp_adjusted_constants: bool,
    ionic_strength_cap: Option<f64>,
    constants: Option<(f64, f64, f64)>,
) -> PyResult<Option<Py<PyDict>>> {
    if naoh_mass_g <= 0.0 || co2_charged_g < 0.0 {
        return Ok(None);
    }
    let naoh_mol = naoh_mass_g / SOL_MW_NAOH;
    let co2_mol = co2_charged_g / SOL_MW_CO2;
    if naoh_mol <= 0.0 {
        return Ok(None);
    }
    let stage1_co2 = co2_mol.min(naoh_mol / 2.0);
    let naoh_after_stage1 = (naoh_mol - stage1_co2 * 2.0).max(0.0);
    let na2co3_from_stage1 = stage1_co2;
    let co2_after_stage1 = (co2_mol - stage1_co2).max(0.0);
    let stage2_co2 = co2_after_stage1.min(na2co3_from_stage1);
    let na2co3_remaining = (na2co3_from_stage1 - stage2_co2).max(0.0);
    let nahco3_produced = (stage2_co2 * 2.0).max(0.0);
    let co2_excess = (co2_after_stage1 - stage2_co2).max(0.0);
    let buffer_carbon = na2co3_remaining + nahco3_produced;
    let pka2_value = resolve_pka2_value(temperature_c, use_temp_adjusted_constants);
    let measurement_value = measured_ph.or(slurry_ph);
    let ratio_estimate = measurement_value.map(|v| 10f64.powf(v - pka2_value));
    let (co3_current, hco3_current) = if buffer_carbon > 0.0 && ratio_estimate.is_some() {
        let ratio = ratio_estimate.unwrap_or(0.0);
        let frac_co3 = ratio / (1.0 + ratio);
        let co3 = buffer_carbon * frac_co3;
        let hco3 = (buffer_carbon - co3).max(0.0);
        (co3, hco3)
    } else {
        (na2co3_remaining, nahco3_produced)
    };
    let desired_ph = target_ph.unwrap_or(8.0);
    let ratio_target = 10f64.powf(desired_ph - pka2_value);
    let numerator = co3_current - ratio_target * hco3_current;
    let denom = 1.0 + 2.0 * ratio_target;
    let mut co2_for_ratio = 0.0;
    if denom > 0.0 && numerator > 0.0 {
        co2_for_ratio = (numerator / denom).min(co3_current.max(0.0));
    }
    let co2_for_naoh = naoh_after_stage1 / 2.0;
    let total_extra_mol = co2_for_ratio.max(0.0) + co2_for_naoh.max(0.0);
    let total_extra_g = total_extra_mol * SOL_MW_CO2;
    let eq_constants = constants
        .unwrap_or_else(|| basic_carbonate_constants(temperature_c, use_temp_adjusted_constants));
    let initial_guess = measurement_value.unwrap_or(desired_ph);
    let (predicted_state, _, predicted_ph) = simulate_reaction_state_with_accounting_impl(
        LedgerState {
            naoh_remaining_mol: naoh_after_stage1,
            na2co3_mol: na2co3_remaining,
            nahco3_mol: nahco3_produced,
            co2_excess_mol: co2_excess,
        },
        total_extra_mol,
        pka2_value,
        solution_volume_l,
        temperature_c,
        ionic_strength_cap,
        use_temp_adjusted_constants,
        Some(initial_guess),
        Some(eq_constants),
        false,
    );
    let slider_max_g = (total_extra_g * 1.6).max(2.0);
    let rows = pyo3::types::PyList::empty(py);
    let mut step_guess = initial_guess;
    for idx in 0..=12 {
        let delta_g = slider_max_g * (idx as f64 / 12.0);
        let delta_mol = delta_g / SOL_MW_CO2;
        let (state, _, ph) = simulate_reaction_state_with_accounting_impl(
            LedgerState {
                naoh_remaining_mol: naoh_after_stage1,
                na2co3_mol: na2co3_remaining,
                nahco3_mol: nahco3_produced,
                co2_excess_mol: co2_excess,
            },
            delta_mol,
            pka2_value,
            solution_volume_l,
            temperature_c,
            ionic_strength_cap,
            use_temp_adjusted_constants,
            Some(step_guess),
            Some(eq_constants),
            false,
        );
        step_guess = ph;
        let row = PyDict::new(py);
        row.set_item("delta_g", delta_g)?;
        row.set_item("total_co2_g", co2_charged_g + delta_g)?;
        row.set_item("ph", ph)?;
        row.set_item("na2co3_mol", state.na2co3_mol)?;
        row.set_item("nahco3_mol", state.nahco3_mol)?;
        rows.append(row)?;
    }
    let out = PyDict::new(py);
    out.set_item("naoh_mol", naoh_mol)?;
    out.set_item("co2_mol", co2_mol)?;
    out.set_item("stage1_co2", stage1_co2)?;
    out.set_item("naoh_after_stage1", naoh_after_stage1)?;
    out.set_item("na2co3_from_stage1", na2co3_from_stage1)?;
    out.set_item("co2_after_stage1", co2_after_stage1)?;
    out.set_item("stage2_co2", stage2_co2)?;
    out.set_item("na2co3_remaining", na2co3_remaining)?;
    out.set_item("nahco3_produced", nahco3_produced)?;
    out.set_item("co2_excess", co2_excess)?;
    out.set_item("buffer_carbon", buffer_carbon)?;
    out.set_item("pka2_value", pka2_value)?;
    out.set_item("co3_current", co3_current)?;
    out.set_item("hco3_current", hco3_current)?;
    out.set_item("desired_ph", desired_ph)?;
    out.set_item("ratio_target", ratio_target)?;
    out.set_item("co2_for_ratio", co2_for_ratio)?;
    out.set_item("co2_for_naoh", co2_for_naoh)?;
    out.set_item("total_extra_mol", total_extra_mol)?;
    out.set_item("total_extra_g", total_extra_g)?;
    out.set_item("predicted_ph", predicted_ph)?;
    out.set_item("slider_max_g", slider_max_g)?;
    out.set_item("eq_ka1", eq_constants.0)?;
    out.set_item("eq_ka2", eq_constants.1)?;
    out.set_item("eq_kw", eq_constants.2)?;
    out.set_item("simulation_curve", rows)?;
    out.set_item(
        "predicted_ledger_naoh_remaining",
        predicted_state.naoh_remaining_mol,
    )?;
    out.set_item("predicted_ledger_na2co3", predicted_state.na2co3_mol)?;
    out.set_item("predicted_ledger_nahco3", predicted_state.nahco3_mol)?;
    out.set_item(
        "predicted_ledger_co2_excess",
        predicted_state.co2_excess_mol,
    )?;
    Ok(Some(out.unbind()))
}

#[pymodule]
fn gl260_rust_ext(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(
        simulate_reaction_state_with_accounting,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(analyze_bicarbonate_core, module)?)?;
    Ok(())
}
