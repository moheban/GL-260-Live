use numpy::PyReadonlyArray1;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList, PyString};
use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

const SOL_KA1: f64 = 4.45e-7;
const SOL_KA2: f64 = 4.69e-11;
const SOL_KW: f64 = 1.0e-14;
const SOL_MW_NAOH: f64 = 39.997;
const SOL_MW_CO2: f64 = 44.0095;
const SOL_A_DEBYE: f64 = 0.509;
const SOL_B_DEBYE: f64 = 0.328;
const SOL_DAVIES_LIMIT: f64 = 0.5;
const SOL_DAVIES_COEFF: f64 = 0.3;
const CYCLE_GAS_CONSTANT: f64 = 0.082057338;
const SOL_PKA1_COEFFS: (f64, f64, f64) = (-1.333e-5, -0.008867, 6.58);
const SOL_PKA2_COEFFS: (f64, f64, f64) = (-3.5238e-5, -0.010719, 10.62);
const PLANNING_PLATEAU_CARBONATE_THRESHOLD: f64 = 1e-9;
const PLANNING_PLATEAU_RELATIVE_THRESHOLD: f64 = 0.02;
const PLANNING_PLATEAU_PH_MIN: f64 = 8.0;
const PLANNING_PLATEAU_PH_MAX: f64 = 8.3;
const SPEC_MODE_FIXED_PCO2: &str = "fixed_pco2";
const SPEC_MODE_CLOSED: &str = "closed_carbon";
const AQION_DEFAULT_PH_LOW: f64 = 2.0;
const AQION_DEFAULT_PH_HIGH: f64 = 12.5;
const PITZER_A_PHI_25C: f64 = 0.392;
const PITZER_B_DH: f64 = 1.2;
const PITZER_ALPHA_B1: f64 = 2.0;
const PITZER_KA1: f64 = 4.5983285677e-7;
const PITZER_KA2: f64 = 4.5782552279169414e-11;
const PITZER_KW: f64 = 1e-14;
const RUST_BACKEND_INTERFACE_ID: &str = "gl260_rust_backend";
const RUST_BACKEND_INTERFACE_VERSION: &str = "2";
const RUST_BACKEND_MODULE_NAME: &str = env!("CARGO_PKG_NAME");
const RUST_BACKEND_CRATE_VERSION: &str = env!("CARGO_PKG_VERSION");
const RUST_EXPORTED_KERNELS: [&str; 23] = [
    "simulate_reaction_state_with_accounting",
    "analyze_bicarbonate_core",
    "carbonate_state_core",
    "forced_ph_distribution_core",
    "aqion_closed_speciation_core",
    "pitzer_solve_total_carbon_core",
    "combined_decimation_indices",
    "combined_required_indices",
    "cycle_detect_markers_core",
    "cycle_manual_snap_core",
    "cycle_overlay_points_core",
    "cycle_segmentation_core",
    "cycle_metrics_core",
    "array_signature_core",
    "analysis_interpolate_reference_series_core",
    "analysis_dashboard_core",
    "measured_ph_uptake_calibration_core",
    "final_report_cycle_stats_rows_core",
    "final_report_cycle_timeline_rows_core",
    "cycle_timeline_normalize_core",
    "compare_aligned_cycle_rows_core",
    "ledger_sort_filter_indices_core",
    "ledger_prefill_metrics_core",
];

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

fn normalize_speciation_mode(mode: &str) -> &str {
    let token = mode.trim().to_ascii_lowercase();
    if token == SPEC_MODE_FIXED_PCO2 {
        SPEC_MODE_FIXED_PCO2
    } else {
        SPEC_MODE_CLOSED
    }
}

fn solve_carbonate_state_open(
    na_conc: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    initial_ph_guess: f64,
    fixed_h2co3: f64,
) -> Result<(f64, f64, f64, f64, f64, [f64; 5], f64), String> {
    let na_conc = na_conc.max(0.0);
    let fixed_h2co3 = fixed_h2co3.max(1e-16);
    let residuals = |log_vars: &[f64]| -> Vec<f64> {
        let h = 10f64.powf(log_vars[0]);
        let hco3 = 10f64.powf(log_vars[1]);
        let co3 = 10f64.powf(log_vars[2]);
        let (_, gammas, oh) = solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
        let ka1_actual = (gammas[1] * gammas[2] * h * hco3) / fixed_h2co3.max(1e-16);
        let ka2_actual = (gammas[1] * gammas[3] * h * co3) / (gammas[2] * hco3.max(1e-16));
        vec![
            (ka1_actual / ka1.max(1e-30)).log10(),
            (ka2_actual / ka2.max(1e-30)).log10(),
            na_conc + h - hco3 - 2.0 * co3 - oh,
        ]
    };
    let guess_ph_values = [initial_ph_guess, 8.2, 7.8, 9.0];
    for ph_guess in guess_ph_values {
        let h = 10f64.powf(-ph_guess);
        let hco3_guess = ((ka1 * fixed_h2co3) / h.max(1e-16)).max(1e-16);
        let co3_guess = ((ka2 * hco3_guess) / h.max(1e-16)).max(1e-16);
        let guess = vec![h.log10(), hco3_guess.log10(), co3_guess.log10()];
        if let Ok(sol) = newton_system_solve(&residuals, guess, 1e-12, 60) {
            let h = 10f64.powf(sol[0]);
            let hco3 = 10f64.powf(sol[1]);
            let co3 = 10f64.powf(sol[2]);
            let (ionic_strength, gammas, oh) =
                solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
            return Ok((h, hco3, co3, fixed_h2co3, oh, gammas, ionic_strength));
        }
    }
    Err("Fixed-pCO2 equilibrium solver did not converge".to_string())
}

fn solve_carbonate_state_with_mode(
    total_carbon_m: f64,
    na_conc: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    initial_ph_guess: f64,
    speciation_mode: &str,
    fixed_h2co3: Option<f64>,
) -> Result<(f64, f64, f64, f64, f64, [f64; 5], f64), String> {
    let mode = normalize_speciation_mode(speciation_mode);
    if mode == SPEC_MODE_FIXED_PCO2 {
        return solve_carbonate_state_open(
            na_conc,
            ka1,
            ka2,
            kw,
            ionic_strength_cap,
            initial_ph_guess,
            fixed_h2co3.unwrap_or(0.0),
        );
    }
    solve_carbonate_state(
        total_carbon_m,
        na_conc,
        ka1,
        ka2,
        kw,
        ionic_strength_cap,
        initial_ph_guess,
    )
}

fn forced_ph_distribution_impl(
    mut total_carbon_m: f64,
    na_conc: f64,
    forced_ph: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    fixed_h2co3: Option<f64>,
    max_iter: usize,
) -> Result<(f64, f64, f64, f64, f64, f64, f64, [f64; 5], f64), String> {
    if !(0.0..14.5).contains(&forced_ph) {
        return Err("Forced pH must be between 0 and 14.5".to_string());
    }
    total_carbon_m = total_carbon_m.max(1e-16);
    let na_conc = na_conc.max(0.0);
    let fixed_h2co3_value = fixed_h2co3.map(|value| value.max(1e-16));
    let h = 10f64.powf(-forced_ph);
    let mut hco3 = (total_carbon_m * 0.9).max(1e-16);
    let mut co3 = (total_carbon_m * 0.05).max(1e-16);
    let mut h2co3 = (total_carbon_m - hco3 - co3).max(0.0);
    let mut charge_residual = 0.0_f64;
    let mut gammas = [1.0_f64; 5];
    let mut ionic_strength = 0.0_f64;
    let mut oh = 1e-7_f64;
    for _ in 0..max_iter.max(1) {
        let (next_i, next_gammas, next_oh) =
            solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
        ionic_strength = next_i;
        gammas = next_gammas;
        oh = next_oh;
        let coeff_co3 = (ka2 * gammas[2]) / (gammas[1] * gammas[3] * h.max(1e-18));
        let coeff_h2co3 = (gammas[1] * gammas[2] * h) / ka1.max(1e-30);
        let mut denominator = 1.0 + coeff_co3 + coeff_h2co3;
        if !denominator.is_finite() || denominator <= 0.0 {
            denominator = 1e-12;
        }
        let alpha_hco3 = 1.0 / denominator;
        let alpha_co3 = coeff_co3 / denominator;
        hco3 = (total_carbon_m * alpha_hco3).max(1e-16);
        co3 = (total_carbon_m * alpha_co3).max(1e-16);
        h2co3 = (total_carbon_m - hco3 - co3).max(fixed_h2co3_value.unwrap_or(0.0));
        charge_residual = na_conc + h - hco3 - 2.0 * co3 - oh;
        let denom_charge = (alpha_hco3 + 2.0 * alpha_co3).max(1e-12);
        let mut next_total = ((na_conc + h - oh) / denom_charge).max(1e-16);
        if let Some(boundary) = fixed_h2co3_value {
            next_total = next_total.max(boundary + hco3 + co3);
        }
        let delta_ct = ((next_total - total_carbon_m) / total_carbon_m.max(1e-12)).abs();
        total_carbon_m = next_total;
        if delta_ct < 1e-8 && charge_residual.abs() < 1e-8 {
            break;
        }
    }
    let (final_i, final_gammas, final_oh) =
        solubility_ionic_state(na_conc, h, hco3, co3, kw, ionic_strength_cap);
    Ok((
        total_carbon_m,
        h,
        hco3,
        co3,
        h2co3,
        final_oh,
        charge_residual,
        final_gammas,
        final_i,
    ))
}

fn aqion_alpha_fractions(h_conc: f64, ka1: f64, ka2: f64) -> (f64, f64, f64) {
    let mut denom = (h_conc * h_conc) + (ka1 * h_conc) + (ka1 * ka2);
    if denom <= 0.0 || !denom.is_finite() {
        denom = 1e-30;
    }
    let a0 = (h_conc * h_conc) / denom;
    let a1 = (ka1 * h_conc) / denom;
    let a2 = (ka1 * ka2) / denom;
    (a0, a1, a2)
}

fn aqion_species_from_ph(
    ct: f64,
    ph: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
) -> (f64, f64, f64, f64, f64, f64, f64, f64, f64) {
    let h = 10f64.powf(-ph);
    let (a0, a1, a2) = aqion_alpha_fractions(h, ka1, ka2);
    let h2co3 = ct * a0;
    let hco3 = ct * a1;
    let co3 = ct * a2;
    let oh = kw / h.max(1e-30);
    let ionic_strength = 0.5 * (h + hco3 + 4.0 * co3 + oh);
    (h, h2co3, hco3, co3, oh, a0, a1, a2, ionic_strength)
}

fn aqion_charge_balance_residual(ct: f64, ph: f64, ka1: f64, ka2: f64, kw: f64) -> f64 {
    let (h, _h2co3, hco3, co3, oh, _a0, _a1, _a2, _ionic_strength) =
        aqion_species_from_ph(ct, ph, ka1, ka2, kw);
    h - hco3 - 2.0 * co3 - oh
}

fn solve_aqion_closed_speciation(
    total_inorganic_carbon_m: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ph_low: f64,
    ph_high: f64,
) -> Result<(f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, String), String> {
    let ct = total_inorganic_carbon_m.max(0.0);
    let low = ph_low.min(ph_high);
    let high = ph_low.max(ph_high);
    let mut f_low = aqion_charge_balance_residual(ct, low, ka1, ka2, kw);
    let mut f_high = aqion_charge_balance_residual(ct, high, ka1, ka2, kw);
    let mut solver = "bisection-charge-balance".to_string();
    let ph_root = if f_low.abs() < 1e-14 {
        solver = "bracket-bound".to_string();
        low
    } else if f_high.abs() < 1e-14 {
        solver = "bracket-bound".to_string();
        high
    } else if f_low * f_high > 0.0 {
        // Fall back to a dense residual scan when the bracket does not straddle.
        solver = "scan-min-residual".to_string();
        let mut best_ph = low;
        let mut best_residual = f_low.abs();
        let scan_steps = 480usize;
        for idx in 0..=scan_steps {
            let ph = low + (high - low) * (idx as f64 / scan_steps as f64);
            let residual = aqion_charge_balance_residual(ct, ph, ka1, ka2, kw).abs();
            if residual < best_residual {
                best_residual = residual;
                best_ph = ph;
            }
        }
        best_ph
    } else {
        let mut lo = low;
        let mut hi = high;
        let mut mid = 0.5 * (lo + hi);
        for _ in 0..220 {
            mid = 0.5 * (lo + hi);
            let f_mid = aqion_charge_balance_residual(ct, mid, ka1, ka2, kw);
            if f_mid.abs() < 1e-14 || (hi - lo).abs() < 1e-6 {
                break;
            }
            if f_low * f_mid <= 0.0 {
                hi = mid;
                f_high = f_mid;
            } else {
                lo = mid;
                f_low = f_mid;
            }
        }
        mid
    };
    let (h, h2co3, hco3, co3, oh, a0, a1, a2, ionic_strength) =
        aqion_species_from_ph(ct, ph_root, ka1, ka2, kw);
    let residual = aqion_charge_balance_residual(ct, ph_root, ka1, ka2, kw);
    Ok((
        ph_root,
        h,
        oh,
        h2co3,
        hco3,
        co3,
        a0,
        a1,
        a2,
        ionic_strength,
        residual,
        solver,
    ))
}

#[derive(Clone, Copy)]
struct PitzerParamsLite {
    b0_na_oh: f64,
    b1_na_oh: f64,
    c0_na_oh: f64,
    b0_na_hco3: f64,
    b1_na_hco3: f64,
    c0_na_hco3: f64,
    b0_na_co3: f64,
    b1_na_co3: f64,
    c0_na_co3: f64,
    theta_co3_oh: f64,
    psi_co3_na_oh: f64,
    psi_co3_hco3_na: f64,
}

fn pitzer_g(x: f64) -> f64 {
    if x.abs() <= 1e-18 {
        return 0.0;
    }
    2.0 * (1.0 - (1.0 + x) * (-x).exp()) / (x * x)
}

fn pitzer_g_prime(x: f64) -> f64 {
    let h = 1e-6;
    (pitzer_g(x + h) - pitzer_g(x - h)) / (2.0 * h)
}

fn pitzer_b(beta0: f64, beta1: f64, ionic_strength: f64) -> f64 {
    beta0 + beta1 * pitzer_g(PITZER_ALPHA_B1 * ionic_strength.max(0.0).sqrt())
}

fn pitzer_b_prime(beta1: f64, ionic_strength: f64) -> f64 {
    if ionic_strength <= 0.0 {
        return 0.0;
    }
    let x = PITZER_ALPHA_B1 * ionic_strength.sqrt();
    beta1 * pitzer_g_prime(x) * PITZER_ALPHA_B1 / (2.0 * ionic_strength.sqrt())
}

fn pitzer_gamma_set(
    na: f64,
    h: f64,
    oh: f64,
    hco3: f64,
    co3: f64,
    params: PitzerParamsLite,
) -> ([f64; 5], f64) {
    let ionic_strength = 0.5 * (na + h + oh + hco3 + 4.0 * co3);
    if ionic_strength <= 1e-30 {
        return ([1.0_f64; 5], 0.0);
    }
    let sqrt_i = ionic_strength.sqrt();
    let f = -PITZER_A_PHI_25C
        * (sqrt_i / (1.0 + PITZER_B_DH * sqrt_i)
            + (2.0 / PITZER_B_DH) * (1.0 + PITZER_B_DH * sqrt_i).ln());
    let z_sum = na + h + oh + hco3 + 2.0 * co3;
    let mut f_term = f;
    let bprime_na_oh = pitzer_b_prime(params.b1_na_oh, ionic_strength);
    let bprime_na_hco3 = pitzer_b_prime(params.b1_na_hco3, ionic_strength);
    let bprime_na_co3 = pitzer_b_prime(params.b1_na_co3, ionic_strength);
    f_term += na * oh * bprime_na_oh;
    f_term += na * hco3 * bprime_na_hco3;
    f_term += na * co3 * bprime_na_co3;
    let mut ln_gamma = [
        f_term,      // Na+ charge^2
        f_term,      // H+ charge^2
        f_term,      // OH- charge^2
        f_term,      // HCO3- charge^2
        4.0 * f_term, // CO3^2- charge^2
    ];

    let b_na_oh = pitzer_b(params.b0_na_oh, params.b1_na_oh, ionic_strength);
    let b_na_hco3 = pitzer_b(params.b0_na_hco3, params.b1_na_hco3, ionic_strength);
    let b_na_co3 = pitzer_b(params.b0_na_co3, params.b1_na_co3, ionic_strength);

    ln_gamma[0] += oh * (2.0 * b_na_oh + z_sum * params.c0_na_oh);
    ln_gamma[2] += na * (2.0 * b_na_oh + z_sum * params.c0_na_oh);
    ln_gamma[0] += hco3 * (2.0 * b_na_hco3 + z_sum * params.c0_na_hco3);
    ln_gamma[3] += na * (2.0 * b_na_hco3 + z_sum * params.c0_na_hco3);
    ln_gamma[0] += co3 * (2.0 * b_na_co3 + z_sum * params.c0_na_co3);
    ln_gamma[4] += na * (2.0 * b_na_co3 + z_sum * params.c0_na_co3);

    ln_gamma[4] += oh * (2.0 * params.theta_co3_oh);
    ln_gamma[2] += co3 * (2.0 * params.theta_co3_oh);

    if na > 0.0 && co3 > 0.0 && oh > 0.0 {
        ln_gamma[0] += co3 * oh * params.psi_co3_na_oh;
        ln_gamma[4] += na * oh * params.psi_co3_na_oh;
        ln_gamma[2] += na * co3 * params.psi_co3_na_oh;
    }
    if na > 0.0 && co3 > 0.0 && hco3 > 0.0 {
        ln_gamma[0] += co3 * hco3 * params.psi_co3_hco3_na;
        ln_gamma[4] += na * hco3 * params.psi_co3_hco3_na;
        ln_gamma[3] += na * co3 * params.psi_co3_hco3_na;
    }

    let mut gammas = [1.0_f64; 5];
    for idx in 0..5 {
        gammas[idx] = ln_gamma[idx].exp().max(1e-18);
    }
    (gammas, ionic_strength)
}

fn pitzer_find_root_bisect_on_log10<F>(
    fun: F,
    lo: f64,
    hi: f64,
    nscan: usize,
) -> Result<f64, String>
where
    F: Fn(f64) -> f64,
{
    let points = nscan.max(32);
    let mut x_prev = lo;
    let mut f_prev = fun(x_prev);
    if f_prev.abs() < 1e-16 {
        return Ok(x_prev);
    }
    for idx in 1..points {
        let x_curr = lo + (hi - lo) * (idx as f64 / (points - 1) as f64);
        let f_curr = fun(x_curr);
        if f_curr.abs() < 1e-16 {
            return Ok(x_curr);
        }
        if f_prev * f_curr < 0.0 {
            let mut a = x_prev;
            let mut b = x_curr;
            let mut fa = f_prev;
            for _ in 0..100 {
                let mid = 0.5 * (a + b);
                let f_mid = fun(mid);
                if fa * f_mid <= 0.0 {
                    b = mid;
                } else {
                    a = mid;
                    fa = f_mid;
                }
            }
            return Ok(0.5 * (a + b));
        }
        x_prev = x_curr;
        f_prev = f_curr;
    }
    Err("No sign change found while bracketing Pitzer root.".to_string())
}

fn solve_pitzer_total_carbon_impl(
    total_carbon_m: f64,
    total_sodium_m: f64,
    params: PitzerParamsLite,
    max_iter: usize,
) -> Result<(f64, f64, f64, f64, f64, f64, f64), String> {
    if total_sodium_m <= 0.0 {
        return Err("Total sodium molality must be positive.".to_string());
    }
    let ct = total_carbon_m.min(total_sodium_m).max(0.0);
    if ct <= 0.5 * total_sodium_m {
        let m_oh = (total_sodium_m - 2.0 * ct).max(0.0);
        let m_co3 = ct.max(0.0);
        let (gammas, _ionic_strength) =
            pitzer_gamma_set(total_sodium_m, 1e-16, m_oh, 0.0, m_co3, params);
        let a_oh = if m_oh > 0.0 {
            gammas[2] * m_oh
        } else {
            1e-30
        };
        let a_h = PITZER_KW / a_oh.max(1e-30);
        let ph = -a_h.max(1e-30).log10();
        let h = a_h / gammas[1].max(1e-30);
        return Ok((ph, total_sodium_m, h, m_oh, 0.0, m_co3, 0.0));
    }

    let mut h = 1e-16_f64;
    let mut oh = total_sodium_m.max(1e-12);
    let mut hco3 = 0.0_f64;
    let mut co3 = 0.0_f64;
    let mut co2 = 0.0_f64;
    let mut gammas = pitzer_gamma_set(total_sodium_m, h, oh, hco3, co3, params).0;
    for _ in 0..max_iter.max(1) {
        let root = pitzer_find_root_bisect_on_log10(
            |log10_h| {
                let m_h = 10f64.powf(log10_h);
                let a_h = gammas[1] * m_h;
                let m_oh = PITZER_KW / (a_h.max(1e-30) * gammas[2].max(1e-30));
                let r1 = PITZER_KA1 / (gammas[1] * gammas[3] * m_h.max(1e-30));
                let r23 = PITZER_KA2 * gammas[3] / (gammas[1] * gammas[4] * m_h.max(1e-30));
                let r2 = r1 * r23;
                let m_co2 = ct / (1.0 + r1 + r2);
                let m_hco3 = r1 * m_co2;
                let m_co3 = r2 * m_co2;
                (total_sodium_m + m_h) - (m_oh + m_hco3 + 2.0 * m_co3)
            },
            -18.0,
            0.0,
            260,
        )?;
        h = 10f64.powf(root);
        let a_h = gammas[1] * h;
        oh = PITZER_KW / (a_h.max(1e-30) * gammas[2].max(1e-30));
        let r1 = PITZER_KA1 / (gammas[1] * gammas[3] * h.max(1e-30));
        let r23 = PITZER_KA2 * gammas[3] / (gammas[1] * gammas[4] * h.max(1e-30));
        let r2 = r1 * r23;
        co2 = ct / (1.0 + r1 + r2);
        hco3 = r1 * co2;
        co3 = r2 * co2;

        let next_gammas = pitzer_gamma_set(total_sodium_m, h, oh, hco3, co3, params).0;
        let mut max_delta = 0.0_f64;
        for idx in 0..5 {
            let delta = (next_gammas[idx] / gammas[idx].max(1e-30)).ln().abs();
            if delta > max_delta {
                max_delta = delta;
            }
        }
        gammas = next_gammas;
        if max_delta < 1e-6 {
            break;
        }
    }

    let ph = -(gammas[1] * h).max(1e-30).log10();
    Ok((ph, total_sodium_m, h, oh, hco3, co3, co2))
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

fn dict_optional_float_value(dict: &Bound<'_, PyDict>, key: &str) -> Option<f64> {
    let value = dict.get_item(key).ok().flatten()?;
    let parsed = value.extract::<f64>().ok()?;
    if parsed.is_finite() {
        Some(parsed)
    } else {
        None
    }
}

/// Return a truthy dictionary value or an empty Python string as an owned object.
///
/// This keeps report-table schema parity with the Python fallback while avoiding
/// deprecated PyO3 conversion APIs that were removed from the current toolchain.
fn dict_truthy_or_empty_pyobject(
    py: Python<'_>,
    dict: &Bound<'_, PyDict>,
    key: &str,
) -> Py<PyAny> {
    let Some(value) = dict.get_item(key).ok().flatten() else {
        return PyString::new(py, "").into_any().unbind();
    };
    if value.is_truthy().unwrap_or(false) {
        value.unbind()
    } else {
        PyString::new(py, "").into_any().unbind()
    }
}

fn format_optional_decimal(value: Option<f64>, precision: usize) -> String {
    if let Some(parsed) = value {
        format!("{parsed:.precision$}")
    } else {
        String::new()
    }
}

/// Convert a Python object into a trimmed owned Rust string.
///
/// The helper materializes an owned `String` before trimming so no borrowed
/// Python string data escapes temporary PyO3 bindings.
fn py_any_to_trimmed_string(value: &Bound<'_, PyAny>) -> String {
    if let Ok(text) = value.extract::<String>() {
        return text.trim().to_string();
    }
    value
        .str()
        .ok()
        .and_then(|text| text.extract::<String>().ok())
        .map(|text| text.trim().to_string())
        .unwrap_or_default()
}

fn dict_string_value(dict: &Bound<'_, PyDict>, key: &str) -> String {
    let Some(value) = dict.get_item(key).ok().flatten() else {
        return String::new();
    };
    py_any_to_trimmed_string(&value)
}

/// Resolve the optional custom-values map attached to a ledger row.
///
/// The explicit lifetime keeps the returned dictionary bound to the same Python
/// interpreter scope as the source row, which PyO3 0.27 requires.
fn dict_custom_map<'py>(dict: &Bound<'py, PyDict>) -> Option<Bound<'py, PyDict>> {
    let custom_any = dict.get_item("custom_values").ok().flatten()?;
    custom_any.cast_into::<PyDict>().ok()
}

fn dict_custom_optional_float_value(dict: &Bound<'_, PyDict>, key: &str) -> Option<f64> {
    let custom_map = dict_custom_map(dict)?;
    let value = custom_map.get_item(key).ok().flatten()?;
    let parsed = value.extract::<f64>().ok()?;
    if parsed.is_finite() {
        Some(parsed)
    } else {
        None
    }
}

fn dict_custom_string_value(dict: &Bound<'_, PyDict>, key: &str) -> String {
    let Some(custom_map) = dict_custom_map(dict) else {
        return String::new();
    };
    let Some(value) = custom_map.get_item(key).ok().flatten() else {
        return String::new();
    };
    py_any_to_trimmed_string(&value)
}

fn is_ledger_builtin_numeric_key(key: &str) -> bool {
    matches!(
        key,
        "final_mass_g"
            | "final_pH"
            | "cycles"
            | "total_dp_uptake"
            | "theoretical_yield_g"
            | "actual_yield_pct"
    )
}

fn is_ledger_builtin_date_key(key: &str) -> bool {
    matches!(key, "run_date" | "updated_at")
}

fn ledger_sort_numeric_value(dict: &Bound<'_, PyDict>, sort_key: &str) -> Option<f64> {
    if is_ledger_builtin_numeric_key(sort_key) {
        return dict_optional_float_value(dict, sort_key);
    }
    dict_custom_optional_float_value(dict, sort_key)
}

fn ledger_sort_text_value(dict: &Bound<'_, PyDict>, sort_key: &str) -> String {
    if is_ledger_builtin_date_key(sort_key)
        || is_ledger_builtin_numeric_key(sort_key)
        || matches!(
            sort_key,
            "profile_name" | "project_number" | "batch_number" | "item_number" | "notes" | "id"
        )
    {
        return dict_string_value(dict, sort_key);
    }
    let custom_value = dict_custom_string_value(dict, sort_key);
    if !custom_value.is_empty() {
        return custom_value;
    }
    dict_string_value(dict, sort_key)
}

fn parse_int_prefix(raw: &str) -> Option<i64> {
    let digits: String = raw.chars().take_while(|ch| ch.is_ascii_digit()).collect();
    if digits.is_empty() {
        return None;
    }
    digits.parse::<i64>().ok()
}

fn parse_iso_datetime_sort_token(text: &str) -> Option<i64> {
    let trimmed = text.trim();
    let bytes = trimmed.as_bytes();
    if bytes.len() < 10 {
        return None;
    }
    if bytes.get(4).copied() != Some(b'-') || bytes.get(7).copied() != Some(b'-') {
        return None;
    }
    let date_part = std::str::from_utf8(&bytes[0..10]).ok()?;
    let mut date_tokens = date_part.split('-');
    let year = date_tokens.next()?.parse::<i64>().ok()?;
    let month = date_tokens.next()?.parse::<i64>().ok()?;
    let day = date_tokens.next()?.parse::<i64>().ok()?;
    if !(1..=12).contains(&month) || !(1..=31).contains(&day) {
        return None;
    }
    let mut hour = 0_i64;
    let mut minute = 0_i64;
    let mut second = 0_i64;
    if bytes.len() > 10 {
        let separator = bytes.get(10).copied()?;
        if !matches!(separator, b'T' | b't' | b' ') {
            return None;
        }
        let time_part = std::str::from_utf8(bytes.get(11..).unwrap_or_default()).ok()?;
        let mut time_tokens = time_part.split(':');
        if let Some(raw_hour) = time_tokens.next() {
            hour = parse_int_prefix(raw_hour).unwrap_or(0);
        }
        if let Some(raw_minute) = time_tokens.next() {
            minute = parse_int_prefix(raw_minute).unwrap_or(0);
        }
        if let Some(raw_second) = time_tokens.next() {
            second = parse_int_prefix(raw_second).unwrap_or(0);
        }
        hour = hour.clamp(0, 23);
        minute = minute.clamp(0, 59);
        second = second.clamp(0, 59);
    }
    Some((((((year * 100) + month) * 100 + day) * 100 + hour) * 100 + minute) * 100 + second)
}

fn ledger_sort_date_value(dict: &Bound<'_, PyDict>, sort_key: &str) -> Option<i64> {
    let raw_value = if is_ledger_builtin_date_key(sort_key) {
        dict_string_value(dict, sort_key)
    } else {
        dict_custom_string_value(dict, sort_key)
    };
    if raw_value.is_empty() {
        return None;
    }
    parse_iso_datetime_sort_token(&raw_value)
}

fn normalize_fraction_value(value: Option<f64>) -> f64 {
    let mut normalized = value.unwrap_or(0.0);
    if normalized > 1.0 {
        normalized /= 100.0;
    }
    if !normalized.is_finite() {
        return 0.0;
    }
    normalized.max(0.0)
}

/// Extract a carbonate fraction value from a nested `fractions` mapping.
///
/// Missing nested dictionaries or non-finite values are treated as absent so
/// Rust-side report builders match the Python fallback behavior.
fn extract_fraction_field(dict: &Bound<'_, PyDict>, key: &str) -> Option<f64> {
    let fractions_any = dict.get_item("fractions").ok().flatten()?;
    let fractions = fractions_any.cast_into::<PyDict>().ok()?;
    dict_optional_float_value(&fractions, key)
}

fn dict_optional_finite_by_keys(dict: &Bound<'_, PyDict>, keys: &[&str]) -> Option<f64> {
    for key in keys {
        let Some(any_value) = dict.get_item(*key).ok().flatten() else {
            continue;
        };
        let Ok(parsed) = any_value.extract::<f64>() else {
            continue;
        };
        if parsed.is_finite() {
            return Some(parsed);
        }
    }
    None
}

/// Parse compact NaOH-CO2 Pitzer coefficients from a Python mapping payload.
///
/// Returns `None` when any required coefficient is missing or non-finite.
fn parse_pitzer_params_map(pitzer_params: Option<&Bound<'_, PyDict>>) -> Option<PitzerParamsLite> {
    let params_map = pitzer_params?;
    let parse = |key: &str| -> Option<f64> {
        let value = params_map.get_item(key).ok().flatten()?;
        let parsed = value.extract::<f64>().ok()?;
        if parsed.is_finite() {
            Some(parsed)
        } else {
            None
        }
    };
    Some(PitzerParamsLite {
        b0_na_oh: parse("b0_na_oh")?,
        b1_na_oh: parse("b1_na_oh")?,
        c0_na_oh: parse("c0_na_oh")?,
        b0_na_hco3: parse("b0_na_hco3")?,
        b1_na_hco3: parse("b1_na_hco3")?,
        c0_na_hco3: parse("c0_na_hco3")?,
        b0_na_co3: parse("b0_na_co3")?,
        b1_na_co3: parse("b1_na_co3")?,
        c0_na_co3: parse("c0_na_co3")?,
        theta_co3_oh: parse("theta_co3_oh")?,
        psi_co3_na_oh: parse("psi_co3_na_oh")?,
        psi_co3_hco3_na: parse("psi_co3_hco3_na")?,
    })
}

fn compare_cycle_row_index(dict: &Bound<'_, PyDict>, fallback_index: usize) -> usize {
    for key in ["cycle_id", "cycle", "cycle_number", "cycle_index", "index"] {
        let Some(any_value) = dict.get_item(key).ok().flatten() else {
            continue;
        };
        let Ok(parsed) = any_value.extract::<isize>() else {
            continue;
        };
        if parsed >= 1 {
            if let Ok(cycle_id) = usize::try_from(parsed) {
                return cycle_id;
            }
        }
    }
    fallback_index.max(1)
}

fn py_any_optional_finite_float(value: &Bound<'_, PyAny>) -> Option<f64> {
    if value.is_none() {
        return None;
    }
    let parsed = value.extract::<f64>().ok()?;
    if parsed.is_finite() {
        Some(parsed)
    } else {
        None
    }
}

fn interpolate_reference_series_impl(
    x_value: Option<f64>,
    x_series: &[f64],
    y_series: &[Option<f64>],
) -> (Option<f64>, &'static str) {
    let Some(current_x) = x_value else {
        return (None, "out_of_range");
    };
    if !current_x.is_finite() {
        return (None, "out_of_range");
    }
    let mut pairs: Vec<(f64, Option<f64>)> = Vec::new();
    for (x_raw, y_raw) in x_series.iter().zip(y_series.iter()) {
        if !x_raw.is_finite() {
            continue;
        }
        pairs.push((*x_raw, *y_raw));
    }
    if pairs.is_empty() {
        return (None, "sparse_reference");
    }
    pairs.sort_by(|left, right| left.0.partial_cmp(&right.0).unwrap_or(Ordering::Equal));
    if pairs.len() < 2 {
        return (pairs[0].1, "sparse_reference");
    }
    if current_x < pairs[0].0 || current_x > pairs[pairs.len() - 1].0 {
        return (None, "out_of_range");
    }

    let mut right_idx: usize = 0;
    let mut found_right = false;
    for (idx, (x_pair, _)) in pairs.iter().enumerate() {
        if *x_pair >= current_x {
            right_idx = idx;
            found_right = true;
            break;
        }
    }
    if !found_right {
        right_idx = pairs.len() - 1;
    }
    let left_idx = right_idx.saturating_sub(1);
    let (x_left, y_left) = pairs[left_idx];
    let (x_right, y_right) = pairs[right_idx];

    if let (Some(left_val), Some(right_val)) = (y_left, y_right) {
        if left_val.is_finite() && right_val.is_finite() && x_right != x_left {
            let ratio = (current_x - x_left) / (x_right - x_left);
            let mapped = left_val + ratio * (right_val - left_val);
            if mapped.is_finite() {
                return (Some(mapped), "ok");
            }
        }
    }

    let nearest_idx = if (current_x - x_right).abs() < (current_x - x_left).abs() {
        right_idx
    } else {
        left_idx
    };
    let nearest = pairs[nearest_idx].1;
    if nearest.is_some() {
        (nearest, "ok")
    } else {
        (None, "sparse_reference")
    }
}

#[pyfunction]
#[pyo3(signature = (x_value, x_series, y_series))]
fn analysis_interpolate_reference_series_core(
    py: Python<'_>,
    x_value: Option<f64>,
    x_series: &Bound<'_, PyList>,
    y_series: &Bound<'_, PyList>,
) -> PyResult<Py<PyDict>> {
    // Interpolate one reference series point with the same out-of-range/sparse
    // flags used by the Python forensic/dashboard alignment path.
    let mut safe_x: Vec<f64> = Vec::new();
    let mut safe_y: Vec<Option<f64>> = Vec::new();
    for (x_any, y_any) in x_series.iter().zip(y_series.iter()) {
        let Some(x_val) = py_any_optional_finite_float(&x_any) else {
            continue;
        };
        safe_x.push(x_val);
        safe_y.push(py_any_optional_finite_float(&y_any));
    }
    let (mapped_value, flag) = interpolate_reference_series_impl(x_value, &safe_x, &safe_y);
    let response = PyDict::new(py);
    if let Some(value) = mapped_value {
        response.set_item("value", value)?;
    } else {
        response.set_item("value", py.None())?;
    }
    response.set_item("flag", flag)?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (
    actual_cycle_series,
    reference_cycle_series,
    target_ph,
    reaction_naoh_mass,
    initial_naoh_mol,
    co2_mw,
    naoh_mw
))]
/// Build the Rust-backed analysis dashboard payload from cycle series inputs.
///
/// The function mirrors the Python dashboard assembly path so backend switching
/// does not change interpolation, fraction extraction, or summary table shape.
fn analysis_dashboard_core(
    py: Python<'_>,
    actual_cycle_series: &Bound<'_, PyList>,
    reference_cycle_series: &Bound<'_, PyList>,
    target_ph: f64,
    reaction_naoh_mass: Option<f64>,
    initial_naoh_mol: Option<f64>,
    co2_mw: f64,
    naoh_mw: f64,
) -> PyResult<Py<PyDict>> {
    // Build comparison rows + summary metrics for the Analysis dashboard using
    // the same deterministic interpolation and fail-closed value handling.
    #[derive(Clone, Copy)]
    struct ActualRow {
        cycle_id: usize,
        cycle_co2_g: Option<f64>,
        cumulative_co2_g: Option<f64>,
        cumulative_co2_mol: Option<f64>,
        duration_x: Option<f64>,
        ph: Option<f64>,
        hco3_fraction: f64,
        co3_fraction: f64,
    }
    #[derive(Clone, Copy)]
    struct ReferenceRow {
        cycle_id: usize,
        cumulative_co2_g: Option<f64>,
        ph: Option<f64>,
        equivalence_reached: bool,
    }
    let mut actual_rows: Vec<ActualRow> = Vec::new();
    let mut actual_alignment_override: Vec<String> = Vec::new();
    let mut inferred_time_label = String::new();
    for (idx, item) in actual_cycle_series.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let cycle_id = compare_cycle_row_index(&entry, idx + 1);
        let cycle_co2_g = dict_optional_finite_by_keys(
            &entry,
            &["co2_cycle_g", "cycle_co2_g", "co2_mass_g"],
        );
        let cumulative_co2_g = dict_optional_finite_by_keys(
            &entry,
            &["cumulative_co2_g", "co2_g", "cumulative_co2_added_mass_g", "co2_mass_g"],
        );
        let cumulative_co2_mol = dict_optional_finite_by_keys(
            &entry,
            &[
                "cumulative_co2_mol",
                "cumulative_co2_added_moles",
                "co2_moles",
                "co2_added_moles",
            ],
        );
        let duration_x = dict_optional_finite_by_keys(&entry, &["duration_x"]);
        if inferred_time_label.is_empty() {
            inferred_time_label = dict_string_value(&entry, "x_label");
        }
        let ph = dict_optional_finite_by_keys(&entry, &["ph", "actual_ph", "solution_ph"]);
        let mut hco3_fraction = 0.0_f64;
        let mut co3_fraction = 0.0_f64;
        if let Some(fractions_any) = entry.get_item("fractions").ok().flatten() {
            if let Ok(fractions) = fractions_any.cast_into::<PyDict>() {
                hco3_fraction = dict_optional_float_value(&fractions, "HCO3-")
                    .unwrap_or(0.0)
                    .max(0.0);
                co3_fraction = dict_optional_float_value(&fractions, "CO3^2-")
                    .unwrap_or(0.0)
                    .max(0.0);
            }
        }
        actual_rows.push(ActualRow {
            cycle_id,
            cycle_co2_g,
            cumulative_co2_g,
            cumulative_co2_mol,
            duration_x,
            ph,
            hco3_fraction,
            co3_fraction,
        });
        actual_alignment_override.push(dict_string_value(&entry, "alignment_quality_flag"));
    }

    let mut reference_rows: Vec<ReferenceRow> = Vec::new();
    let mut reference_x: Vec<f64> = Vec::new();
    let mut reference_ph: Vec<Option<f64>> = Vec::new();
    let mut reference_hco3: Vec<Option<f64>> = Vec::new();
    let mut reference_co3: Vec<Option<f64>> = Vec::new();
    for (idx, item) in reference_cycle_series.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let cycle_id = compare_cycle_row_index(&entry, idx + 1);
        let cumulative_co2_g = dict_optional_finite_by_keys(
            &entry,
            &["cumulative_co2_g", "co2_g", "cumulative_co2_added_mass_g", "co2_mass_g"],
        );
        if let Some(x_value) = cumulative_co2_g {
            if x_value.is_finite() {
                reference_x.push(x_value);
            }
        }
        let ph = dict_optional_finite_by_keys(&entry, &["ph", "reference_ph", "solution_ph"]);
        let mut hco3_fraction = None;
        let mut co3_fraction = None;
        if let Some(fractions_any) = entry.get_item("fractions").ok().flatten() {
            if let Ok(fractions) = fractions_any.cast_into::<PyDict>() {
                hco3_fraction = dict_optional_float_value(&fractions, "HCO3-");
                co3_fraction = dict_optional_float_value(&fractions, "CO3^2-");
            }
        }
        reference_ph.push(ph);
        reference_hco3.push(hco3_fraction);
        reference_co3.push(co3_fraction);
        let equivalence_reached = entry
            .get_item("equivalence_reached")
            .ok()
            .flatten()
            .and_then(|value| value.is_truthy().ok())
            .unwrap_or(false);
        reference_rows.push(ReferenceRow {
            cycle_id,
            cumulative_co2_g,
            ph,
            equivalence_reached,
        });
    }

    let comparison_series = PyList::empty(py);
    for (idx, row) in actual_rows.iter().enumerate() {
        let ref_cycle = reference_rows.get(idx).copied();
        let reference_cycle_ph = ref_cycle.and_then(|item| item.ph);
        let delta_cycle_ph = match (row.ph, reference_cycle_ph) {
            (Some(actual), Some(reference)) => Some(actual - reference),
            _ => None,
        };
        let (reference_co2_aligned_ph, ph_alignment) = interpolate_reference_series_impl(
            row.cumulative_co2_g,
            &reference_x,
            &reference_ph,
        );
        let (co2_aligned_hco3, hco3_alignment) = interpolate_reference_series_impl(
            row.cumulative_co2_g,
            &reference_x,
            &reference_hco3,
        );
        let (co2_aligned_co3, co3_alignment) = interpolate_reference_series_impl(
            row.cumulative_co2_g,
            &reference_x,
            &reference_co3,
        );
        let delta_co2_ph = match (row.ph, reference_co2_aligned_ph) {
            (Some(actual), Some(reference)) => Some(actual - reference),
            _ => None,
        };
        let actual_hco3_pct = row.hco3_fraction.max(0.0) * 100.0;
        let actual_co3_pct = row.co3_fraction.max(0.0) * 100.0;
        let reference_hco3_pct = co2_aligned_hco3.map(|value| value * 100.0);
        let reference_co3_pct = co2_aligned_co3.map(|value| value * 100.0);
        let delta_hco3_pct = reference_hco3_pct.map(|reference| actual_hco3_pct - reference);
        let delta_co3_pct = reference_co3_pct.map(|reference| actual_co3_pct - reference);
        let mut alignment_quality = if [ph_alignment, hco3_alignment, co3_alignment]
            .iter()
            .any(|flag| *flag == "out_of_range")
        {
            "out_of_range".to_string()
        } else if [ph_alignment, hco3_alignment, co3_alignment]
            .iter()
            .any(|flag| *flag == "sparse_reference")
        {
            "sparse_reference".to_string()
        } else {
            "ok".to_string()
        };
        if let Some(override_flag) = actual_alignment_override.get(idx) {
            let trimmed = override_flag.trim();
            if !trimmed.is_empty() {
                alignment_quality = trimmed.to_string();
            }
        }

        let comparison_row = PyDict::new(py);
        comparison_row.set_item("cycle_id", row.cycle_id)?;
        if let Some(value) = row.ph {
            comparison_row.set_item("actual_ph", value)?;
        } else {
            comparison_row.set_item("actual_ph", py.None())?;
        }
        if let Some(value) = reference_cycle_ph {
            comparison_row.set_item("reference_cycle_ph", value)?;
        } else {
            comparison_row.set_item("reference_cycle_ph", py.None())?;
        }
        if let Some(value) = reference_co2_aligned_ph {
            comparison_row.set_item("reference_co2_aligned_ph", value)?;
        } else {
            comparison_row.set_item("reference_co2_aligned_ph", py.None())?;
        }
        if let Some(value) = delta_cycle_ph {
            comparison_row.set_item("delta_cycle_ph", value)?;
        } else {
            comparison_row.set_item("delta_cycle_ph", py.None())?;
        }
        if let Some(value) = delta_co2_ph {
            comparison_row.set_item("delta_co2_ph", value)?;
        } else {
            comparison_row.set_item("delta_co2_ph", py.None())?;
        }
        comparison_row.set_item("actual_hco3_pct", actual_hco3_pct)?;
        comparison_row.set_item("actual_co3_pct", actual_co3_pct)?;
        if let Some(value) = reference_hco3_pct {
            comparison_row.set_item("reference_hco3_pct", value)?;
        } else {
            comparison_row.set_item("reference_hco3_pct", py.None())?;
        }
        if let Some(value) = reference_co3_pct {
            comparison_row.set_item("reference_co3_pct", value)?;
        } else {
            comparison_row.set_item("reference_co3_pct", py.None())?;
        }
        if let Some(value) = delta_hco3_pct {
            comparison_row.set_item("delta_hco3_pct", value)?;
        } else {
            comparison_row.set_item("delta_hco3_pct", py.None())?;
        }
        if let Some(value) = delta_co3_pct {
            comparison_row.set_item("delta_co3_pct", value)?;
        } else {
            comparison_row.set_item("delta_co3_pct", py.None())?;
        }
        comparison_row.set_item("alignment_quality_flag", alignment_quality)?;
        comparison_series.append(comparison_row)?;
    }

    let total_uptake_g = actual_rows.last().and_then(|row| row.cumulative_co2_g);
    let total_uptake_mol = actual_rows.last().and_then(|row| row.cumulative_co2_mol);
    let co2_mw_value = if co2_mw.is_finite() && co2_mw > 0.0 {
        co2_mw
    } else {
        SOL_MW_CO2
    };
    let naoh_mw_value = if naoh_mw.is_finite() && naoh_mw > 0.0 {
        naoh_mw
    } else {
        SOL_MW_NAOH
    };
    let theoretical_yield_g = if let Some(start_mass_g) = reaction_naoh_mass {
        if start_mass_g.is_finite() && start_mass_g > 0.0 && naoh_mw_value > 0.0 {
            Some((start_mass_g / naoh_mw_value) * co2_mw_value)
        } else {
            None
        }
    } else {
        None
    };
    let actual_yield_pct = match (total_uptake_g, theoretical_yield_g) {
        (Some(total), Some(theoretical)) if theoretical > 1e-12 => Some((total / theoretical) * 100.0),
        _ => None,
    };
    let reference_final_g = reference_rows.last().and_then(|row| row.cumulative_co2_g);
    let planning_completion_pct = match (reference_final_g, total_uptake_g) {
        (Some(reference), Some(total)) if reference > 1e-12 => {
            Some((total / reference).clamp(0.0, 1.0) * 100.0)
        }
        _ => None,
    };
    let equivalence_co2_g = match initial_naoh_mol {
        Some(moles) if moles.is_finite() && moles > 0.0 => Some((moles / 2.0) * co2_mw_value),
        _ => None,
    };
    let equivalence_completion_pct = match (equivalence_co2_g, total_uptake_g) {
        (Some(reference), Some(total)) if reference > 1e-12 => {
            Some((total / reference).clamp(0.0, 1.0) * 100.0)
        }
        _ => None,
    };
    let mut equivalence_cycle_actual: Option<usize> = None;
    if let Some(eq_target_g) = equivalence_co2_g {
        for row in &actual_rows {
            if let Some(cumulative_g) = row.cumulative_co2_g {
                if cumulative_g >= eq_target_g {
                    equivalence_cycle_actual = Some(row.cycle_id);
                    break;
                }
            }
        }
    }
    let mut equivalence_cycle_reference: Option<usize> = None;
    for row in &reference_rows {
        if row.equivalence_reached {
            equivalence_cycle_reference = Some(row.cycle_id);
            break;
        }
    }
    let additional_co2_required_g = match (reference_final_g, total_uptake_g) {
        (Some(reference), Some(total)) if reference.is_finite() && total.is_finite() => {
            Some((reference - total).max(0.0))
        }
        _ => None,
    };
    let additional_co2_required_mol = match additional_co2_required_g {
        Some(value) if co2_mw_value > 0.0 => Some(value / co2_mw_value),
        _ => None,
    };
    let mut forecast_confidence = "low".to_string();
    let mut forecast_slowdown_detected = false;
    let mut forecast_lookback_cycles: usize = 0;
    let mut forecast_knee_cycle: Option<usize> = None;
    let mut forecast_pre_knee_rate_g_per_cycle: Option<f64> = None;
    let mut forecast_post_knee_rate_g_per_cycle: Option<f64> = None;
    let mut forecast_tail_rate_g_per_cycle: Option<f64> = None;
    let mut forecast_remaining_cycles: Option<f64> = None;
    let mut forecast_remaining_time_x: Option<f64> = None;
    let mut forecast_time_basis = "cycles_only".to_string();
    let remaining_target_g = additional_co2_required_g.unwrap_or(0.0);
    if remaining_target_g <= 1e-12 {
        forecast_confidence = "high".to_string();
        forecast_remaining_cycles = Some(0.0);
        forecast_remaining_time_x = Some(0.0);
    } else {
        let mut cycle_uptakes_g: Vec<f64> = Vec::new();
        let mut durations_x: Vec<Option<f64>> = Vec::new();
        let mut cumulative_known = false;
        let mut last_cumulative = 0.0_f64;
        for row in &actual_rows {
            let mut cycle_mass = row.cycle_co2_g;
            if cycle_mass.is_none() {
                if let Some(cumulative) = row.cumulative_co2_g {
                    if cumulative_known {
                        cycle_mass = Some((cumulative - last_cumulative).max(0.0));
                    } else {
                        cycle_mass = Some(cumulative.max(0.0));
                    }
                    cumulative_known = true;
                    last_cumulative = cumulative;
                }
            }
            cycle_uptakes_g.push(cycle_mass.unwrap_or(0.0).max(0.0));
            let duration = row.duration_x.and_then(|value| {
                if value.is_finite() && value > 0.0 {
                    Some(value)
                } else {
                    None
                }
            });
            durations_x.push(duration);
        }
        let detected_cycles = cycle_uptakes_g.len();
        if detected_cycles >= 4 {
            let mut lookback = ((detected_cycles as f64) * 0.2_f64).round() as usize;
            lookback = lookback.clamp(4, 12).min(detected_cycles);
            forecast_lookback_cycles = lookback;
            let recent = &cycle_uptakes_g[detected_cycles - lookback..];
            if recent.len() >= 4 {
                let mut best_split: Option<usize> = None;
                let mut best_sse = f64::INFINITY;
                for split_idx in 2..(recent.len() - 1) {
                    let pre = &recent[..split_idx];
                    let post = &recent[split_idx..];
                    let pre_mean = pre.iter().sum::<f64>() / pre.len() as f64;
                    let post_mean = post.iter().sum::<f64>() / post.len() as f64;
                    let pre_sse = pre
                        .iter()
                        .map(|value| (value - pre_mean) * (value - pre_mean))
                        .sum::<f64>();
                    let post_sse = post
                        .iter()
                        .map(|value| (value - post_mean) * (value - post_mean))
                        .sum::<f64>();
                    let sse = pre_sse + post_sse;
                    if sse < best_sse {
                        best_sse = sse;
                        best_split = Some(split_idx);
                    }
                }
                if let Some(split_idx) = best_split {
                    let pre = &recent[..split_idx];
                    let post = &recent[split_idx..];
                    let pre_rate = pre.iter().sum::<f64>() / pre.len() as f64;
                    let post_rate = post.iter().sum::<f64>() / post.len() as f64;
                    forecast_pre_knee_rate_g_per_cycle = Some(pre_rate);
                    forecast_post_knee_rate_g_per_cycle = Some(post_rate);
                    forecast_knee_cycle = Some(detected_cycles - lookback + split_idx);
                    forecast_slowdown_detected =
                        pre_rate > 1e-12 && post_rate <= (pre_rate * 0.92_f64);
                    let tail_window = recent.len().clamp(3, 5);
                    let tail_rate = if forecast_slowdown_detected && post_rate > 1e-12 {
                        post_rate
                    } else {
                        recent[recent.len() - tail_window..].iter().sum::<f64>()
                            / tail_window as f64
                    };
                    if tail_rate > 1e-12 && tail_rate.is_finite() {
                        forecast_tail_rate_g_per_cycle = Some(tail_rate);
                        let remaining_cycles = (remaining_target_g / tail_rate).max(0.0);
                        forecast_remaining_cycles = Some(remaining_cycles);
                        let post_variance = post
                            .iter()
                            .map(|value| (value - post_rate) * (value - post_rate))
                            .sum::<f64>()
                            / post.len().max(1) as f64;
                        let post_cv = if post_rate.abs() > 1e-12 {
                            post_variance.sqrt() / post_rate.abs()
                        } else {
                            f64::INFINITY
                        };
                        if detected_cycles >= 8 && forecast_slowdown_detected && post_cv <= 0.25 {
                            forecast_confidence = "high".to_string();
                        } else if detected_cycles >= 6 && post_cv <= 0.45 {
                            forecast_confidence = "medium".to_string();
                        }
                        let time_label_lower = inferred_time_label.trim().to_lowercase();
                        let is_time_basis = ["elapsed", "time", "sec", "second", "min", "hour", "day"]
                            .iter()
                            .any(|token| time_label_lower.contains(token));
                        if is_time_basis {
                            let finite_durations: Vec<f64> = durations_x
                                [durations_x.len().saturating_sub(lookback)..]
                                .iter()
                                .filter_map(|value| *value)
                                .collect();
                            if !finite_durations.is_empty() {
                                let avg_duration =
                                    finite_durations.iter().sum::<f64>() / finite_durations.len() as f64;
                                forecast_remaining_time_x = Some(remaining_cycles * avg_duration);
                                forecast_time_basis = if inferred_time_label.trim().is_empty() {
                                    "elapsed_time".to_string()
                                } else {
                                    inferred_time_label.trim().to_string()
                                };
                            }
                        }
                    }
                }
            }
        }
    }
    let warning_rows = PyList::empty(py);
    if reference_rows.is_empty() && !actual_rows.is_empty() {
        warning_rows.append(
            "Reference simulation unavailable; verify per-cycle CO2 uptake fields.",
        )?;
    }

    let summary = PyDict::new(py);
    summary.set_item("detected_cycles", actual_rows.len())?;
    summary.set_item("reference_cycles", reference_rows.len())?;
    summary.set_item("target_ph", target_ph)?;
    if let Some(value) = total_uptake_g {
        summary.set_item("total_uptake_g", value)?;
    } else {
        summary.set_item("total_uptake_g", py.None())?;
    }
    if let Some(value) = total_uptake_mol {
        summary.set_item("total_uptake_mol", value)?;
    } else {
        summary.set_item("total_uptake_mol", py.None())?;
    }
    if let Some(value) = theoretical_yield_g {
        summary.set_item("theoretical_yield_g", value)?;
    } else {
        summary.set_item("theoretical_yield_g", py.None())?;
    }
    if let Some(value) = actual_yield_pct {
        summary.set_item("actual_yield_pct", value)?;
    } else {
        summary.set_item("actual_yield_pct", py.None())?;
    }
    if let Some(value) = planning_completion_pct {
        summary.set_item("planning_completion_pct", value)?;
    } else {
        summary.set_item("planning_completion_pct", py.None())?;
    }
    if let Some(value) = equivalence_completion_pct {
        summary.set_item("equivalence_completion_pct", value)?;
    } else {
        summary.set_item("equivalence_completion_pct", py.None())?;
    }
    if let Some(value) = equivalence_cycle_actual {
        summary.set_item("equivalence_cycle_actual", value)?;
    } else {
        summary.set_item("equivalence_cycle_actual", py.None())?;
    }
    if let Some(value) = equivalence_cycle_reference {
        summary.set_item("equivalence_cycle_reference", value)?;
    } else {
        summary.set_item("equivalence_cycle_reference", py.None())?;
    }
    if let Some(value) = additional_co2_required_g {
        summary.set_item("additional_co2_required_g", value)?;
    } else {
        summary.set_item("additional_co2_required_g", py.None())?;
    }
    if let Some(value) = additional_co2_required_mol {
        summary.set_item("additional_co2_required_mol", value)?;
    } else {
        summary.set_item("additional_co2_required_mol", py.None())?;
    }
    summary.set_item("forecast_model", "two_phase_trend")?;
    summary.set_item("forecast_confidence", forecast_confidence)?;
    summary.set_item("forecast_slowdown_detected", forecast_slowdown_detected)?;
    summary.set_item("forecast_lookback_cycles", forecast_lookback_cycles)?;
    if let Some(value) = forecast_knee_cycle {
        summary.set_item("forecast_knee_cycle", value)?;
    } else {
        summary.set_item("forecast_knee_cycle", py.None())?;
    }
    if let Some(value) = forecast_pre_knee_rate_g_per_cycle {
        summary.set_item("forecast_pre_knee_rate_g_per_cycle", value)?;
    } else {
        summary.set_item("forecast_pre_knee_rate_g_per_cycle", py.None())?;
    }
    if let Some(value) = forecast_post_knee_rate_g_per_cycle {
        summary.set_item("forecast_post_knee_rate_g_per_cycle", value)?;
    } else {
        summary.set_item("forecast_post_knee_rate_g_per_cycle", py.None())?;
    }
    if let Some(value) = forecast_tail_rate_g_per_cycle {
        summary.set_item("forecast_tail_rate_g_per_cycle", value)?;
    } else {
        summary.set_item("forecast_tail_rate_g_per_cycle", py.None())?;
    }
    if let Some(value) = forecast_remaining_cycles {
        summary.set_item("forecast_remaining_cycles", value)?;
    } else {
        summary.set_item("forecast_remaining_cycles", py.None())?;
    }
    if let Some(value) = forecast_remaining_time_x {
        summary.set_item("forecast_remaining_time_x", value)?;
    } else {
        summary.set_item("forecast_remaining_time_x", py.None())?;
    }
    summary.set_item("forecast_time_basis", forecast_time_basis)?;
    summary.set_item("warnings", warning_rows)?;

    let response = PyDict::new(py);
    response.set_item("comparison_series", comparison_series)?;
    response.set_item("summary", summary)?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (
    model_key,
    cycle_uptake_mol_series,
    anchor_cycle_index=None,
    measured_ph=None,
    equivalence_cycle_index=None,
    target_ph=None,
    initial_naoh_mol=None,
    solution_volume_l=None,
    temperature_c=None,
    planning_reference_total_mol=None,
    equivalence_co2_mol=None,
    pitzer_params=None,
    anchors=None,
    prior_cycle_factor_series=None,
    prior_sample_count=0,
    regularization_strength=0.02,
    smoothness_strength=0.01,
    min_factor=0.5,
    max_factor=1.5
))]
/// Calibrate piecewise uptake factors against one or more measured pH anchors.
///
/// The solver mirrors the Python fallback contract: bounded deterministic
/// segment fitting with regularization and split-factor smoothness.
fn measured_ph_uptake_calibration_core(
    py: Python<'_>,
    model_key: &str,
    cycle_uptake_mol_series: &Bound<'_, PyList>,
    anchor_cycle_index: Option<usize>,
    measured_ph: Option<f64>,
    equivalence_cycle_index: Option<usize>,
    target_ph: Option<f64>,
    initial_naoh_mol: Option<f64>,
    solution_volume_l: Option<f64>,
    temperature_c: Option<f64>,
    planning_reference_total_mol: Option<f64>,
    equivalence_co2_mol: Option<f64>,
    pitzer_params: Option<Bound<'_, PyDict>>,
    anchors: Option<Bound<'_, PyList>>,
    prior_cycle_factor_series: Option<Bound<'_, PyList>>,
    prior_sample_count: usize,
    regularization_strength: f64,
    smoothness_strength: f64,
    min_factor: f64,
    max_factor: f64,
) -> PyResult<Py<PyDict>> {
    #[derive(Clone)]
    struct SimulationPayload {
        corrected_cycle: Vec<f64>,
        corrected_cumulative: Vec<f64>,
        corrected_ph: Vec<Option<f64>>,
        corrected_fractions: Vec<[f64; 3]>,
    }

    #[derive(Clone)]
    struct AnchorPoint {
        cycle_index: usize,
        measured_ph: f64,
        source: String,
    }

    let build_error = |message: &str| -> PyResult<Py<PyDict>> {
        let payload = PyDict::new(py);
        payload.set_item("solver_status", "invalid_input")?;
        payload.set_item("solver_message", message)?;
        Ok(payload.unbind())
    };

    let mut cycle_moles: Vec<f64> = Vec::new();
    for item in cycle_uptake_mol_series.iter() {
        let parsed = item.extract::<f64>().ok().unwrap_or(0.0);
        if parsed.is_finite() && parsed >= 0.0 {
            cycle_moles.push(parsed);
        } else {
            cycle_moles.push(0.0);
        }
    }
    if cycle_moles.is_empty() {
        return build_error("No cycle uptake values were provided for calibration.");
    }

    let mut lower_bound = min_factor.min(max_factor);
    let mut upper_bound = min_factor.max(max_factor);
    if !lower_bound.is_finite() || !upper_bound.is_finite() {
        lower_bound = 0.5;
        upper_bound = 1.5;
    }
    if lower_bound <= 0.0 {
        lower_bound = 0.1;
    }
    if upper_bound <= lower_bound {
        upper_bound = lower_bound + 0.1;
    }

    let source_priority = |source: &str| -> i32 {
        match source.trim().to_ascii_lowercase().as_str() {
            "manual" | "form" => 5,
            "legacy" => 4,
            "profile" => 3,
            "auto_final_ph" => 1,
            _ => 2,
        }
    };

    let mut anchors_by_cycle: BTreeMap<usize, (i32, AnchorPoint)> = BTreeMap::new();
    if let Some(anchor_rows) = anchors {
        for item in anchor_rows.iter() {
            let Ok(row) = item.cast_into::<PyDict>() else {
                continue;
            };
            let cycle_any = row
                .get_item("cycle_index")
                .ok()
                .flatten()
                .or_else(|| row.get_item("measured_ph_cycle_index").ok().flatten());
            let ph_any = row
                .get_item("measured_ph")
                .ok()
                .flatten()
                .or_else(|| row.get_item("measured_ph_value").ok().flatten());
            let source = row
                .get_item("source")
                .ok()
                .flatten()
                .and_then(|value| value.extract::<String>().ok())
                .unwrap_or_else(|| "manual".to_string());
            let Some(cycle_raw) = cycle_any.and_then(|value| value.extract::<f64>().ok()) else {
                continue;
            };
            let Some(ph_value) = ph_any.and_then(|value| value.extract::<f64>().ok()) else {
                continue;
            };
            if !cycle_raw.is_finite() || !ph_value.is_finite() {
                continue;
            }
            let rounded_cycle = cycle_raw.round();
            if (cycle_raw - rounded_cycle).abs() > 1e-6 || rounded_cycle <= 0.0 {
                continue;
            }
            let cycle_index = (rounded_cycle as usize).max(1).min(cycle_moles.len());
            if !(0.0 < ph_value && ph_value < 14.0) {
                continue;
            }
            let anchor = AnchorPoint {
                cycle_index,
                measured_ph: ph_value,
                source: source.clone(),
            };
            let incoming_priority = source_priority(&source);
            if let Some((existing_priority, _existing_anchor)) =
                anchors_by_cycle.get(&cycle_index)
            {
                if incoming_priority < *existing_priority {
                    continue;
                }
            }
            anchors_by_cycle.insert(cycle_index, (incoming_priority, anchor));
        }
    }
    if anchors_by_cycle.is_empty() {
        let Some(legacy_ph) = measured_ph.filter(|value| value.is_finite()) else {
            return build_error("Measured pH anchors are required for calibration.");
        };
        let anchor_idx = anchor_cycle_index
            .unwrap_or(1)
            .max(1)
            .min(cycle_moles.len());
        anchors_by_cycle.insert(
            anchor_idx,
            (
                source_priority("legacy"),
                AnchorPoint {
                    cycle_index: anchor_idx,
                    measured_ph: legacy_ph,
                    source: "legacy".to_string(),
                },
            ),
        );
    }
    let normalized_anchors: Vec<AnchorPoint> = anchors_by_cycle
        .values()
        .map(|(_priority, anchor)| anchor.clone())
        .collect();
    let primary_anchor = normalized_anchors
        .last()
        .cloned()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Missing anchor payload"))?;
    let split_idx = equivalence_cycle_index
        .unwrap_or(primary_anchor.cycle_index)
        .max(1)
        .min(cycle_moles.len());

    let temp_c = temperature_c
        .filter(|value| value.is_finite())
        .unwrap_or(25.0);
    let use_temp_constants = true;
    let pka2_value = resolve_pka2_value(Some(temp_c), use_temp_constants);
    let is_pitzer_model = model_key.trim().eq_ignore_ascii_case("naoh_co2_pitzer_hmw");
    let pitzer_coeffs = if is_pitzer_model {
        parse_pitzer_params_map(pitzer_params.as_ref())
    } else {
        None
    };
    let available_naoh_mol = initial_naoh_mol
        .filter(|value| value.is_finite() && *value > 0.0)
        .map(|value| value.max(0.0));
    let available_volume_l = solution_volume_l
        .filter(|value| value.is_finite() && *value > 0.0)
        .map(|value| value.max(1e-9));

    let predict_from_cumulative =
        |cumulative_mol: f64, _cycle_index: usize| -> (Option<f64>, [f64; 3]) {
            let cumulative = cumulative_mol.max(0.0);

            // Prefer the Pitzer mapping when the selected model is NaOH-CO2 Pitzer
            // and compact parameter coefficients are available.
            if let (Some(params), Some(naoh_mol), Some(volume_l)) =
                (pitzer_coeffs, available_naoh_mol, available_volume_l)
            {
                let total_sodium_m = naoh_mol / volume_l;
                let total_carbon_m = cumulative / volume_l;
                if total_sodium_m.is_finite() && total_sodium_m > 0.0 {
                    if let Ok((ph, _na, _h, _oh, hco3, co3, co2)) =
                        solve_pitzer_total_carbon_impl(total_carbon_m, total_sodium_m, params, 60)
                    {
                        if ph.is_finite() {
                            let total = (co2.max(0.0) + hco3.max(0.0) + co3.max(0.0)).max(1e-12);
                            return (
                                Some(clamp_ph_value(ph)),
                                [co2.max(0.0) / total, hco3.max(0.0) / total, co3.max(0.0) / total],
                            );
                        }
                    }
                }
            }

            if let (Some(naoh_mol), Some(volume_l)) = (available_naoh_mol, available_volume_l) {
                let input_ledger = LedgerState {
                    naoh_remaining_mol: naoh_mol,
                    na2co3_mol: 0.0,
                    nahco3_mol: 0.0,
                    co2_excess_mol: 0.0,
                };
                let (state, _accounting, ph_value) = simulate_reaction_state_with_accounting_impl(
                    input_ledger,
                    cumulative,
                    pka2_value,
                    Some(volume_l),
                    Some(temp_c),
                    None,
                    use_temp_constants,
                    None,
                    None,
                    true,
                );
                let total_carbon = (state.co2_excess_mol.max(0.0)
                    + state.nahco3_mol.max(0.0)
                    + state.na2co3_mol.max(0.0))
                .max(1e-12);
                return (
                    Some(clamp_ph_value(ph_value)),
                    [
                        state.co2_excess_mol.max(0.0) / total_carbon,
                        state.nahco3_mol.max(0.0) / total_carbon,
                        state.na2co3_mol.max(0.0) / total_carbon,
                    ],
                );
            }

            let (ka1, ka2, _kw) = basic_carbonate_constants(Some(temp_c), use_temp_constants);
            let pseudo_ph = clamp_ph_value(13.5 - (cumulative + 1.0).ln() * 1.2);
            let h = 10f64.powf(-pseudo_ph);
            let denom = h * h + ka1 * h + ka1 * ka2;
            if denom <= 1e-30 {
                return (Some(pseudo_ph), [0.0, 0.0, 0.0]);
            }
            let h2co3 = (h * h / denom).max(0.0);
            let hco3 = (ka1 * h / denom).max(0.0);
            let co3 = (ka1 * ka2 / denom).max(0.0);
            let total = (h2co3 + hco3 + co3).max(1e-12);
            (Some(pseudo_ph), [h2co3 / total, hco3 / total, co3 / total])
        };

    let simulate_for_factor_series = |factor_series: &[f64]| -> SimulationPayload {
        let mut corrected_cycle: Vec<f64> = Vec::with_capacity(cycle_moles.len());
        let mut corrected_cumulative: Vec<f64> = Vec::with_capacity(cycle_moles.len());
        let mut corrected_ph: Vec<Option<f64>> = Vec::with_capacity(cycle_moles.len());
        let mut corrected_fractions: Vec<[f64; 3]> = Vec::with_capacity(cycle_moles.len());
        let mut cumulative = 0.0_f64;
        for (idx, raw_cycle_mol) in cycle_moles.iter().enumerate() {
            let cycle_index = idx + 1;
            let factor = if idx < factor_series.len() {
                factor_series[idx]
            } else {
                1.0
            };
            let corrected = (raw_cycle_mol * factor).max(0.0);
            cumulative += corrected;
            let (ph_value, fractions) = predict_from_cumulative(cumulative, cycle_index);
            corrected_cycle.push(corrected);
            corrected_cumulative.push(cumulative);
            corrected_ph.push(ph_value.filter(|value| value.is_finite()));
            corrected_fractions.push([
                fractions[0].max(0.0),
                fractions[1].max(0.0),
                fractions[2].max(0.0),
            ]);
        }
        SimulationPayload {
            corrected_cycle,
            corrected_cumulative,
            corrected_ph,
            corrected_fractions,
        }
    };

    let mut seed_factors: Vec<f64> = vec![1.0; cycle_moles.len()];
    let mut prior_applied = false;
    if let Some(prior_rows) = prior_cycle_factor_series {
        for (idx, item) in prior_rows.iter().enumerate() {
            if idx >= seed_factors.len() {
                break;
            }
            let parsed = item.extract::<f64>().ok().unwrap_or(1.0);
            if parsed.is_finite() {
                seed_factors[idx] = parsed.clamp(lower_bound, upper_bound);
                prior_applied = true;
            }
        }
    }
    let prefit_baseline = simulate_for_factor_series(&seed_factors);
    let mut working_factors = seed_factors.clone();
    let mut segment_rows: Vec<(usize, usize, f64, bool)> = Vec::new();
    let mut objective_total = 0.0_f64;
    let mut prev_anchor_idx = 0_usize;
    let mut previous_segment_scale = 1.0_f64;

    let mut grid_values: Vec<f64> = Vec::new();
    let mut current = lower_bound;
    while current <= upper_bound + 1e-12 {
        grid_values.push((current * 1_000_000.0).round() / 1_000_000.0);
        current += 0.05;
    }
    if grid_values.is_empty() {
        grid_values.push(1.0);
    }

    for anchor in &normalized_anchors {
        let anchor_idx = anchor.cycle_index.max(1).min(cycle_moles.len());
        let measured_anchor_ph = anchor.measured_ph;
        let segment_start = prev_anchor_idx + 1;
        let segment_end = anchor_idx;
        if segment_end < segment_start {
            continue;
        }
        let segment_base = working_factors.clone();
        let segment_objective = |segment_scale: f64| -> (f64, SimulationPayload) {
            let mut candidate_factors = working_factors.clone();
            for cycle_pos in (segment_start - 1)..segment_end {
                let candidate_value =
                    (segment_base[cycle_pos] * segment_scale).clamp(lower_bound, upper_bound);
                candidate_factors[cycle_pos] = candidate_value;
            }
            let sim_payload = simulate_for_factor_series(&candidate_factors);
            let anchor_pred = sim_payload
                .corrected_ph
                .get(anchor_idx.saturating_sub(1))
                .copied()
                .flatten();
            let Some(anchor_predicted) = anchor_pred else {
                return (f64::INFINITY, sim_payload);
            };
            if !anchor_predicted.is_finite() {
                return (f64::INFINITY, sim_payload);
            }
            let residual = anchor_predicted - measured_anchor_ph;
            let objective = residual * residual
                + regularization_strength * (segment_scale - 1.0).powi(2)
                + smoothness_strength * (segment_scale - previous_segment_scale).powi(2);
            (objective, sim_payload)
        };
        let mut best_scale = 1.0_f64;
        let mut best_objective = f64::INFINITY;
        let mut best_sim = simulate_for_factor_series(&working_factors);
        for candidate in &grid_values {
            let (objective_value, sim_payload) = segment_objective(*candidate);
            if objective_value < best_objective {
                best_objective = objective_value;
                best_scale = *candidate;
                best_sim = sim_payload;
            }
        }
        let mut local_step = 0.025_f64;
        for _ in 0..4 {
            for candidate in [
                best_scale - local_step,
                best_scale,
                best_scale + local_step,
            ] {
                let clipped = candidate.clamp(lower_bound, upper_bound);
                let (objective_value, sim_payload) = segment_objective(clipped);
                if objective_value < best_objective {
                    best_objective = objective_value;
                    best_scale = clipped;
                    best_sim = sim_payload;
                }
            }
            local_step *= 0.5;
        }
        for cycle_pos in (segment_start - 1)..segment_end {
            let candidate_value = (segment_base[cycle_pos] * best_scale).clamp(lower_bound, upper_bound);
            working_factors[cycle_pos] = candidate_value;
        }
        prev_anchor_idx = anchor_idx;
        previous_segment_scale = best_scale;
        if best_objective.is_finite() {
            objective_total += best_objective;
        }
        segment_rows.push((segment_start, segment_end, best_scale, false));
        let _ = best_sim;
    }
    if prev_anchor_idx < cycle_moles.len() {
        let tail_start = prev_anchor_idx + 1;
        for cycle_pos in prev_anchor_idx..cycle_moles.len() {
            let candidate_value =
                (working_factors[cycle_pos] * previous_segment_scale).clamp(lower_bound, upper_bound);
            working_factors[cycle_pos] = candidate_value;
        }
        segment_rows.push((tail_start, cycle_moles.len(), previous_segment_scale, true));
    }

    let final_sim = simulate_for_factor_series(&working_factors);
    let corrected_cycle_series = final_sim.corrected_cycle.clone();
    let corrected_cumulative_series = final_sim.corrected_cumulative.clone();
    let corrected_ph_series = final_sim.corrected_ph.clone();
    let corrected_fractions_series = final_sim.corrected_fractions.clone();
    let anchor_after_ph = corrected_ph_series
        .get(primary_anchor.cycle_index.saturating_sub(1))
        .copied()
        .flatten();
    let anchor_before_ph = prefit_baseline
        .corrected_ph
        .get(primary_anchor.cycle_index.saturating_sub(1))
        .copied()
        .flatten();
    let anchor_residual_before = anchor_before_ph.map(|value| value - primary_anchor.measured_ph);
    let anchor_residual_after = anchor_after_ph.map(|value| value - primary_anchor.measured_ph);
    let corrected_latest_total_mol = corrected_cumulative_series
        .last()
        .copied()
        .unwrap_or(0.0);

    let latest_fraction = corrected_fractions_series
        .last()
        .copied()
        .unwrap_or([0.0, 0.0, 0.0]);
    let latest_ph = corrected_ph_series.last().copied().flatten();

    let pre_slice = &working_factors[..split_idx];
    let alpha_pre = if pre_slice.is_empty() {
        1.0
    } else {
        pre_slice.iter().sum::<f64>() / (pre_slice.len() as f64)
    };
    let post_slice = &working_factors[split_idx..];
    let alpha_post = if post_slice.is_empty() {
        alpha_pre
    } else {
        post_slice.iter().sum::<f64>() / (post_slice.len() as f64)
    };
    let reference_total = planning_reference_total_mol
        .filter(|value| value.is_finite() && *value > 0.0);
    let eq_reference = equivalence_co2_mol.filter(|value| value.is_finite() && *value > 0.0);
    let co2_required_target_mol = if let Some(reference_total_value) = reference_total {
        let pre_reference = if let Some(eq_reference_value) = eq_reference {
            reference_total_value.min(eq_reference_value)
        } else {
            reference_total_value
        };
        let post_reference = (reference_total_value - pre_reference).max(0.0);
        Some(pre_reference * alpha_pre + post_reference * alpha_post)
    } else if let Some(eq_reference_value) = eq_reference {
        Some(eq_reference_value * alpha_pre)
    } else {
        None
    };
    let completion_pct = co2_required_target_mol.and_then(|required| {
        if required <= 1e-12 {
            None
        } else {
            Some((corrected_latest_total_mol / required).clamp(0.0, 1.0) * 100.0)
        }
    });

    let corrected_cycle_g_series: Vec<f64> = corrected_cycle_series
        .iter()
        .map(|value| value * SOL_MW_CO2)
        .collect();
    let corrected_cumulative_g_series: Vec<f64> = corrected_cumulative_series
        .iter()
        .map(|value| value * SOL_MW_CO2)
        .collect();

    let set_optional_f64 =
        |dict: &Bound<'_, PyDict>, key: &str, value: Option<f64>| -> PyResult<()> {
            if let Some(parsed) = value.filter(|item| item.is_finite()) {
                dict.set_item(key, parsed)?;
            } else {
                dict.set_item(key, py.None())?;
            }
            Ok(())
        };

    let response = PyDict::new(py);
    response.set_item("solver_status", "ok")?;
    response.set_item("solver_message", "")?;
    response.set_item("split_cycle_index", split_idx)?;
    response.set_item("anchor_cycle_index", primary_anchor.cycle_index)?;
    response.set_item("anchor_measured_ph", primary_anchor.measured_ph)?;
    set_optional_f64(&response, "anchor_predicted_ph_before", anchor_before_ph)?;
    set_optional_f64(&response, "anchor_predicted_ph_after", anchor_after_ph)?;
    set_optional_f64(&response, "anchor_residual_before", anchor_residual_before)?;
    set_optional_f64(&response, "anchor_residual_after", anchor_residual_after)?;
    if objective_total.is_finite() {
        response.set_item("objective", objective_total)?;
    } else {
        response.set_item("objective", py.None())?;
    }
    response.set_item("alpha_pre", alpha_pre)?;
    response.set_item("alpha_post", alpha_post)?;
    response.set_item("cycle_factor_series", working_factors.clone())?;
    response.set_item("learning_prior_applied", prior_applied)?;
    response.set_item("prior_sample_count", prior_sample_count)?;
    response.set_item("prior_cycle_factor_series", seed_factors.clone())?;
    let segment_list = PyList::empty(py);
    for (start_cycle, end_cycle, scale, tail_flag) in &segment_rows {
        let row = PyDict::new(py);
        row.set_item("start_cycle_index", *start_cycle)?;
        row.set_item("end_cycle_index", *end_cycle)?;
        row.set_item("scale", *scale)?;
        if *tail_flag {
            row.set_item("tail_extrapolation", true)?;
        }
        segment_list.append(row)?;
    }
    response.set_item("segment_scales", segment_list)?;
    let anchors_list = PyList::empty(py);
    for anchor in &normalized_anchors {
        let before_ph = prefit_baseline
            .corrected_ph
            .get(anchor.cycle_index.saturating_sub(1))
            .copied()
            .flatten();
        let after_ph = corrected_ph_series
            .get(anchor.cycle_index.saturating_sub(1))
            .copied()
            .flatten();
        let row = PyDict::new(py);
        row.set_item("cycle_index", anchor.cycle_index)?;
        row.set_item("measured_ph", anchor.measured_ph)?;
        row.set_item("source", anchor.source.clone())?;
        set_optional_f64(&row, "predicted_ph_before", before_ph)?;
        set_optional_f64(&row, "predicted_ph_after", after_ph)?;
        set_optional_f64(
            &row,
            "residual_before",
            before_ph.map(|value| value - anchor.measured_ph),
        )?;
        set_optional_f64(
            &row,
            "residual_after",
            after_ph.map(|value| value - anchor.measured_ph),
        )?;
        anchors_list.append(row)?;
    }
    response.set_item("anchors", anchors_list)?;
    response.set_item(
        "corrected_cycle_uptake_mol_series",
        corrected_cycle_series.clone(),
    )?;
    response.set_item(
        "corrected_cycle_uptake_g_series",
        corrected_cycle_g_series.clone(),
    )?;
    response.set_item(
        "corrected_cumulative_co2_mol_series",
        corrected_cumulative_series.clone(),
    )?;
    response.set_item(
        "corrected_cumulative_co2_g_series",
        corrected_cumulative_g_series.clone(),
    )?;

    let corrected_ph_list = PyList::empty(py);
    for value in corrected_ph_series {
        if let Some(parsed) = value.filter(|item| item.is_finite()) {
            corrected_ph_list.append(parsed)?;
        } else {
            corrected_ph_list.append(py.None())?;
        }
    }
    response.set_item("corrected_ph_series", corrected_ph_list)?;

    let fractions_list = PyList::empty(py);
    for fraction_row in corrected_fractions_series {
        let fraction_map = PyDict::new(py);
        fraction_map.set_item("H2CO3", fraction_row[0].max(0.0))?;
        fraction_map.set_item("HCO3-", fraction_row[1].max(0.0))?;
        fraction_map.set_item("CO3^2-", fraction_row[2].max(0.0))?;
        fractions_list.append(fraction_map)?;
    }
    response.set_item("corrected_fraction_series", fractions_list)?;

    let latest_speciation = PyDict::new(py);
    set_optional_f64(&latest_speciation, "ph", latest_ph)?;
    let latest_fractions_map = PyDict::new(py);
    latest_fractions_map.set_item("H2CO3", latest_fraction[0].max(0.0))?;
    latest_fractions_map.set_item("HCO3-", latest_fraction[1].max(0.0))?;
    latest_fractions_map.set_item("CO3^2-", latest_fraction[2].max(0.0))?;
    latest_speciation.set_item("fractions", latest_fractions_map)?;
    response.set_item("latest_corrected_speciation", latest_speciation)?;

    set_optional_f64(
        &response,
        "co2_required_for_target_ph_mol",
        co2_required_target_mol,
    )?;
    set_optional_f64(
        &response,
        "co2_required_for_target_ph_g",
        co2_required_target_mol.map(|value| value * SOL_MW_CO2),
    )?;
    response.set_item(
        "corrected_cumulative_uptake_latest_mol",
        corrected_latest_total_mol,
    )?;
    response.set_item(
        "corrected_cumulative_uptake_latest_g",
        corrected_latest_total_mol * SOL_MW_CO2,
    )?;
    set_optional_f64(
        &response,
        "completion_from_measured_ph_pct",
        completion_pct,
    )?;
    set_optional_f64(
        &response,
        "target_ph",
        target_ph.filter(|value| value.is_finite()),
    )?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (rows_a, rows_b))]
/// Compare aligned cycle rows from two datasets while preserving Python parity.
///
/// The output ordering and lookup rules intentionally mirror the Python
/// implementation so Compare tables remain backend-agnostic.
fn compare_aligned_cycle_rows_core(
    py: Python<'_>,
    rows_a: &Bound<'_, PyList>,
    rows_b: &Bound<'_, PyList>,
) -> PyResult<Py<PyList>> {
    // Keep Rust/Python parity for Compare cycle alignment and delta aggregation
    // so table math remains identical across backend selection.
    let uptake_keys = [
        "selected_mass_g",
        "selected_mass",
        "co2_added_g",
        "co2_added_mass_g",
        "co2_mass_g",
        "co2_g",
        "cycle_mass_g",
        "cycle_co2_mass_g",
    ];
    let cumulative_keys = [
        "cumulative_co2_mass_g",
        "cumulative_co2_added_mass_g",
        "cumulative_co2_added_g",
        "cumulative_co2_g",
        "cumulative_added_g",
        "cumulative_mass_g",
    ];

    let mut map_a: BTreeMap<usize, (Option<f64>, Option<f64>)> = BTreeMap::new();
    let mut map_b: BTreeMap<usize, (Option<f64>, Option<f64>)> = BTreeMap::new();

    for (idx, item) in rows_a.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let cycle_id = compare_cycle_row_index(&entry, idx + 1);
        if map_a.contains_key(&cycle_id) {
            continue;
        }
        let uptake = dict_optional_finite_by_keys(&entry, &uptake_keys);
        let cumulative = dict_optional_finite_by_keys(&entry, &cumulative_keys);
        map_a.insert(cycle_id, (uptake, cumulative));
    }
    for (idx, item) in rows_b.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let cycle_id = compare_cycle_row_index(&entry, idx + 1);
        if map_b.contains_key(&cycle_id) {
            continue;
        }
        let uptake = dict_optional_finite_by_keys(&entry, &uptake_keys);
        let cumulative = dict_optional_finite_by_keys(&entry, &cumulative_keys);
        map_b.insert(cycle_id, (uptake, cumulative));
    }

    let all_cycles: BTreeSet<usize> = map_a.keys().chain(map_b.keys()).copied().collect();
    let rows = PyList::empty(py);
    let mut last_cum_a = 0.0_f64;
    let mut last_cum_b = 0.0_f64;
    let mut valid_a = false;
    let mut valid_b = false;

    for cycle_id in all_cycles {
        let (mut uptake_a, mut cum_a) = map_a.get(&cycle_id).copied().unwrap_or((None, None));
        let (mut uptake_b, mut cum_b) = map_b.get(&cycle_id).copied().unwrap_or((None, None));
        let prior_cum_a = if valid_a { last_cum_a } else { 0.0 };
        let prior_cum_b = if valid_b { last_cum_b } else { 0.0 };

        if uptake_a.is_none() {
            if let Some(cum_val) = cum_a {
                uptake_a = Some(cum_val - prior_cum_a);
            }
        }
        if uptake_b.is_none() {
            if let Some(cum_val) = cum_b {
                uptake_b = Some(cum_val - prior_cum_b);
            }
        }
        if cum_a.is_none() {
            if let Some(uptake_val) = uptake_a {
                cum_a = Some(last_cum_a + uptake_val);
            }
        }
        if cum_b.is_none() {
            if let Some(uptake_val) = uptake_b {
                cum_b = Some(last_cum_b + uptake_val);
            }
        }
        if let Some(cum_val) = cum_a {
            last_cum_a = cum_val;
            valid_a = true;
        }
        if let Some(cum_val) = cum_b {
            last_cum_b = cum_val;
            valid_b = true;
        }
        let delta_g = match (uptake_a, uptake_b) {
            (Some(a), Some(b)) => Some(b - a),
            _ => None,
        };
        let cum_delta_g = match (cum_a, cum_b) {
            (Some(a), Some(b)) => Some(b - a),
            _ => None,
        };

        let row = PyDict::new(py);
        row.set_item("cycle", cycle_id)?;
        if let Some(value) = uptake_a {
            row.set_item("uptake_a_g", value)?;
        } else {
            row.set_item("uptake_a_g", py.None())?;
        }
        if let Some(value) = uptake_b {
            row.set_item("uptake_b_g", value)?;
        } else {
            row.set_item("uptake_b_g", py.None())?;
        }
        if let Some(value) = delta_g {
            row.set_item("delta_g", value)?;
        } else {
            row.set_item("delta_g", py.None())?;
        }
        if let Some(value) = cum_a {
            row.set_item("cum_a_g", value)?;
        } else {
            row.set_item("cum_a_g", py.None())?;
        }
        if let Some(value) = cum_b {
            row.set_item("cum_b_g", value)?;
        } else {
            row.set_item("cum_b_g", py.None())?;
        }
        if let Some(value) = cum_delta_g {
            row.set_item("cum_delta_g", value)?;
        } else {
            row.set_item("cum_delta_g", py.None())?;
        }
        rows.append(row)?;
    }
    Ok(rows.unbind())
}

#[pyfunction]
#[pyo3(signature = (entries, filter_value, sort_mode, sort_key, sort_desc, sort_column_type))]
/// Compute Ledger row indices after applying filter and sort rules.
///
/// Returning indices instead of rebuilt rows preserves the existing Python UI
/// update flow while allowing Rust to accelerate the expensive comparisons.
fn ledger_sort_filter_indices_core(
    entries: &Bound<'_, PyList>,
    filter_value: &str,
    sort_mode: &str,
    sort_key: &str,
    sort_desc: bool,
    sort_column_type: &str,
) -> PyResult<Option<Vec<usize>>> {
    // Prepare filtered/sorted row indices for Ledger table refresh while keeping
    // schema handling deterministic and fallback-safe.
    #[derive(Clone)]
    struct RowSortData {
        idx: usize,
        display_order: i64,
        updated_at: String,
        row_id: String,
        number_value: Option<f64>,
        date_value: Option<i64>,
        text_value: String,
    }

    let mode_token = match sort_mode.trim().to_ascii_lowercase().as_str() {
        "column" | "column sort" => "column",
        _ => "manual",
    };
    let column_type = sort_column_type.trim().to_ascii_lowercase();
    if mode_token == "column" && column_type == "formula" {
        return Ok(None);
    }
    let normalized_sort_key = {
        let candidate = sort_key.trim();
        if candidate.is_empty() {
            "updated_at"
        } else {
            candidate
        }
    };
    let filter_token = filter_value.trim().to_ascii_lowercase();
    let apply_filter = !filter_token.is_empty() && filter_token != "all profiles";
    let mut rows: Vec<RowSortData> = Vec::new();
    for (idx, item) in entries.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let profile_lower = dict_string_value(&entry, "profile_name").to_ascii_lowercase();
        if apply_filter && profile_lower != filter_token {
            continue;
        }
        let display_order = entry
            .get_item("display_order")
            .ok()
            .flatten()
            .and_then(|value| value.extract::<i64>().ok())
            .unwrap_or(0);
        let updated_at = dict_string_value(&entry, "updated_at");
        let row_id = dict_string_value(&entry, "id");
        let number_value = if column_type == "number" {
            ledger_sort_numeric_value(&entry, normalized_sort_key)
        } else {
            None
        };
        let date_value = if column_type == "date" {
            ledger_sort_date_value(&entry, normalized_sort_key)
        } else {
            None
        };
        let text_value = if column_type == "text" {
            ledger_sort_text_value(&entry, normalized_sort_key).to_ascii_lowercase()
        } else {
            String::new()
        };
        rows.push(RowSortData {
            idx,
            display_order,
            updated_at,
            row_id,
            number_value,
            date_value,
            text_value,
        });
    }

    if mode_token == "manual" {
        rows.sort_by(|left, right| {
            (
                left.display_order,
                left.updated_at.as_str(),
                left.row_id.as_str(),
            )
                .cmp(&(
                    right.display_order,
                    right.updated_at.as_str(),
                    right.row_id.as_str(),
                ))
        });
        return Ok(Some(rows.into_iter().map(|row| row.idx).collect()));
    }

    match column_type.as_str() {
        "number" => {
            rows.sort_by(|left, right| {
                let left_missing = left.number_value.is_none();
                let right_missing = right.number_value.is_none();
                if left_missing != right_missing {
                    return if sort_desc {
                        if left_missing {
                            Ordering::Less
                        } else {
                            Ordering::Greater
                        }
                    } else if left_missing {
                        Ordering::Greater
                    } else {
                        Ordering::Less
                    };
                }
                match (left.number_value, right.number_value) {
                    (Some(a), Some(b)) => {
                        if sort_desc {
                            b.partial_cmp(&a).unwrap_or(Ordering::Equal)
                        } else {
                            a.partial_cmp(&b).unwrap_or(Ordering::Equal)
                        }
                    }
                    _ => Ordering::Equal,
                }
            });
        }
        "date" => {
            rows.sort_by(|left, right| {
                let left_missing = left.date_value.is_none();
                let right_missing = right.date_value.is_none();
                if left_missing != right_missing {
                    return if sort_desc {
                        if left_missing {
                            Ordering::Less
                        } else {
                            Ordering::Greater
                        }
                    } else if left_missing {
                        Ordering::Greater
                    } else {
                        Ordering::Less
                    };
                }
                match (left.date_value, right.date_value) {
                    (Some(a), Some(b)) => {
                        if sort_desc {
                            b.cmp(&a)
                        } else {
                            a.cmp(&b)
                        }
                    }
                    _ => Ordering::Equal,
                }
            });
        }
        _ => {
            rows.sort_by(|left, right| {
                if sort_desc {
                    right.text_value.cmp(&left.text_value)
                } else {
                    left.text_value.cmp(&right.text_value)
                }
            });
        }
    }
    Ok(Some(rows.into_iter().map(|row| row.idx).collect()))
}

#[pyfunction]
#[pyo3(signature = (cycle_rows, total_drop_value=None, reaction_basis=None))]
/// Derive Ledger add-from-profile metrics from cycle rows and reaction inputs.
///
/// The function preserves the Python fallback schema while normalizing PyO3
/// ownership so row dictionaries can be retained safely across the loop.
fn ledger_prefill_metrics_core(
    py: Python<'_>,
    cycle_rows: &Bound<'_, PyList>,
    total_drop_value: Option<f64>,
    reaction_basis: Option<Bound<'_, PyDict>>,
) -> PyResult<Py<PyDict>> {
    // Extract Ledger add-from-profile metrics in Rust while preserving Python
    // fallback parity and schema expectations.
    let cumulative_keys = [
        "cumulative_co2_mass_g",
        "cumulative_co2_added_mass_g",
        "cumulative_co2_added_g",
        "cumulative_co2_g",
        "cumulative_added_g",
        "cumulative_mass_g",
    ];
    let mut normalized_rows: Vec<Bound<'_, PyDict>> = Vec::new();
    for item in cycle_rows.iter() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        normalized_rows.push(entry);
    }
    let mut total_drop = total_drop_value.filter(|value| value.is_finite() && *value >= 0.0);
    if total_drop.is_none() {
        if let Some(last_row) = normalized_rows.last() {
            total_drop = dict_optional_finite_by_keys(last_row, &cumulative_keys)
                .filter(|value| value.is_finite() && *value >= 0.0);
        }
    }
    let basis = reaction_basis.as_ref();
    let start_mass = basis.and_then(|dict| dict_optional_float_value(dict, "starting_mass_g"));
    let start_mw =
        basis.and_then(|dict| dict_optional_float_value(dict, "starting_material_mw_g_mol"));
    let stoich =
        basis.and_then(|dict| dict_optional_float_value(dict, "stoich_mol_gas_per_mol_starting"));
    let gas_mw = basis.and_then(|dict| dict_optional_float_value(dict, "gas_molar_mass"));
    let theoretical = match (start_mass, start_mw, stoich, gas_mw) {
        (Some(mass), Some(mw), Some(st), Some(gas))
            if mw > 0.0 && st > 0.0 && gas > 0.0 && mass >= 0.0 =>
        {
            Some((mass / mw) * st * gas)
        }
        _ => None,
    };
    let out = PyDict::new(py);
    if normalized_rows.is_empty() {
        out.set_item("cycles", py.None())?;
    } else {
        out.set_item("cycles", normalized_rows.len())?;
    }
    if let Some(value) = total_drop {
        out.set_item("total_dp_uptake", value)?;
    } else {
        out.set_item("total_dp_uptake", py.None())?;
    }
    if let Some(value) = theoretical {
        out.set_item("theoretical_yield_g", value)?;
    } else {
        out.set_item("theoretical_yield_g", py.None())?;
    }
    Ok(out.unbind())
}

#[pyfunction]
#[pyo3(signature = (x_values))]
fn array_signature_core(x_values: PyReadonlyArray1<'_, f64>) -> PyResult<(usize, String, i64)> {
    // Compute deterministic signed 64-bit FNV-1a hash for contiguous float bytes
    // so Python/Rust parity checks remain stable across process restarts.
    let view = x_values.as_array();
    let mut hash_value: u64 = 0xCBF29CE484222325;
    for value in view.iter() {
        let bytes = value.to_le_bytes();
        for byte_value in bytes {
            hash_value ^= u64::from(byte_value);
            hash_value = hash_value.wrapping_mul(0x100000001B3);
        }
    }
    let hash_i64 = i64::from_ne_bytes(hash_value.to_ne_bytes());
    Ok((view.len(), "float64".to_string(), hash_i64))
}

#[pyfunction]
#[pyo3(signature = (cycle_transfer_rows, duration_header))]
/// Format Final Report cycle-stat rows using the shared table schema.
///
/// Rust keeps the same column values and empty-string behavior expected by the
/// Python report builders, so exports remain identical across backends.
fn final_report_cycle_stats_rows_core(
    py: Python<'_>,
    cycle_transfer_rows: &Bound<'_, PyList>,
    duration_header: &str,
) -> PyResult<Py<PyList>> {
    // Format cycle-stat rows with the same schema expected by Python report
    // builders while keeping Rust wrappers strictly fallback-safe.
    let rows = PyList::empty(py);
    for item in cycle_transfer_rows.iter() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let delta = dict_optional_float_value(&entry, "delta_pressure_psi");
        let duration = dict_optional_float_value(&entry, "duration_x")
            .or_else(|| dict_optional_float_value(&entry, "duration"));
        let peak_psi = dict_optional_float_value(&entry, "peak_pressure_psi");
        let trough_psi = dict_optional_float_value(&entry, "trough_pressure_psi");
        let mean_temp = dict_optional_float_value(&entry, "mean_temperature_c");
        let co2_mass = dict_optional_float_value(&entry, "cumulative_co2_mass_g");
        let row = PyDict::new(py);
        row.set_item("Cycle", dict_truthy_or_empty_pyobject(py, &entry, "cycle_id"))?;
        row.set_item("\u{0394}P (PSI)", format_optional_decimal(delta, 2))?;
        row.set_item(duration_header, format_optional_decimal(duration, 3))?;
        row.set_item("Peak PSI", format_optional_decimal(peak_psi, 2))?;
        row.set_item("Trough PSI", format_optional_decimal(trough_psi, 2))?;
        row.set_item("Mean T (\u{00B0}C)", format_optional_decimal(mean_temp, 2))?;
        row.set_item("CO\u{2082} (g)", format_optional_decimal(co2_mass, 2))?;
        rows.append(row)?;
    }
    Ok(rows.unbind())
}

#[pyfunction]
#[pyo3(signature = (timeline_rows))]
/// Format Final Report timeline rows using the Rust speciation outputs.
///
/// The formatter keeps the existing table contract intact while using owned
/// PyO3 dictionary casts that are compatible with current PyO3 releases.
fn final_report_cycle_timeline_rows_core(
    py: Python<'_>,
    timeline_rows: &Bound<'_, PyList>,
) -> PyResult<Py<PyList>> {
    // Format timeline rows for Final Report preview/export table builders.
    let rows = PyList::empty(py);
    for item in timeline_rows.iter() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let co2_total = dict_optional_float_value(&entry, "co2_g")
            .or_else(|| dict_optional_float_value(&entry, "co2_mass_g"))
            .or_else(|| dict_optional_float_value(&entry, "cumulative_co2_added_mass_g"))
            .unwrap_or(0.0);
        let h2co3_fraction = normalize_fraction_value(extract_fraction_field(&entry, "H2CO3"));
        let hco3_fraction = normalize_fraction_value(extract_fraction_field(&entry, "HCO3-"));
        let co3_fraction = normalize_fraction_value(extract_fraction_field(&entry, "CO3^2-"));
        let ph_value = dict_optional_float_value(&entry, "solution_ph")
            .or_else(|| dict_optional_float_value(&entry, "speciation_ph"));
        let row = PyDict::new(py);
        row.set_item("Cycle", dict_truthy_or_empty_pyobject(py, &entry, "cycle_id"))?;
        row.set_item("CO\u{2082} total (g)", format!("{co2_total:.2}"))?;
        row.set_item("pH", format_optional_decimal(ph_value, 2))?;
        row.set_item("H\u{2082}CO\u{2083} (%)", format!("{:.1}", h2co3_fraction * 100.0))?;
        row.set_item("HCO\u{2083}\u{207B} (%)", format!("{:.1}", hco3_fraction * 100.0))?;
        row.set_item("CO\u{2083}\u{00B2}\u{207B} (%)", format!("{:.1}", co3_fraction * 100.0))?;
        rows.append(row)?;
    }
    Ok(rows.unbind())
}

#[pyfunction]
#[pyo3(signature = (timeline_rows))]
/// Normalize cycle timeline rows for staged table/callout rendering paths.
///
/// The function preserves passthrough fields from each source row while
/// coercing key numeric/fraction terms into a stable schema used by both
/// Rust and Python render payload builders.
fn cycle_timeline_normalize_core(
    py: Python<'_>,
    timeline_rows: &Bound<'_, PyList>,
) -> PyResult<Py<PyList>> {
    // Normalize mixed workflow timeline row payloads into one renderer-safe
    // schema without dropping unknown passthrough fields.
    let co2_total_keys = ["co2_g", "co2_mass_g", "cumulative_co2_added_mass_g"];
    let co2_cycle_keys = ["co2_mass_g", "cycle_co2_mass_g", "selected_mass_g"];
    let ph_keys = ["ph", "actual_ph", "solution_ph", "speciation_ph"];
    let actual_ph_keys = ["actual_ph", "ph"];
    let solution_ph_keys = ["solution_ph", "ph", "actual_ph"];
    let normalized_rows = PyList::empty(py);
    for (idx, item) in timeline_rows.iter().enumerate() {
        let Ok(entry) = item.cast_into::<PyDict>() else {
            continue;
        };
        let row = PyDict::new(py);
        for (key, value) in entry.iter() {
            row.set_item(key, value)?;
        }
        let cycle_id = compare_cycle_row_index(&entry, idx + 1);
        let co2_total = dict_optional_finite_by_keys(&entry, &co2_total_keys).unwrap_or(0.0);
        let co2_cycle = dict_optional_finite_by_keys(&entry, &co2_cycle_keys).unwrap_or(0.0);
        let ph_value = dict_optional_finite_by_keys(&entry, &ph_keys);
        let actual_ph = dict_optional_finite_by_keys(&entry, &actual_ph_keys);
        let solution_ph = dict_optional_finite_by_keys(&entry, &solution_ph_keys);
        let fractions = PyDict::new(py);
        fractions.set_item(
            "H2CO3",
            normalize_fraction_value(extract_fraction_field(&entry, "H2CO3")),
        )?;
        fractions.set_item(
            "HCO3-",
            normalize_fraction_value(extract_fraction_field(&entry, "HCO3-")),
        )?;
        fractions.set_item(
            "CO3^2-",
            normalize_fraction_value(extract_fraction_field(&entry, "CO3^2-")),
        )?;
        let warnings = PyList::empty(py);
        if let Some(warnings_any) = entry.get_item("warnings").ok().flatten() {
            if let Ok(warnings_list) = warnings_any.clone().cast_into::<PyList>() {
                for warning in warnings_list.iter() {
                    let text = py_any_to_trimmed_string(&warning);
                    if !text.is_empty() {
                        warnings.append(text)?;
                    }
                }
            } else {
                let warning_text = py_any_to_trimmed_string(&warnings_any);
                if !warning_text.is_empty() {
                    warnings.append(warning_text)?;
                }
            }
        }
        let analysis_prediction = PyDict::new(py);
        let mut prediction_target_ph: Option<f64> = None;
        let mut prediction_co2_to_target: Option<f64> = None;
        if let Some(prediction_any) = entry.get_item("analysis_prediction").ok().flatten() {
            if let Ok(prediction_map) = prediction_any.cast_into::<PyDict>() {
                prediction_target_ph =
                    dict_optional_finite_by_keys(&prediction_map, &["target_ph"]);
                prediction_co2_to_target =
                    dict_optional_finite_by_keys(&prediction_map, &["co2_to_target_g"]);
            }
        }
        if let Some(value) = prediction_target_ph {
            analysis_prediction.set_item("target_ph", value)?;
        } else {
            analysis_prediction.set_item("target_ph", py.None())?;
        }
        if let Some(value) = prediction_co2_to_target {
            analysis_prediction.set_item("co2_to_target_g", value)?;
        } else {
            analysis_prediction.set_item("co2_to_target_g", py.None())?;
        }
        row.set_item("cycle_id", cycle_id)?;
        row.set_item("co2_g", co2_total)?;
        row.set_item("co2_mass_g", co2_cycle)?;
        if let Some(value) = dict_optional_finite_by_keys(&entry, &["co2_to_target_g"]) {
            row.set_item("co2_to_target_g", value)?;
        } else {
            row.set_item("co2_to_target_g", py.None())?;
        }
        if let Some(value) = ph_value {
            row.set_item("ph", value)?;
        } else {
            row.set_item("ph", py.None())?;
        }
        if let Some(value) = actual_ph {
            row.set_item("actual_ph", value)?;
        } else {
            row.set_item("actual_ph", py.None())?;
        }
        if let Some(value) = solution_ph {
            row.set_item("solution_ph", value)?;
        } else {
            row.set_item("solution_ph", py.None())?;
        }
        for key in [
            "forecast_ph",
            "pco2_atm",
            "planning_cycle_ph",
            "planning_co2_aligned_ph",
            "ph_delta_cycle",
            "ph_delta_co2",
            "actual_cycle_co2_mol",
            "planning_cycle_co2_mol",
            "co2_mol_delta",
            "co2_mol_delta_pct",
            "actual_hco3_pct",
            "actual_co3_pct",
            "planning_hco3_pct",
            "planning_co3_pct",
            "hco3_pct_delta",
            "co3_pct_delta",
            "delta_pressure_psi",
            "co2_moles",
            "peak_pressure_psi",
            "trough_pressure_psi",
            "headspace_pressure_psi",
        ] {
            if let Some(value) = dict_optional_finite_by_keys(&entry, &[key]) {
                row.set_item(key, value)?;
            } else {
                row.set_item(key, py.None())?;
            }
        }
        row.set_item(
            "solid_na2co3_g",
            dict_optional_finite_by_keys(&entry, &["solid_na2co3_g"]).unwrap_or(0.0),
        )?;
        row.set_item(
            "solid_nahco3_g",
            dict_optional_finite_by_keys(&entry, &["solid_nahco3_g"]).unwrap_or(0.0),
        )?;
        row.set_item("alignment_quality_flag", dict_string_value(&entry, "alignment_quality_flag"))?;
        row.set_item("fractions", fractions)?;
        row.set_item("warnings", warnings)?;
        row.set_item("analysis_prediction", analysis_prediction)?;
        let error_flag = entry
            .get_item("error")
            .ok()
            .flatten()
            .and_then(|value| value.is_truthy().ok())
            .unwrap_or(false);
        row.set_item("error", error_flag)?;
        normalized_rows.append(row)?;
    }
    Ok(normalized_rows.unbind())
}

#[pyfunction]
/// Return Rust backend interface metadata consumed by Python capability checks.
fn rust_backend_manifest(py: Python<'_>) -> PyResult<Py<PyDict>> {
    let payload = PyDict::new(py);
    payload.set_item("interface_id", RUST_BACKEND_INTERFACE_ID)?;
    payload.set_item("interface_version", RUST_BACKEND_INTERFACE_VERSION)?;
    payload.set_item("crate_version", RUST_BACKEND_CRATE_VERSION)?;
    payload.set_item("module_name", RUST_BACKEND_MODULE_NAME)?;
    let exported_kernels = PyList::empty(py);
    for kernel_name in RUST_EXPORTED_KERNELS {
        exported_kernels.append(kernel_name)?;
    }
    payload.set_item("exported_kernels", exported_kernels)?;
    Ok(payload.unbind())
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

#[pyfunction]
#[pyo3(signature = (total_carbon_m, na_conc, ka1, ka2, kw, ionic_strength_cap=None, initial_ph_guess=8.35, speciation_mode="closed_carbon", fixed_h2co3=None))]
fn carbonate_state_core(
    py: Python<'_>,
    total_carbon_m: f64,
    na_conc: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    initial_ph_guess: f64,
    speciation_mode: &str,
    fixed_h2co3: Option<f64>,
) -> PyResult<Py<PyDict>> {
    let (h, hco3, co3, h2co3, oh, gammas, ionic_strength) = solve_carbonate_state_with_mode(
        total_carbon_m,
        na_conc,
        ka1,
        ka2,
        kw,
        ionic_strength_cap,
        initial_ph_guess,
        speciation_mode,
        fixed_h2co3,
    )
    .map_err(PyRuntimeError::new_err)?;
    let out = PyDict::new(py);
    let gamma_map = PyDict::new(py);
    gamma_map.set_item("Na", gammas[0])?;
    gamma_map.set_item("H", gammas[1])?;
    gamma_map.set_item("HCO3", gammas[2])?;
    gamma_map.set_item("CO3", gammas[3])?;
    gamma_map.set_item("OH", gammas[4])?;
    out.set_item("h", h)?;
    out.set_item("hco3", hco3)?;
    out.set_item("co3", co3)?;
    out.set_item("h2co3", h2co3)?;
    out.set_item("oh", oh)?;
    out.set_item("ionic_strength", ionic_strength)?;
    out.set_item("gammas", gamma_map)?;
    out.set_item("speciation_mode", normalize_speciation_mode(speciation_mode))?;
    Ok(out.unbind())
}

#[pyfunction]
#[pyo3(signature = (total_carbon_m, na_conc, forced_ph, ka1, ka2, kw, ionic_strength_cap=None, fixed_h2co3=None, max_iter=80))]
fn forced_ph_distribution_core(
    py: Python<'_>,
    total_carbon_m: f64,
    na_conc: f64,
    forced_ph: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ionic_strength_cap: Option<f64>,
    fixed_h2co3: Option<f64>,
    max_iter: usize,
) -> PyResult<Py<PyDict>> {
    let (total_carbon, h, hco3, co3, h2co3, oh, charge_residual, gammas, ionic_strength) =
        forced_ph_distribution_impl(
            total_carbon_m,
            na_conc,
            forced_ph,
            ka1,
            ka2,
            kw,
            ionic_strength_cap,
            fixed_h2co3,
            max_iter,
        )
        .map_err(PyRuntimeError::new_err)?;
    let out = PyDict::new(py);
    let gamma_map = PyDict::new(py);
    gamma_map.set_item("Na", gammas[0])?;
    gamma_map.set_item("H", gammas[1])?;
    gamma_map.set_item("HCO3", gammas[2])?;
    gamma_map.set_item("CO3", gammas[3])?;
    gamma_map.set_item("OH", gammas[4])?;
    out.set_item("total_carbon_m", total_carbon)?;
    out.set_item("h", h)?;
    out.set_item("hco3", hco3)?;
    out.set_item("co3", co3)?;
    out.set_item("h2co3", h2co3)?;
    out.set_item("oh", oh)?;
    out.set_item("charge_balance_residual", charge_residual)?;
    out.set_item("ionic_strength", ionic_strength)?;
    out.set_item("gammas", gamma_map)?;
    Ok(out.unbind())
}

#[pyfunction]
#[pyo3(signature = (total_inorganic_carbon_m, ka1=SOL_KA1, ka2=SOL_KA2, kw=SOL_KW, ph_low=AQION_DEFAULT_PH_LOW, ph_high=AQION_DEFAULT_PH_HIGH))]
fn aqion_closed_speciation_core(
    py: Python<'_>,
    total_inorganic_carbon_m: f64,
    ka1: f64,
    ka2: f64,
    kw: f64,
    ph_low: f64,
    ph_high: f64,
) -> PyResult<Py<PyDict>> {
    let (
        ph,
        h,
        oh,
        h2co3,
        hco3,
        co3,
        a0,
        a1,
        a2,
        ionic_strength,
        residual,
        solver_tag,
    ) = solve_aqion_closed_speciation(total_inorganic_carbon_m, ka1, ka2, kw, ph_low, ph_high)
        .map_err(PyRuntimeError::new_err)?;
    let out = PyDict::new(py);
    let species = PyDict::new(py);
    species.set_item("H+", h)?;
    species.set_item("H2CO3", h2co3)?;
    species.set_item("HCO3-", hco3)?;
    species.set_item("CO3^2-", co3)?;
    species.set_item("OH-", oh)?;
    let alpha = PyDict::new(py);
    alpha.set_item("a0", a0)?;
    alpha.set_item("a1", a1)?;
    alpha.set_item("a2", a2)?;
    out.set_item("ph", ph)?;
    out.set_item("h_conc", h)?;
    out.set_item("oh_conc", oh)?;
    out.set_item("species_m", species)?;
    out.set_item("alpha", alpha)?;
    out.set_item("ionic_strength", ionic_strength)?;
    out.set_item("charge_balance_residual", residual)?;
    out.set_item("solver", solver_tag)?;
    Ok(out.unbind())
}

#[pyfunction]
#[pyo3(signature = (total_carbon_m, total_sodium_m, pitzer_params, max_iter=60))]
fn pitzer_solve_total_carbon_core(
    py: Python<'_>,
    total_carbon_m: f64,
    total_sodium_m: f64,
    pitzer_params: &Bound<'_, PyDict>,
    max_iter: usize,
) -> PyResult<Option<Py<PyDict>>> {
    if total_carbon_m < 0.0 || total_sodium_m <= 0.0 {
        return Ok(None);
    }
    let parse = |key: &str| -> Option<f64> {
        let value = pitzer_params.get_item(key).ok().flatten()?;
        let parsed = value.extract::<f64>().ok()?;
        if parsed.is_finite() {
            Some(parsed)
        } else {
            None
        }
    };
    let Some(b0_na_oh) = parse("b0_na_oh") else {
        return Ok(None);
    };
    let Some(b1_na_oh) = parse("b1_na_oh") else {
        return Ok(None);
    };
    let Some(c0_na_oh) = parse("c0_na_oh") else {
        return Ok(None);
    };
    let Some(b0_na_hco3) = parse("b0_na_hco3") else {
        return Ok(None);
    };
    let Some(b1_na_hco3) = parse("b1_na_hco3") else {
        return Ok(None);
    };
    let Some(c0_na_hco3) = parse("c0_na_hco3") else {
        return Ok(None);
    };
    let Some(b0_na_co3) = parse("b0_na_co3") else {
        return Ok(None);
    };
    let Some(b1_na_co3) = parse("b1_na_co3") else {
        return Ok(None);
    };
    let Some(c0_na_co3) = parse("c0_na_co3") else {
        return Ok(None);
    };
    let Some(theta_co3_oh) = parse("theta_co3_oh") else {
        return Ok(None);
    };
    let Some(psi_co3_na_oh) = parse("psi_co3_na_oh") else {
        return Ok(None);
    };
    let Some(psi_co3_hco3_na) = parse("psi_co3_hco3_na") else {
        return Ok(None);
    };
    let params = PitzerParamsLite {
        b0_na_oh,
        b1_na_oh,
        c0_na_oh,
        b0_na_hco3,
        b1_na_hco3,
        c0_na_hco3,
        b0_na_co3,
        b1_na_co3,
        c0_na_co3,
        theta_co3_oh,
        psi_co3_na_oh,
        psi_co3_hco3_na,
    };
    let solved = solve_pitzer_total_carbon_impl(total_carbon_m, total_sodium_m, params, max_iter);
    let (ph, na, h, oh, hco3, co3, co2) = match solved {
        Ok(value) => value,
        Err(_) => return Ok(None),
    };
    if !ph.is_finite() {
        return Ok(None);
    }
    let out = PyDict::new(py);
    out.set_item("ph", ph)?;
    out.set_item("m_Na", na)?;
    out.set_item("m_H", h)?;
    out.set_item("m_OH", oh)?;
    out.set_item("m_HCO3", hco3)?;
    out.set_item("m_CO3", co3)?;
    out.set_item("m_CO2", co2)?;
    out.set_item("Na+", na)?;
    out.set_item("H+", h)?;
    out.set_item("OH-", oh)?;
    out.set_item("HCO3-", hco3)?;
    out.set_item("CO3-2", co3)?;
    out.set_item("CO2", co2)?;
    Ok(Some(out.unbind()))
}

fn dict_index_value(dict: &Bound<'_, PyDict>, key: &str) -> Option<usize> {
    let raw = dict
        .get_item(key)
        .ok()
        .flatten()
        .and_then(|value| value.extract::<isize>().ok())?;
    if raw < 0 {
        return None;
    }
    usize::try_from(raw).ok()
}

fn finite_value_or_nan(value: f64) -> f64 {
    if value.is_finite() {
        value
    } else {
        f64::NAN
    }
}

fn vdw_moles_from_delta_p(
    delta_p_atm: f64,
    volume_l: f64,
    temp_k: f64,
    a: f64,
    b: f64,
) -> Option<f64> {
    if !delta_p_atm.is_finite() || !volume_l.is_finite() || !temp_k.is_finite() {
        return None;
    }
    if delta_p_atm < 0.0 || volume_l <= 0.0 || temp_k <= 0.0 {
        return None;
    }
    let mut n = ((delta_p_atm * volume_l) / (CYCLE_GAS_CONSTANT * temp_k)).max(0.0);
    let upper = if b > 0.0 {
        (volume_l / b) * 0.999_999
    } else {
        f64::INFINITY
    };
    for _ in 0..60 {
        let conc = n / volume_l;
        let a_term = delta_p_atm + a * conc * conc;
        let f_val = a_term * (volume_l - n * b) - n * CYCLE_GAS_CONSTANT * temp_k;
        if !f_val.is_finite() {
            return None;
        }
        if f_val.abs() < 1e-12 {
            return Some(n.max(0.0));
        }
        let d_a_term = 2.0 * a * n / (volume_l * volume_l);
        let deriv = d_a_term * (volume_l - n * b) - (a_term * b) - (CYCLE_GAS_CONSTANT * temp_k);
        if !deriv.is_finite() || deriv.abs() <= 1e-14 {
            break;
        }
        let mut next = n - (f_val / deriv);
        if !next.is_finite() {
            return None;
        }
        if next < 0.0 {
            next = 0.5 * n;
        }
        if upper.is_finite() && next >= upper {
            next = 0.5 * (n + upper);
        }
        if (next - n).abs() <= 1e-12 {
            return Some(next.max(0.0));
        }
        n = next;
    }
    if n.is_finite() {
        Some(n.max(0.0))
    } else {
        None
    }
}

fn mean_temp_between(
    temp_values: Option<&PyReadonlyArray1<'_, f64>>,
    i: usize,
    j: usize,
    default_temp_c: f64,
) -> (f64, bool) {
    let Some(temp_arr) = temp_values else {
        return (default_temp_c, true);
    };
    let view = temp_arr.as_array();
    let len = view.len();
    if len == 0 {
        return (default_temp_c, true);
    }
    let mut lo = i.min(j);
    let hi = i.max(j).min(len.saturating_sub(1));
    if lo > hi {
        return (default_temp_c, true);
    }
    lo = lo.min(len.saturating_sub(1));
    let mut sum = 0.0_f64;
    let mut count = 0usize;
    for idx in lo..=hi {
        let value = view[idx];
        if value.is_finite() {
            sum += value;
            count += 1;
        }
    }
    if count == 0 {
        (default_temp_c, true)
    } else {
        (sum / count as f64, false)
    }
}

fn safe_array_value(values: Option<&PyReadonlyArray1<'_, f64>>, idx: usize) -> Option<f64> {
    let arr = values?;
    let view = arr.as_array();
    if idx >= view.len() {
        return None;
    }
    let value = view[idx];
    if value.is_finite() {
        Some(value)
    } else {
        None
    }
}

#[pyfunction]
#[pyo3(signature = (data_len, step, required_indices=None))]
fn combined_decimation_indices(
    data_len: usize,
    step: usize,
    required_indices: Option<Vec<isize>>,
) -> PyResult<Vec<usize>> {
    if data_len == 0 {
        return Ok(Vec::new());
    }
    let stride = step.max(1);
    let mut result = BTreeSet::new();
    let mut idx = 0usize;
    while idx < data_len {
        result.insert(idx);
        idx = idx.saturating_add(stride);
    }
    result.insert(data_len - 1);
    if let Some(required) = required_indices {
        for raw in required {
            if raw < 0 {
                continue;
            }
            let Ok(base) = usize::try_from(raw) else {
                continue;
            };
            if base >= data_len {
                continue;
            }
            result.insert(base);
            if base > 0 {
                result.insert(base - 1);
            }
            if base + 1 < data_len {
                result.insert(base + 1);
            }
        }
    }
    Ok(result.into_iter().collect())
}

#[pyfunction]
#[pyo3(signature = (x_values, series_values))]
fn combined_required_indices(
    x_values: PyReadonlyArray1<'_, f64>,
    series_values: &Bound<'_, PyList>,
) -> PyResult<Vec<usize>> {
    // Build the required-retention index set for combined preview decimation by
    // tracking non-finite x/y values that must be preserved across downsampling.
    let x_view = x_values.as_array();
    let data_len = x_view.len();
    let mut required = BTreeSet::new();
    for (idx, value) in x_view.iter().enumerate() {
        if !value.is_finite() {
            required.insert(idx);
        }
    }
    for item in series_values.iter() {
        let Ok(arr) = item.extract::<PyReadonlyArray1<'_, f64>>() else {
            continue;
        };
        let view = arr.as_array();
        if view.len() != data_len {
            continue;
        }
        for (idx, value) in view.iter().enumerate() {
            if !value.is_finite() {
                required.insert(idx);
            }
        }
    }
    Ok(required.into_iter().collect())
}

#[derive(Clone, Copy, Debug)]
struct CycleMarkerCandidate {
    compact_idx: usize,
    global_idx: usize,
    prominence: f64,
    curvature: f64,
    anchor_delta: usize,
}

fn normalize_window_size(window: usize) -> usize {
    let base = window.max(1);
    if base % 2 == 0 {
        base.saturating_add(1)
    } else {
        base
    }
}

fn transform_cycle_value(value: f64, prefer_peak: bool) -> f64 {
    if prefer_peak {
        value
    } else {
        -value
    }
}

fn moving_average_centered(values: &[f64], window: usize) -> Vec<f64> {
    let n = values.len();
    if n == 0 {
        return Vec::new();
    }
    let normalized = normalize_window_size(window);
    if normalized <= 1 || n <= 2 {
        return values.to_vec();
    }
    let half = normalized / 2;
    let mut smoothed = vec![0.0; n];
    for idx in 0..n {
        let start = idx.saturating_sub(half);
        let end = (idx + half + 1).min(n);
        let mut total = 0.0;
        let mut count = 0usize;
        for value in &values[start..end] {
            if value.is_finite() {
                total += *value;
                count += 1;
            }
        }
        smoothed[idx] = if count > 0 {
            total / count as f64
        } else {
            values[idx]
        };
    }
    smoothed
}

fn is_local_maximum(values: &[f64], idx: usize) -> bool {
    if values.is_empty() || idx >= values.len() {
        return false;
    }
    let center = values[idx];
    if !center.is_finite() {
        return false;
    }
    let left_ok = if idx == 0 {
        false
    } else {
        let left = values[idx - 1];
        left.is_finite() && center >= left
    };
    let right_ok = if idx + 1 >= values.len() {
        false
    } else {
        let right = values[idx + 1];
        right.is_finite() && center >= right
    };
    let strictly_higher = (idx > 0 && center > values[idx - 1])
        || (idx + 1 < values.len() && center > values[idx + 1]);
    left_ok && right_ok && strictly_higher
}

fn local_maxima_positions(values: &[f64]) -> Vec<usize> {
    let mut maxima = Vec::new();
    if values.len() < 3 {
        return maxima;
    }
    for idx in 1..(values.len() - 1) {
        if is_local_maximum(values, idx) {
            maxima.push(idx);
        }
    }
    maxima
}

fn estimate_peak_prominence(values: &[f64], idx: usize) -> f64 {
    if values.is_empty() || idx >= values.len() {
        return 0.0;
    }
    let peak = values[idx];
    if !peak.is_finite() {
        return 0.0;
    }
    let mut left_min = peak;
    let mut j = idx;
    while j > 0 {
        j -= 1;
        let value = values[j];
        if !value.is_finite() {
            continue;
        }
        left_min = left_min.min(value);
        if value > peak {
            break;
        }
    }
    let mut right_min = peak;
    let mut k = idx;
    while k + 1 < values.len() {
        k += 1;
        let value = values[k];
        if !value.is_finite() {
            continue;
        }
        right_min = right_min.min(value);
        if value > peak {
            break;
        }
    }
    (peak - left_min.max(right_min)).max(0.0)
}

fn estimate_peak_width(values: &[f64], idx: usize, prominence: f64) -> usize {
    if values.is_empty() || idx >= values.len() {
        return 0;
    }
    let peak = values[idx];
    if !peak.is_finite() || !prominence.is_finite() || prominence <= 0.0 {
        return 0;
    }
    let threshold = peak - (prominence * 0.5);
    let mut left = idx;
    while left > 0 {
        let value = values[left];
        let prev = values[left - 1];
        if !value.is_finite() || !prev.is_finite() || prev < threshold {
            break;
        }
        left -= 1;
    }
    let mut right = idx;
    while right + 1 < values.len() {
        let value = values[right];
        let next = values[right + 1];
        if !value.is_finite() || !next.is_finite() || next < threshold {
            break;
        }
        right += 1;
    }
    right.saturating_sub(left).saturating_add(1)
}

fn estimate_peak_curvature(values: &[f64], idx: usize) -> f64 {
    if idx == 0 || idx + 1 >= values.len() {
        return 0.0;
    }
    let prev = values[idx - 1];
    let center = values[idx];
    let next = values[idx + 1];
    if !(prev.is_finite() && center.is_finite() && next.is_finite()) {
        return 0.0;
    }
    (2.0 * center - prev - next).abs()
}

fn refine_peak_candidate(
    transformed_raw: &[f64],
    compact_idx: usize,
    refine_radius: usize,
) -> usize {
    if transformed_raw.is_empty() {
        return 0;
    }
    let start = compact_idx.saturating_sub(refine_radius);
    let end = (compact_idx + refine_radius + 1).min(transformed_raw.len());
    let mut best_idx = compact_idx.min(transformed_raw.len() - 1);
    let mut best_value = transformed_raw[best_idx];
    let mut best_delta = usize::MAX;
    for idx in start..end {
        let value = transformed_raw[idx];
        if !value.is_finite() {
            continue;
        }
        let local_ok = is_local_maximum(transformed_raw, idx);
        let delta = idx.abs_diff(compact_idx);
        if local_ok
            && (
                !best_value.is_finite()
                    || value > best_value
                    || (value == best_value && delta < best_delta)
            )
        {
            best_idx = idx;
            best_value = value;
            best_delta = delta;
        }
    }
    if is_local_maximum(transformed_raw, best_idx) {
        return best_idx;
    }
    for idx in start..end {
        let value = transformed_raw[idx];
        if !value.is_finite() {
            continue;
        }
        let delta = idx.abs_diff(compact_idx);
        if !best_value.is_finite() || value > best_value || (value == best_value && delta < best_delta)
        {
            best_idx = idx;
            best_value = value;
            best_delta = delta;
        }
    }
    best_idx
}

fn collapse_refined_candidates(
    compact_to_global: &[usize],
    transformed_raw: &[f64],
    candidates: &[usize],
    refine_radius: usize,
) -> Vec<CycleMarkerCandidate> {
    let mut refined_map: BTreeMap<usize, CycleMarkerCandidate> = BTreeMap::new();
    for compact_idx in candidates {
        if *compact_idx >= compact_to_global.len() {
            continue;
        }
        let refined_idx = refine_peak_candidate(transformed_raw, *compact_idx, refine_radius);
        if refined_idx >= compact_to_global.len() {
            continue;
        }
        let global_idx = compact_to_global[refined_idx];
        let prominence = estimate_peak_prominence(transformed_raw, refined_idx);
        let curvature = estimate_peak_curvature(transformed_raw, refined_idx);
        let candidate = CycleMarkerCandidate {
            compact_idx: refined_idx,
            global_idx,
            prominence,
            curvature,
            anchor_delta: refined_idx.abs_diff(*compact_idx),
        };
        match refined_map.get(&global_idx) {
            Some(existing)
                if existing.prominence > candidate.prominence
                    || (existing.prominence == candidate.prominence
                        && existing.curvature >= candidate.curvature) => {}
            _ => {
                refined_map.insert(global_idx, candidate);
            }
        }
    }
    refined_map.into_values().collect()
}

fn select_distance_filtered_candidates(
    candidates: &mut Vec<CycleMarkerCandidate>,
    min_distance: usize,
) -> Vec<CycleMarkerCandidate> {
    candidates.sort_by(|left, right| {
        right
            .prominence
            .partial_cmp(&left.prominence)
            .unwrap_or(Ordering::Equal)
            .then_with(|| {
                right
                    .curvature
                    .partial_cmp(&left.curvature)
                    .unwrap_or(Ordering::Equal)
            })
            .then_with(|| left.global_idx.cmp(&right.global_idx))
    });
    let mut selected: Vec<CycleMarkerCandidate> = Vec::new();
    for candidate in candidates.iter().copied() {
        if selected
            .iter()
            .any(|existing| existing.global_idx.abs_diff(candidate.global_idx) < min_distance)
        {
            continue;
        }
        selected.push(candidate);
    }
    selected.sort_by_key(|item| item.global_idx);
    selected
}

fn build_cycle_candidates(
    compact_to_global: &[usize],
    raw_values: &[f64],
    prefer_peak: bool,
    prominence_threshold: f64,
    min_distance: usize,
    min_width: usize,
    smoothing_window: usize,
    refine_radius: usize,
) -> Vec<CycleMarkerCandidate> {
    if compact_to_global.len() < 3 || raw_values.len() < 3 {
        return Vec::new();
    }
    let transformed_raw: Vec<f64> = raw_values
        .iter()
        .map(|value| transform_cycle_value(*value, prefer_peak))
        .collect();
    let transformed_smoothed = moving_average_centered(&transformed_raw, smoothing_window);
    let maxima = local_maxima_positions(&transformed_smoothed);
    let mut prefiltered: Vec<usize> = Vec::new();
    for idx in maxima {
        let prominence = estimate_peak_prominence(&transformed_smoothed, idx);
        if prominence < prominence_threshold {
            continue;
        }
        let width = estimate_peak_width(&transformed_smoothed, idx, prominence);
        if width < min_width {
            continue;
        }
        prefiltered.push(idx);
    }
    let mut refined = collapse_refined_candidates(
        compact_to_global,
        &transformed_raw,
        &prefiltered,
        refine_radius.max(1),
    );
    for item in &mut refined {
        item.prominence = estimate_peak_prominence(&transformed_raw, item.compact_idx);
        item.curvature = estimate_peak_curvature(&transformed_raw, item.compact_idx);
    }
    select_distance_filtered_candidates(&mut refined, min_distance.max(1))
}

fn auto_snap_window(selection_len: usize) -> usize {
    if selection_len == 0 {
        return 6;
    }
    let by_percent = ((selection_len as f64) * 0.01).round() as usize;
    by_percent.max(6).min(80)
}

fn best_manual_candidate(
    compact_x: &[f64],
    compact_y: &[f64],
    x_target: f64,
    prefer_peak: bool,
    snap_radius: usize,
    smoothing_window: usize,
) -> Option<(CycleMarkerCandidate, f64)> {
    if compact_x.len() < 3 || compact_y.len() < 3 || !x_target.is_finite() {
        return None;
    }
    let mut anchor_idx = 0usize;
    let mut best_anchor_dx = f64::INFINITY;
    for (idx, x_value) in compact_x.iter().enumerate() {
        if !x_value.is_finite() {
            continue;
        }
        let delta = (*x_value - x_target).abs();
        if delta < best_anchor_dx {
            best_anchor_dx = delta;
            anchor_idx = idx;
        }
    }
    let window_radius = if snap_radius == 0 {
        auto_snap_window(compact_x.len())
    } else {
        snap_radius.max(1)
    };
    let window_start = anchor_idx.saturating_sub(window_radius);
    let window_end = (anchor_idx + window_radius + 1).min(compact_x.len());
    let local_to_global: Vec<usize> = (window_start..window_end).collect();
    let local_y = &compact_y[window_start..window_end];
    let transformed_local: Vec<f64> = local_y
        .iter()
        .map(|value| transform_cycle_value(*value, prefer_peak))
        .collect();
    let smoothed_local = moving_average_centered(&transformed_local, smoothing_window);
    let maxima = local_maxima_positions(&smoothed_local);
    let refine_radius = (normalize_window_size(smoothing_window) / 2).max(2);
    let mut refined = collapse_refined_candidates(
        &local_to_global,
        &transformed_local,
        &maxima,
        refine_radius,
    );
    if refined.is_empty() {
        let compact_candidate = refine_peak_candidate(
            &transformed_local,
            anchor_idx.saturating_sub(window_start).min(transformed_local.len() - 1),
            refine_radius,
        );
        let global_idx = window_start + compact_candidate;
        refined.push(CycleMarkerCandidate {
            compact_idx: global_idx,
            global_idx,
            prominence: estimate_peak_prominence(
                &compact_y
                    .iter()
                    .map(|value| transform_cycle_value(*value, prefer_peak))
                    .collect::<Vec<f64>>(),
                global_idx,
            ),
            curvature: estimate_peak_curvature(
                &compact_y
                    .iter()
                    .map(|value| transform_cycle_value(*value, prefer_peak))
                    .collect::<Vec<f64>>(),
                global_idx,
            ),
            anchor_delta: global_idx.abs_diff(anchor_idx),
        });
    }
    let transformed_full: Vec<f64> = compact_y
        .iter()
        .map(|value| transform_cycle_value(*value, prefer_peak))
        .collect();
    let mut best: Option<(CycleMarkerCandidate, f64, f64, usize)> = None;
    for mut candidate in refined {
        candidate.prominence = estimate_peak_prominence(&transformed_full, candidate.global_idx);
        candidate.curvature = estimate_peak_curvature(&transformed_full, candidate.global_idx);
        let x_distance = (compact_x[candidate.global_idx] - x_target).abs();
        let metric = (candidate.prominence, -x_distance, candidate.curvature, -(candidate.anchor_delta as f64));
        let score =
            candidate.prominence * 1000.0 + candidate.curvature * 50.0 - x_distance - candidate.anchor_delta as f64 * 0.01;
        match best {
            Some((existing, existing_dx, existing_score, existing_delta))
                if existing.prominence > metric.0
                    || (existing.prominence == metric.0 && existing_dx < x_distance)
                    || (existing.prominence == metric.0
                        && existing_dx == x_distance
                        && existing.curvature > metric.2)
                    || (existing.prominence == metric.0
                        && existing_dx == x_distance
                        && existing.curvature == metric.2
                        && existing_delta <= candidate.anchor_delta) =>
            {
                let _ = existing_score;
            }
            _ => {
                best = Some((candidate, x_distance, score, candidate.anchor_delta));
            }
        }
    }
    best.map(|(candidate, _dx, score, _delta)| (candidate, score))
}

#[pyfunction]
#[pyo3(signature = (x_values, y_values, mask, prominence, distance, width, smoothing_window=1, refine_radius=6))]
fn cycle_detect_markers_core(
    py: Python<'_>,
    x_values: PyReadonlyArray1<'_, f64>,
    y_values: PyReadonlyArray1<'_, f64>,
    mask: PyReadonlyArray1<'_, bool>,
    prominence: f64,
    distance: usize,
    width: usize,
    smoothing_window: usize,
    refine_radius: usize,
) -> PyResult<Py<PyDict>> {
    let x_view = x_values.as_array();
    let y_view = y_values.as_array();
    let mask_view = mask.as_array();
    let data_len = x_view.len().min(y_view.len()).min(mask_view.len());
    let response = PyDict::new(py);
    if data_len < 3 {
        response.set_item("auto_peaks", Vec::<usize>::new())?;
        response.set_item("auto_troughs", Vec::<usize>::new())?;
        response.set_item("debug", PyDict::new(py))?;
        return Ok(response.unbind());
    }
    let mut compact_to_global: Vec<usize> = Vec::new();
    let mut compact_x: Vec<f64> = Vec::new();
    let mut compact_y: Vec<f64> = Vec::new();
    for idx in 0..data_len {
        let x_val = x_view[idx];
        let y_val = y_view[idx];
        if mask_view[idx] && x_val.is_finite() && y_val.is_finite() {
            compact_to_global.push(idx);
            compact_x.push(x_val);
            compact_y.push(y_val);
        }
    }
    if compact_to_global.len() < 3 {
        response.set_item("auto_peaks", Vec::<usize>::new())?;
        response.set_item("auto_troughs", Vec::<usize>::new())?;
        response.set_item("debug", PyDict::new(py))?;
        return Ok(response.unbind());
    }
    let peaks = build_cycle_candidates(
        &compact_to_global,
        &compact_y,
        true,
        if prominence.is_finite() { prominence.max(0.0) } else { 0.0 },
        distance.max(1),
        width.max(1),
        smoothing_window.max(1),
        refine_radius.max(1),
    );
    let troughs = build_cycle_candidates(
        &compact_to_global,
        &compact_y,
        false,
        if prominence.is_finite() { prominence.max(0.0) } else { 0.0 },
        distance.max(1),
        width.max(1),
        smoothing_window.max(1),
        refine_radius.max(1),
    );
    let debug = PyDict::new(py);
    debug.set_item("selection_size", compact_to_global.len())?;
    debug.set_item("smoothing_window", normalize_window_size(smoothing_window))?;
    debug.set_item("refine_radius", refine_radius.max(1))?;
    debug.set_item("peak_candidates", peaks.len())?;
    debug.set_item("trough_candidates", troughs.len())?;
    response.set_item(
        "auto_peaks",
        peaks.iter().map(|item| item.global_idx).collect::<Vec<usize>>(),
    )?;
    response.set_item(
        "auto_troughs",
        troughs.iter().map(|item| item.global_idx).collect::<Vec<usize>>(),
    )?;
    response.set_item("debug", debug)?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (x_values, y_values, mask, x_target, y_target=None, prefer_peak=true, snap_radius=0, smoothing_window=1))]
fn cycle_manual_snap_core(
    py: Python<'_>,
    x_values: PyReadonlyArray1<'_, f64>,
    y_values: PyReadonlyArray1<'_, f64>,
    mask: PyReadonlyArray1<'_, bool>,
    x_target: f64,
    y_target: Option<f64>,
    prefer_peak: bool,
    snap_radius: usize,
    smoothing_window: usize,
) -> PyResult<Py<PyDict>> {
    let x_view = x_values.as_array();
    let y_view = y_values.as_array();
    let mask_view = mask.as_array();
    let data_len = x_view.len().min(y_view.len()).min(mask_view.len());
    let response = PyDict::new(py);
    if data_len < 3 || !x_target.is_finite() {
        response.set_item("index", py.None())?;
        response.set_item("x", py.None())?;
        response.set_item("y", py.None())?;
        response.set_item("prominence", py.None())?;
        response.set_item("score", py.None())?;
        return Ok(response.unbind());
    }
    let mut compact_x: Vec<f64> = Vec::new();
    let mut compact_y: Vec<f64> = Vec::new();
    let mut compact_to_global: Vec<usize> = Vec::new();
    for idx in 0..data_len {
        let x_val = x_view[idx];
        let y_val = y_view[idx];
        if mask_view[idx] && x_val.is_finite() && y_val.is_finite() {
            compact_x.push(x_val);
            compact_y.push(y_val);
            compact_to_global.push(idx);
        }
    }
    if compact_x.len() < 3 {
        response.set_item("index", py.None())?;
        response.set_item("x", py.None())?;
        response.set_item("y", py.None())?;
        response.set_item("prominence", py.None())?;
        response.set_item("score", py.None())?;
        return Ok(response.unbind());
    }
    if let Some((candidate, score)) = best_manual_candidate(
        &compact_x,
        &compact_y,
        x_target,
        prefer_peak,
        snap_radius,
        smoothing_window.max(1),
    ) {
        let global_idx = compact_to_global[candidate.global_idx];
        response.set_item("index", global_idx)?;
        response.set_item("x", compact_x[candidate.global_idx])?;
        response.set_item("y", compact_y[candidate.global_idx])?;
        response.set_item("prominence", candidate.prominence)?;
        let y_bonus = if let Some(target) = y_target {
            if target.is_finite() {
                -(compact_y[candidate.global_idx] - target).abs() * 0.001
            } else {
                0.0
            }
        } else {
            0.0
        };
        response.set_item("score", score + y_bonus)?;
    } else {
        response.set_item("index", py.None())?;
        response.set_item("x", py.None())?;
        response.set_item("y", py.None())?;
        response.set_item("prominence", py.None())?;
        response.set_item("score", py.None())?;
    }
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (x_values, y_values, peak_indices, trough_indices))]
fn cycle_overlay_points_core(
    py: Python<'_>,
    x_values: PyReadonlyArray1<'_, f64>,
    y_values: PyReadonlyArray1<'_, f64>,
    peak_indices: Vec<isize>,
    trough_indices: Vec<isize>,
) -> PyResult<Py<PyDict>> {
    let x_view = x_values.as_array();
    let y_view = y_values.as_array();
    let data_len = x_view.len().min(y_view.len());
    let sanitize = |values: &[isize]| -> Vec<usize> {
        let mut out = BTreeSet::new();
        for raw in values {
            if *raw < 0 {
                continue;
            }
            let Ok(idx) = usize::try_from(*raw) else {
                continue;
            };
            if idx < data_len {
                out.insert(idx);
            }
        }
        out.into_iter().collect()
    };
    let build_points = |indices: &[usize]| -> Vec<(f64, f64)> {
        let mut points = Vec::new();
        for idx in indices {
            if *idx >= data_len {
                continue;
            }
            let x_val = x_view[*idx];
            let y_val = y_view[*idx];
            if x_val.is_finite() && y_val.is_finite() {
                points.push((x_val, y_val));
            }
        }
        points
    };
    let safe_peaks = sanitize(&peak_indices);
    let safe_troughs = sanitize(&trough_indices);
    let response = PyDict::new(py);
    response.set_item("peak_points", build_points(&safe_peaks))?;
    response.set_item("trough_points", build_points(&safe_troughs))?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (y_values, mask, auto_peaks, auto_troughs, add_peaks, add_troughs, rm_peaks, rm_troughs, min_cycle_drop, ignore_min_drop=false, manual_only=false))]
fn cycle_segmentation_core(
    py: Python<'_>,
    y_values: PyReadonlyArray1<'_, f64>,
    mask: PyReadonlyArray1<'_, bool>,
    auto_peaks: Vec<isize>,
    auto_troughs: Vec<isize>,
    add_peaks: Vec<isize>,
    add_troughs: Vec<isize>,
    rm_peaks: Vec<isize>,
    rm_troughs: Vec<isize>,
    min_cycle_drop: f64,
    ignore_min_drop: bool,
    manual_only: bool,
) -> PyResult<Py<PyDict>> {
    let y_view = y_values.as_array();
    let mask_view = mask.as_array();
    let mask_len = y_view.len().min(mask_view.len());
    let response = PyDict::new(py);
    let empty_cycles = PyList::empty(py);
    if mask_len == 0 {
        response.set_item("peaks", Vec::<usize>::new())?;
        response.set_item("troughs", Vec::<usize>::new())?;
        response.set_item("plot_peaks", Vec::<usize>::new())?;
        response.set_item("plot_troughs", Vec::<usize>::new())?;
        response.set_item("cycles", empty_cycles)?;
        response.set_item("total_drop", 0.0_f64)?;
        response.set_item("selection_size", 0usize)?;
        return Ok(response.unbind());
    }

    let sanitize = |values: &[isize]| -> BTreeSet<usize> {
        values
            .iter()
            .filter_map(|raw| {
                if *raw < 0 {
                    return None;
                }
                let idx = usize::try_from(*raw).ok()?;
                if idx < mask_len {
                    Some(idx)
                } else {
                    None
                }
            })
            .collect()
    };

    let auto_peaks_set = sanitize(&auto_peaks);
    let auto_troughs_set = sanitize(&auto_troughs);
    let add_peaks_set = sanitize(&add_peaks);
    let add_troughs_set = sanitize(&add_troughs);
    let rm_peaks_set = sanitize(&rm_peaks);
    let rm_troughs_set = sanitize(&rm_troughs);

    let effective_peaks: BTreeSet<usize> = if manual_only {
        add_peaks_set.clone()
    } else {
        auto_peaks_set
            .union(&add_peaks_set)
            .copied()
            .collect::<BTreeSet<_>>()
            .difference(&rm_peaks_set)
            .copied()
            .collect()
    };
    let effective_troughs: BTreeSet<usize> = if manual_only {
        add_troughs_set.clone()
    } else {
        auto_troughs_set
            .union(&add_troughs_set)
            .copied()
            .collect::<BTreeSet<_>>()
            .difference(&rm_troughs_set)
            .copied()
            .collect()
    };

    let peaks: Vec<usize> = effective_peaks
        .iter()
        .copied()
        .filter(|idx| *idx < mask_len && mask_view[*idx])
        .collect();
    let troughs: Vec<usize> = effective_troughs
        .iter()
        .copied()
        .filter(|idx| *idx < mask_len && mask_view[*idx])
        .collect();

    let threshold = if ignore_min_drop {
        f64::NEG_INFINITY
    } else {
        min_cycle_drop
    };
    let mut cycles = PyList::empty(py);
    let mut total_drop = 0.0_f64;
    let mut cycle_peaks = BTreeSet::new();
    let mut cycle_troughs = BTreeSet::new();
    let mut t_ptr = 0usize;
    for peak_idx in &peaks {
        while t_ptr < troughs.len() && troughs[t_ptr] <= *peak_idx {
            t_ptr += 1;
        }
        if t_ptr >= troughs.len() {
            break;
        }
        let trough_idx = troughs[t_ptr];
        let peak_value = y_view[*peak_idx];
        let trough_value = y_view[trough_idx];
        let delta_p = peak_value - trough_value;
        if delta_p >= threshold {
            let row = PyDict::new(py);
            row.set_item("peak_idx", *peak_idx)?;
            row.set_item("trough_idx", trough_idx)?;
            row.set_item("peak", peak_value)?;
            row.set_item("trough", trough_value)?;
            row.set_item("delta_P", delta_p)?;
            cycles.append(row)?;
            total_drop += delta_p;
            cycle_peaks.insert(*peak_idx);
            cycle_troughs.insert(trough_idx);
        }
    }

    let display_peaks: BTreeSet<usize> = effective_peaks
        .iter()
        .copied()
        .filter(|idx| *idx < mask_len && mask_view[*idx])
        .collect();
    let display_troughs: BTreeSet<usize> = effective_troughs
        .iter()
        .copied()
        .filter(|idx| *idx < mask_len && mask_view[*idx])
        .collect();
    let plot_peaks: Vec<usize> = cycle_peaks.union(&display_peaks).copied().collect();
    let plot_troughs: Vec<usize> = cycle_troughs.union(&display_troughs).copied().collect();

    response.set_item("peaks", peaks)?;
    response.set_item("troughs", troughs)?;
    response.set_item("plot_peaks", plot_peaks)?;
    response.set_item("plot_troughs", plot_troughs)?;
    response.set_item("cycles", cycles)?;
    response.set_item("total_drop", total_drop)?;
    response.set_item(
        "selection_size",
        mask_view
            .iter()
            .take(mask_len)
            .filter(|value| **value)
            .count(),
    )?;
    Ok(response.unbind())
}

#[pyfunction]
#[pyo3(signature = (cycles, temp_values=None, x_values=None, volume_l=1.0, a_const=1.39, b_const=0.0391, gas_molar_mass=44.0095, x_label="Elapsed Time (days)", compute_vdw=false, default_temp_c=25.0))]
/// Compute per-cycle gas metrics for overlay tables and exported summaries.
///
/// The function consumes cycle dictionaries from Python and keeps the same field
/// semantics as the Python backend while supporting free-threaded imports.
fn cycle_metrics_core(
    py: Python<'_>,
    cycles: &Bound<'_, PyList>,
    temp_values: Option<PyReadonlyArray1<'_, f64>>,
    x_values: Option<PyReadonlyArray1<'_, f64>>,
    volume_l: f64,
    a_const: f64,
    b_const: f64,
    gas_molar_mass: f64,
    x_label: &str,
    compute_vdw: bool,
    default_temp_c: f64,
) -> PyResult<Py<PyDict>> {
    let v_l = if volume_l.is_finite() && volume_l > 0.0 {
        volume_l
    } else {
        1.0
    };
    let a_vdw = if a_const.is_finite() { a_const } else { 1.39 };
    let b_vdw = if b_const.is_finite() { b_const } else { 0.0391 };
    let molar_mass = if gas_molar_mass.is_finite() && gas_molar_mass > 0.0 {
        gas_molar_mass
    } else {
        44.0095
    };
    let default_temp = if default_temp_c.is_finite() {
        default_temp_c
    } else {
        25.0
    };
    let per_cycle = PyList::empty(py);
    let transfer_rows = PyList::empty(py);
    let mut total_ideal = 0.0_f64;
    let mut total_vdw = 0.0_f64;
    let mut cumulative_moles = 0.0_f64;

    for (cycle_idx, item) in cycles.iter().enumerate() {
        let Ok(cycle_dict) = item.cast_into::<PyDict>() else {
            continue;
        };
        let Some(peak_idx) = dict_index_value(&cycle_dict, "peak_idx") else {
            continue;
        };
        let Some(trough_idx) = dict_index_value(&cycle_dict, "trough_idx") else {
            continue;
        };
        let peak_pressure = dict_float_value(&cycle_dict, "peak");
        let trough_pressure = dict_float_value(&cycle_dict, "trough");
        let mut delta_psi = dict_float_value(&cycle_dict, "delta_P");
        if !delta_psi.is_finite() {
            delta_psi = peak_pressure - trough_pressure;
        }
        let delta_atm = if delta_psi.is_finite() {
            delta_psi / 14.696
        } else {
            f64::NAN
        };
        let (mean_temp_c, used_default_temp) =
            mean_temp_between(temp_values.as_ref(), peak_idx, trough_idx, default_temp);
        let temp_k = mean_temp_c + 273.15;
        let n_ideal = if delta_atm.is_finite() && temp_k > 0.0 {
            ((delta_atm * v_l) / (CYCLE_GAS_CONSTANT * temp_k)).max(0.0)
        } else {
            f64::NAN
        };
        let n_vdw = if compute_vdw {
            vdw_moles_from_delta_p(delta_atm, v_l, temp_k, a_vdw, b_vdw).unwrap_or(f64::NAN)
        } else {
            f64::NAN
        };
        if n_ideal.is_finite() {
            total_ideal += n_ideal;
        }
        if compute_vdw && n_vdw.is_finite() {
            total_vdw += n_vdw;
        }

        let per_cycle_row = PyDict::new(py);
        per_cycle_row.set_item("peak", finite_value_or_nan(peak_pressure))?;
        per_cycle_row.set_item("trough", finite_value_or_nan(trough_pressure))?;
        per_cycle_row.set_item("deltaP", finite_value_or_nan(delta_psi))?;
        per_cycle_row.set_item("T_mean_C", finite_value_or_nan(mean_temp_c))?;
        per_cycle_row.set_item("used_default", used_default_temp)?;
        per_cycle_row.set_item("n_ideal", finite_value_or_nan(n_ideal))?;
        per_cycle_row.set_item("n_vdw", finite_value_or_nan(n_vdw))?;
        per_cycle.append(per_cycle_row)?;

        let start_x = safe_array_value(x_values.as_ref(), peak_idx);
        let end_x = safe_array_value(x_values.as_ref(), trough_idx);
        let duration_x = match (start_x, end_x) {
            (Some(start), Some(end)) => Some(end - start),
            _ => None,
        };
        let use_vdw_basis = n_vdw.is_finite() && n_vdw >= 0.0;
        let selected_moles = if use_vdw_basis {
            Some(n_vdw)
        } else if n_ideal.is_finite() {
            Some(n_ideal)
        } else {
            None
        };
        if let Some(selected) = selected_moles {
            cumulative_moles += selected;
        }
        let selected_mass = selected_moles.map(|value| value * molar_mass);
        let cumulative_mass = cumulative_moles * molar_mass;
        let transfer_row = PyDict::new(py);
        transfer_row.set_item("cycle_id", cycle_idx + 1)?;
        transfer_row.set_item("peak_index", peak_idx)?;
        transfer_row.set_item("trough_index", trough_idx)?;
        if let Some(value) = start_x {
            transfer_row.set_item("start_x", value)?;
        } else {
            transfer_row.set_item("start_x", py.None())?;
        }
        if let Some(value) = end_x {
            transfer_row.set_item("end_x", value)?;
        } else {
            transfer_row.set_item("end_x", py.None())?;
        }
        transfer_row.set_item("x_label", x_label)?;
        if let Some(value) = duration_x {
            transfer_row.set_item("duration_x", value)?;
        } else {
            transfer_row.set_item("duration_x", py.None())?;
        }
        transfer_row.set_item("peak_pressure_psi", finite_value_or_nan(peak_pressure))?;
        transfer_row.set_item("trough_pressure_psi", finite_value_or_nan(trough_pressure))?;
        transfer_row.set_item("delta_pressure_psi", finite_value_or_nan(delta_psi))?;
        if delta_atm.is_finite() {
            transfer_row.set_item("delta_pressure_atm", delta_atm)?;
        } else {
            transfer_row.set_item("delta_pressure_atm", py.None())?;
        }
        transfer_row.set_item("mean_temperature_c", finite_value_or_nan(mean_temp_c))?;
        transfer_row.set_item("used_default_temperature", used_default_temp)?;
        if n_ideal.is_finite() {
            transfer_row.set_item("moles_ideal", n_ideal)?;
        } else {
            transfer_row.set_item("moles_ideal", py.None())?;
        }
        if n_vdw.is_finite() {
            transfer_row.set_item("moles_vdw", n_vdw)?;
        } else {
            transfer_row.set_item("moles_vdw", py.None())?;
        }
        transfer_row.set_item("moles_basis", if use_vdw_basis { "vdw" } else { "ideal" })?;
        if let Some(value) = selected_moles {
            transfer_row.set_item("selected_moles", value)?;
        } else {
            transfer_row.set_item("selected_moles", py.None())?;
        }
        if let Some(value) = selected_mass {
            transfer_row.set_item("selected_mass_g", value)?;
        } else {
            transfer_row.set_item("selected_mass_g", py.None())?;
        }
        transfer_row.set_item("cumulative_moles", cumulative_moles)?;
        transfer_row.set_item("cumulative_co2_moles", cumulative_moles)?;
        transfer_row.set_item("cumulative_co2_mass_g", cumulative_mass)?;
        transfer_rows.append(transfer_row)?;
    }

    let response = PyDict::new(py);
    response.set_item("per_cycle", per_cycle)?;
    response.set_item("total_moles_ideal", total_ideal)?;
    response.set_item(
        "total_moles_vdw",
        if compute_vdw { total_vdw } else { 0.0_f64 },
    )?;
    response.set_item("vdw_used", compute_vdw)?;
    response.set_item("cycle_transfer", transfer_rows)?;
    let context = PyDict::new(py);
    context.set_item("volume_l", v_l)?;
    context.set_item("vdw_a", a_vdw)?;
    context.set_item("vdw_b", b_vdw)?;
    context.set_item("x_label", x_label)?;
    context.set_item("gas_molar_mass", molar_mass)?;
    context.set_item("vdw_used", compute_vdw)?;
    response.set_item("context", context)?;
    Ok(response.unbind())
}

#[pymodule(gil_used = false)]
fn gl260_rust_ext(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(rust_backend_manifest, module)?)?;
    module.add_function(wrap_pyfunction!(
        simulate_reaction_state_with_accounting,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(analyze_bicarbonate_core, module)?)?;
    module.add_function(wrap_pyfunction!(carbonate_state_core, module)?)?;
    module.add_function(wrap_pyfunction!(forced_ph_distribution_core, module)?)?;
    module.add_function(wrap_pyfunction!(aqion_closed_speciation_core, module)?)?;
    module.add_function(wrap_pyfunction!(pitzer_solve_total_carbon_core, module)?)?;
    module.add_function(wrap_pyfunction!(combined_decimation_indices, module)?)?;
    module.add_function(wrap_pyfunction!(combined_required_indices, module)?)?;
    module.add_function(wrap_pyfunction!(cycle_detect_markers_core, module)?)?;
    module.add_function(wrap_pyfunction!(cycle_manual_snap_core, module)?)?;
    module.add_function(wrap_pyfunction!(cycle_overlay_points_core, module)?)?;
    module.add_function(wrap_pyfunction!(cycle_segmentation_core, module)?)?;
    module.add_function(wrap_pyfunction!(cycle_metrics_core, module)?)?;
    module.add_function(wrap_pyfunction!(array_signature_core, module)?)?;
    module.add_function(wrap_pyfunction!(
        analysis_interpolate_reference_series_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(analysis_dashboard_core, module)?)?;
    module.add_function(wrap_pyfunction!(
        measured_ph_uptake_calibration_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        final_report_cycle_stats_rows_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        final_report_cycle_timeline_rows_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(cycle_timeline_normalize_core, module)?)?;
    module.add_function(wrap_pyfunction!(
        compare_aligned_cycle_rows_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        ledger_sort_filter_indices_core,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(ledger_prefill_metrics_core, module)?)?;
    Ok(())
}
