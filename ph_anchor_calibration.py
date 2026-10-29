"""Learn pH response at fixed measured CO2 inventory, shared by both workflows."""

import math
from bisect import bisect_right


def response_ph(uptake_mol, baseline_ph, points, native=None):
    """Return pH plus interpolated measured residual at uptake in mol.

    Points are sorted (CO2 mol, measured-minus-model pH) pairs. The nearest
    residual is retained outside their range so a forecast does not forget the
    observations. No inventory or inputs are mutated. Invalid points raise
    ValueError; an absent, incompatible or unhealthy native kernel falls back
    to the identical Python interpolation.
    """
    x, base = float(uptake_mol), float(baseline_ph)
    if not math.isfinite(x) or not math.isfinite(base):
        raise ValueError("Calibration requires finite uptake and baseline pH.")
    pairs = [(float(a), float(b)) for a, b in points]
    if any(not math.isfinite(a) or not math.isfinite(b) for a, b in pairs):
        raise ValueError("Calibration points must be finite.")
    if any(b[0] <= a[0] for a, b in zip(pairs, pairs[1:], strict=False)):
        raise ValueError("Calibration uptake points must increase strictly.")
    if not pairs:
        return base
    index = bisect_right([a for a, _ in pairs], x)
    if index == 0:
        residual = pairs[0][1]
    elif index == len(pairs):
        residual = pairs[-1][1]
    else:
        left, right = pairs[index - 1], pairs[index]
        ratio = (x - left[0]) / (right[0] - left[0])
        residual = left[1] + ratio * (right[1] - left[1])
    expected = max(0.0, min(14.0, base + residual))
    if callable(native):
        try:
            result = float(native(x, base, pairs))
            if math.isfinite(result) and abs(result - expected) <= 1e-10:
                return result
        except Exception:
            pass
    return expected


def fit_response(cumulative_mol, baseline_ph, anchors, native=None):
    """Fit measured pH residuals without fitting or changing uptake.

    Takes aligned mol/pH sequences and normalized one-based cycle anchors.
    Returns predicted pH, uptake/residual knots and updated anchor diagnostics.
    Linear residual interpolation informs unmeasured cycles as well as anchors.
    Does not mutate inputs. Missing baselines, invalid cycles or contradictory
    pH observations at identical uptake raise ValueError rather than invent mass.
    """
    if len(cumulative_mol) != len(baseline_ph):
        raise ValueError("Uptake and pH series must align.")
    knots = {}
    records = []
    for anchor in anchors:
        index = int(anchor["cycle_index"]) - 1
        if index < 0 or index >= len(baseline_ph):
            raise ValueError("Anchor cycle is outside the uptake series.")
        base = float(baseline_ph[index])
        measured = float(anchor["measured_ph"])
        uptake = float(cumulative_mol[index])
        if not all(math.isfinite(v) for v in (base, measured, uptake)):
            raise ValueError("Anchor pH and uptake must be finite.")
        residual = measured - base
        if uptake in knots and abs(knots[uptake] - residual) > 1e-8:
            raise ValueError(
                "Different pH anchors at identical CO2 uptake need review."
            )
        knots[uptake] = residual
        records.append(
            dict(anchor, predicted_ph_before=base, residual_before=-residual)
        )
    points = sorted(knots.items())
    predicted = [
        response_ph(x, ph, points, native)
        for x, ph in zip(cumulative_mol, baseline_ph, strict=True)
    ]
    for record in records:
        value = predicted[int(record["cycle_index"]) - 1]
        record.update(
            predicted_ph_after=value, residual_after=value - record["measured_ph"]
        )
    return predicted, points, records


def compatible_points(record, model_key, context):
    """Return saved knots only for matching model, NaOH, volume and temperature.

    Inputs are a stored record and current model/context mappings in g, L and C.
    Returns a new list; missing/invalid/mismatched state returns no calibration.
    This conservative gate prevents unrelated runs inheriting cycle-index fits.
    No state is changed and malformed persisted values do not raise.
    """
    try:
        if record.get("model_key") != model_key:
            return []
        for key in ("naoh_mass_g", "solution_volume_l", "temperature_c"):
            if not math.isclose(
                float(record[key]), float(context[key]), rel_tol=1e-6, abs_tol=1e-6
            ):
                return []
        points = list(record.get("points") or [])
        response_ph(0.0, 7.0, points)
        return points
    except (KeyError, TypeError, ValueError, OverflowError):
        return []


def observed_response_ph(uptake_mol, baseline_ph, points, observations, native=None):
    """Predict pH using measured uptake/pH pairs inside their observed interval.

    Inputs use mol and pH; residual knots support model-shaped extrapolation
    outside observations. Within observations, interpolate the measurements so
    theoretical curvature cannot predict an endpoint before a measured alkaline
    anchor. Uses the shared native/Python interpolation kernel. Returns pH,
    mutates nothing, and raises ValueError for malformed or contradictory pairs.
    """
    observed = [(float(x), float(y)) for x, y in observations]
    if observed:
        response_ph(0.0, 0.0, observed)
        if observed[0][0] <= uptake_mol <= observed[-1][0]:
            return response_ph(uptake_mol, 0.0, observed, native)
    return response_ph(uptake_mol, baseline_ph, points, native)


def select_verified_run(records, context, profile_key=""):
    """Select the latest completed measured run for the same recipe and vessel.

    Records contain observations in mol/pH, recipe g/L/C, molar mass g/mol and
    optional nominal vessel liters. A matching NaOH/water charge (1% tolerance)
    is authoritative despite differing estimated liquid volumes. Temperature
    must be within 5 C; model keys need not match because observations are physical.
    Returns a copied record or None, without mutation. Malformed/incomplete runs
    are skipped so a new partial run cannot erase a completed reference.
    """
    # Explicitly confirmed references outrank automatically recognized completions;
    # stale/replayed current-run results must not replace the operator's baseline.
    candidates = sorted(
        [
            (index, row)
            for index, row in enumerate(records or [])
            if isinstance(row, dict)
        ],
        key=lambda item: (item[1].get("verified_by") == "user", item[0]),
        reverse=True,
    )
    for _index, record in candidates:
        try:
            if not record.get("verified") or not record.get("completed"):
                continue
            volume = float(record["effective_headspace_volume_l"])
            if not math.isfinite(volume) or volume <= 0:
                continue
            if profile_key and record.get("profile_key") != profile_key:
                continue
            for key in ("naoh_mass_g", "water_mass_g", "gas_molar_mass"):
                actual, expected = float(context[key]), float(record[key])
                if (
                    actual <= 0
                    or expected <= 0
                    or not math.isclose(actual, expected, rel_tol=0.01)
                ):
                    break
            else:
                if (
                    abs(
                        float(context["temperature_c"]) - float(record["temperature_c"])
                    )
                    > 5.0
                ):
                    continue
                vessel = record.get("nominal_vessel_volume_l")
                if vessel is not None and not math.isclose(
                    float(vessel),
                    float(context["nominal_vessel_volume_l"]),
                    rel_tol=0.01,
                ):
                    continue
                observed_response_ph(0.0, 7.0, [], record["observations"])
                if len(record["observations"]) >= 2:
                    return dict(record)
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    return None


def completed_reference(
    response, mass_calibration, anchors, target_ph, row_count, profile_key
):
    """Build a reusable reference only from a completed measured-mass run.

    Inputs contain response observations (mol/pH), measured total g and inferred
    gas-volume L, cycle anchors and target pH. Returns a record or None when a
    partial/unmeasured run cannot establish a completed reference. Pure function;
    malformed optional metadata is rejected without replacing existing history.
    """
    try:
        latest = anchors[-1]
        if len(anchors) < 2 or int(latest["cycle_index"]) != row_count:
            return None
        if float(latest["measured_ph"]) > float(target_ph) + 0.05:
            return None
        mass = float(mass_calibration["measured_mass_g"])
        volume = float(mass_calibration["headspace_volume_l"])
        if not all(math.isfinite(v) and v > 0 for v in (mass, volume)):
            return None
        if int(mass_calibration["cycle_count"]) != row_count:
            return None
        return dict(
            response,
            verified=True,
            completed=True,
            profile_key=profile_key,
            reference_id=f"{profile_key}: {mass:.3f} g / {row_count} charges",
            measured_mass_g=mass,
            effective_headspace_volume_l=volume,
            source="completed measured-mass Analysis",
            cycle_count=row_count,
        )
    except (IndexError, KeyError, TypeError, ValueError, OverflowError):
        return None
