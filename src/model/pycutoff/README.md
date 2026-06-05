# CutoffRigidity — Geomagnetic Cutoff Rigidity (Smart & Shea, IGRF-95)

[中文文档 (Chinese)](README_zh.md)

## Model Background

The Geomagnetic Cutoff Rigidity model predicts magnetic rigidity (momentum/charge) cutoffs or thresholds for penetration of energetic cosmic ray particles from interplanetary space through Earth's geomagnetic field. The concept was pioneered by Carl Störmer in 1930.

This implementation is based on the standard cosmic ray trajectory program maintained by Don F. Smart and Margaret A. Shea (University of Alabama in Huntsville), archived from the NSSDC/CCMC ModelWeb. It uses the IGRF-1995 geomagnetic field model (order 10, Schmidt normalized coefficients) with Runge-Kutta integration to trace charged particle trajectories.

**No external data files are required** — IGRF-95 coefficients are hard-coded in the Fortran source.

**References**:

> Smart, D. F. & Shea, M. A., *Geomagnetic Cutoff Rigidity Computer Program*, NSSDC, 2001.

> Störmer, C., *On the Trajectories of Electric Particles in the Field of a Magnetic Dipole*, Astrophysica Norvegica, 1930.

## Directory Structure

```
pycutoff/
├── cutoff_legacy.for    # Fortran 77 subroutines (GDGC, SINGLTJ, FGRAD, MAGNEW95, azrgeg)
├── cutoff_cshim.F90     # C ABI shim, exports cutoff_trajectory()
├── CMakeLists.txt       # CMake target cutoff
├── __init__.py          # Python Model class
└── README.md            # This file
```

## Fortran Interface

### `cutoff_legacy.for` — Core subroutines

| Subroutine | Description |
|------------|-------------|
| `GDGC(TCD, TSD)` | Geodetic to geocentric coordinate conversion |
| `SINGLTJ(PC, IRSLT, INDXPC, Y1GC, Y2GC, Y3GC)` | Single trajectory calculation via Runge-Kutta |
| `FGRAD` | Force gradient computation |
| `MAGNEW95` | IGRF-95 magnetic field computation |
| `azrgeg(na, nz, pamu, rigin, epn, beta)` | Energy-rigidity conversion |

### `cutoff_cshim.F90` — C ABI

```c
void cutoff_trajectory(double lat_deg, double lon_deg, double rigidity_gv,
                       double zenith_deg, double azimuth_deg,
                       int *result_code, double *faslat, double *faslon,
                       double *path_length);

void cutoff_rigidity_to_energy(int atomic_number, int charge,
                               double mass_amu, double rigidity_mv,
                               double *energy_mev);
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `lat_deg` | float or ndarray | Geographic latitude (degrees), -90 to 90 |
| `lon_deg` | float or ndarray | Geographic longitude (degrees), -180 to 360 |
| `rigidity_gv` | float, ndarray, or None | Magnetic rigidity (GV). If None, scan mode is used |
| `zenith_deg` | float or ndarray | Zenith angle (degrees), 0 to 180. Default 0 (vertical) |
| `azimuth_deg` | float or ndarray | Azimuth angle (degrees). Default 0 (north) |
| `start_rigidity_gv` | float | Scan start rigidity (GV). Default 20.0. Scan mode only |
| `delta_rigidity_mv` | float | Rigidity step (MV). Default 10.0. Scan mode only |
| `max_trajectories` | int | Maximum trajectories. Default 1000. Scan mode only |

Array inputs are supported in single trajectory mode and are broadcast using
NumPy rules. Scan mode accepts scalar position and direction inputs.

## Output

### Single trajectory mode (`rigidity_gv` specified)

| Field | Type | Description |
|-------|------|-------------|
| `rigidity_gv` | float | Input rigidity |
| `result_code` | int | +1 (allowed), 0 (failed), -1 (re-entrant) |
| `fate` | str | "allowed", "failed", or "reentrant" |
| `asymptotic_latitude_deg` | float | Asymptotic latitude (degrees) |
| `asymptotic_longitude_deg` | float | Asymptotic longitude (degrees) |
| `path_length_re` | float | Trajectory path length (Earth radii) |

### Scan mode (`rigidity_gv` is None)

| Field | Type | Description |
|-------|------|-------------|
| `cutoff_rigidity_gv` | float | Geomagnetic cutoff rigidity (GV) |
| `fate` | str | "allowed" or "forbidden" |
| `asymptotic_latitude_deg` | float | Asymptotic latitude of cutoff trajectory |
| `asymptotic_longitude_deg` | float | Asymptotic longitude of cutoff trajectory |
| `path_length_re` | float | Path length of cutoff trajectory |
| `n_trajectories_computed` | int | Number of trajectories computed |
| `rigidity_gv` | ndarray | All tested rigidities (GV) |
| `trajectory_results` | ndarray | Result codes for each trajectory |

## Usage Examples

### Single trajectory

```python
from model import CutoffRigidity

model = CutoffRigidity()
result = model.calculate(
    lat_deg=40.0, lon_deg=0.0, rigidity_gv=10.0,
    zenith_deg=0.0, azimuth_deg=0.0,
)
print(f"Fate: {result['fate']}")
print(f"Asymptotic: ({result['asymptotic_latitude_deg']:.1f}°, "
      f"{result['asymptotic_longitude_deg']:.1f}°)")
```

### Batch single trajectories

```python
import numpy as np
from model import CutoffRigidity

model = CutoffRigidity()
result = model.calculate(
    lat_deg=np.array([0.0, 40.0]),
    lon_deg=0.0,
    rigidity_gv=np.array([15.0, 10.0]),
)
print(result["fate"])
```

### Cutoff scan

```python
result = model.calculate(
    lat_deg=0.0, lon_deg=0.0,
    start_rigidity_gv=20.0,
    delta_rigidity_mv=50.0,
    max_trajectories=500,
)
print(f"Cutoff rigidity: {result['cutoff_rigidity_gv']:.2f} GV")
print(f"Trajectories computed: {result['n_trajectories_computed']}")
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom DLL path |

## Coordinate Notes

- Input coordinates are **geographic** (geodetic) latitude and longitude.
- Internally, the model converts to geocentric coordinates using the WGS ellipsoid.
- Asymptotic coordinates represent the direction from which a cosmic ray arrives at the top of the atmosphere.
- The model cannot run trajectories over the poles (will get BETA blowup).

## Acknowledgement

Please acknowledge the software providers (NSSDC) and the model authors (Smart & Shea) in any publication that results from work using this software.
