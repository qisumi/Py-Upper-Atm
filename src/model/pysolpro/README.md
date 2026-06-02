# SOLPRO — Interplanetary Solar Proton Fluence Model

## Background

SOLPRO computes interplanetary integral solar proton fluence at 1 AU for
missions of up to 72 months, based on a user-specified confidence level. The
model was developed by E. G. Stassinopoulos (NASA/GSFC) and is based on the
solar proton fluence model of King (1974) and Stassinopoulos & King (1974).

The model outputs fluence at 10 energy thresholds (10–100 MeV) and accounts
for two types of solar proton events:

- **OR (Ordinary Recurrent) events**: Normal solar proton events modeled using
  polynomial fits to data from solar cycle 20 (1964–1972).
- **AL (Anomalously Large) events**: Extremely rare events like the August 1972
  event, which was more than 10× larger than any other event in solar cycle 20.
  The model predicts the number of AL events expected for a given mission
  duration and confidence level.

All empirical coefficients are hard-coded in the Fortran source — **no external
data files are required**.

## Directory Structure

```text
pysolpro/
├── solpro.for              # SOLPRO Fortran IV source (subroutine SOLPRO)
├── solpro_cshim.F90        # C ABI shim
├── CMakeLists.txt          # Builds solpro.dll / libsolpro.so
├── __init__.py             # Python Model class
├── README.md               # This file (English)
└── README_zh.md            # Chinese documentation
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | auto-detected | Custom path to the compiled DLL |

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `duration_months` | float / array | Mission duration in months (1–72) |
| `confidence_pct` | int / array | Confidence level in percent (80–99). Represents the probability that the computed fluence will not be exceeded. |

Both parameters support numpy broadcasting.

## Output

`calculate()` returns a dictionary:

| Field | Type | Description |
|-------|------|-------------|
| `duration_months` | float / ndarray | Input duration (echoed) |
| `confidence_pct` | int / ndarray | Input confidence level (echoed) |
| `fluence_cm2` | ndarray | Integral fluence in protons/cm². Shape `(10,)` for scalar input, `(N, 10)` for batch. Columns correspond to energy thresholds 10, 20, 30, …, 100 MeV. |
| `n_al_events` | int / ndarray | Number of predicted Anomalously Large events. |

## Usage Examples

### Single-point calculation

```python
from model import SOLPRO

model = SOLPRO()
result = model.calculate(duration_months=12, confidence_pct=90)

print(f"AL events: {result['n_al_events']}")
print(f"Fluence >10 MeV: {result['fluence_cm2'][0]:.3e} protons/cm²")
print(f"Fluence >100 MeV: {result['fluence_cm2'][9]:.3e} protons/cm²")
```

### Batch over mission durations

```python
import numpy as np

model = SOLPRO()
durations = np.array([1, 3, 6, 12, 24, 48, 72], dtype=float)
result = model.calculate(duration_months=durations, confidence_pct=90)

print(result["fluence_cm2"].shape)    # (7, 10)
print(result["n_al_events"].shape)    # (7,)
```

### Compare confidence levels

```python
model = SOLPRO()
for conf in [80, 90, 95, 99]:
    r = model.calculate(duration_months=24, confidence_pct=conf)
    print(f"  {conf}%: {r['fluence_cm2'][0]:.3e} protons/cm² (>10 MeV), "
          f"{r['n_al_events']} AL events")
```

## Notes

- The model is based on solar cycle 20 data (1964–1972) and is known to
  over-predict for later solar cycles.
- Scalar inputs return scalar `n_al_events` and 1-D `fluence_cm2` array (shape
  `(10,)`); array inputs return array `n_al_events` and 2-D `fluence_cm2`
  (shape `(N, 10)`).
- The energy thresholds are hard-coded at E = 10, 20, 30, …, 100 MeV.

## References

1. King, J. H., "Solar Proton Fluences for 1977-1983 Space Missions",
   J. Spacecraft & Rockets 11, 401, 1974.

2. Stassinopoulos, E. G., and J. H. King, "A Method for Rapid Estimation
   of Solar Proton Fluences for NASA Missions", NASA TM X-71140, 1974.

3. King, J. H., and E. G. Stassinopoulos, "A Model for the Calculation
   of Interplanetary Solar Proton Fluences", NASA TM X-71139, 1975.

4. Stassinopoulos, E. G., "SOLPRO: A Computer Code for the Calculation
   of Interplanetary Solar Proton Fluences", NASA TM X-71141, 1975.
