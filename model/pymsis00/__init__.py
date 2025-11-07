"""
Python interface for MSIS00 (NRLMSISE-00) neutral atmosphere model.

This module provides a Python interface to the MSIS00 Fortran model,
allowing calculation of neutral atmospheric densities and temperatures.

The MSIS00 model calculates the neutral temperature and densities in the
Earth's atmosphere from ground level to 1000 km. It is based on the
NRLMSISE-00 model developed by NASA.

Example:
    >>> import numpy as np
    >>> from model.pymsis00 import msis00
    >>> 
    >>> # Single point calculation
    >>> iyd = 2023001  # Year day (Jan 1, 2023)
    >>> sec = 12.0 * 3600  # Seconds in day (noon)
    >>> alt = 200.0  # Altitude (km)
    >>> glat = 40.0  # Geodetic latitude (deg)
    >>> glong = -75.0  # Geodetic longitude (deg)
    >>> stl = 12.0  # Local solar time (hours)
    >>> f107a = 150.0  # 81-day average F10.7 flux
    >>> f107 = 150.0  # Daily F10.7 flux
    >>> ap = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0])  # Geomagnetic indices
    >>> mass = 48  # Total mass number (for total density)
    >>> 
    >>> d, t = msis00.gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
    >>> print(f"He density: {d[0]:.2e} cm^-3")
    >>> print(f"O density: {d[1]:.2e} cm^-3")
    >>> print(f"N2 density: {d[2]:.2e} cm^-3")
    >>> print(f"Temperature: {t[1]:.1f} K")
"""

import os
import ctypes
import numpy as np
from typing import Tuple, Union, Optional

# Get the directory of this module
_module_dir = os.path.dirname(os.path.abspath(__file__))
_dll_path = os.path.join(_module_dir, "msis00.dll")

# Load the DLL
try:
    _msis00_lib = ctypes.CDLL(_dll_path)
except OSError as e:
    raise ImportError(f"Failed to load MSIS00 DLL from {_dll_path}: {e}")

# Define function signatures
_gtd7_eval = _msis00_lib.gtd7_eval
_gtd7_eval.restype = None
_gtd7_eval.argtypes = [
    ctypes.c_int,    # iyd
    ctypes.c_float,  # sec
    ctypes.c_float,  # alt
    ctypes.c_float,  # glat
    ctypes.c_float,  # glong
    ctypes.c_float,  # stl
    ctypes.c_float,  # f107a
    ctypes.c_float,  # f107
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),  # ap
    ctypes.c_int,    # mass
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),  # d_out
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS')   # t_out
]

_gtd7d_eval = _msis00_lib.gtd7d_eval
_gtd7d_eval.restype = None
_gtd7d_eval.argtypes = [
    ctypes.c_int,    # iyd
    ctypes.c_float,  # sec
    ctypes.c_float,  # alt
    ctypes.c_float,  # glat
    ctypes.c_float,  # glong
    ctypes.c_float,  # stl
    ctypes.c_float,  # f107a
    ctypes.c_float,  # f107
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),  # ap
    ctypes.c_int,    # mass
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),  # d_out
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS')   # t_out
]

# Species indices for the output density array
SPECIES = {
    'HE': 0,    # Helium
    'O': 1,     # Atomic oxygen
    'N2': 2,    # Molecular nitrogen
    'O2': 3,    # Molecular oxygen
    'AR': 4,    # Argon
    'H': 5,     # Atomic hydrogen
    'N': 6,     # Atomic nitrogen
    'ANOMALOUS_O': 7,  # Anomalous oxygen
    'TOTAL': 8   # Total mass density
}

# Temperature indices for the output temperature array
TEMPERATURE = {
    'EXOSPHERIC': 0,  # Exospheric temperature
    'ALTITUDE': 1     # Temperature at specified altitude
}

def gtd7(iyd: int, sec: float, alt: float, glat: float, glong: float, 
         stl: float, f107a: float, f107: float, ap: Union[np.ndarray, list], 
         mass: int = 48) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate neutral atmospheric densities and temperatures using MSIS00 GTD7 model.
    
    Parameters:
    -----------
    iyd : int
        Year and day as YYDDD (e.g., 2023001 for Jan 1, 2023)
    sec : float
        Seconds of the day (0-86400)
    alt : float
        Altitude in km
    glat : float
        Geodetic latitude in degrees (-90 to 90)
    glong : float
        Geodetic longitude in degrees (-180 to 180)
    stl : float
        Local solar time in hours (0-24)
    f107a : float
        81-day average of F10.7 solar flux
    f107 : float
        Daily F10.7 solar flux
    ap : array_like
        Geomagnetic activity indices (7 elements):
        ap[0] : Daily ap
        ap[1-3] : 3-hour ap for current time
        ap[4-6] : 3-hour ap for previous times
    mass : int, optional
        Mass number (default=48 for total mass density)
        
    Returns:
    --------
    d : ndarray
        Densities for 9 species (cm^-3):
        d[0] : He density
        d[1] : O density
        d[2] : N2 density
        d[3] : O2 density
        d[4] : Ar density
        d[5] : H density
        d[6] : N density
        d[7] : Anomalous O density
        d[8] : Total mass density (g/cm^3)
        
    t : ndarray
        Temperatures (K):
        t[0] : Exospheric temperature
        t[1] : Temperature at specified altitude
    """
    # Convert inputs to correct types
    ap_array = np.asarray(ap, dtype=np.float32)
    if ap_array.shape != (7,):
        raise ValueError("ap array must have exactly 7 elements")
    
    # Prepare output arrays
    d_out = np.zeros(9, dtype=np.float32)
    t_out = np.zeros(2, dtype=np.float32)
    
    # Call the Fortran function
    _gtd7_eval(
        ctypes.c_int(iyd),
        ctypes.c_float(sec),
        ctypes.c_float(alt),
        ctypes.c_float(glat),
        ctypes.c_float(glong),
        ctypes.c_float(stl),
        ctypes.c_float(f107a),
        ctypes.c_float(f107),
        ap_array,
        ctypes.c_int(mass),
        d_out,
        t_out
    )
    
    return d_out, t_out

def gtd7d(iyd: int, sec: float, alt: float, glat: float, glong: float, 
          stl: float, f107a: float, f107: float, ap: Union[np.ndarray, list], 
          mass: int = 48) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate neutral atmospheric densities and temperatures using MSIS00 GTD7D model.
    
    This version includes anomalous oxygen in the total mass density calculation.
    
    Parameters are the same as gtd7().
    
    Returns:
    --------
    d : ndarray
        Densities for 9 species (cm^-3)
    t : ndarray
        Temperatures (K)
    """
    # Convert inputs to correct types
    ap_array = np.asarray(ap, dtype=np.float32)
    if ap_array.shape != (7,):
        raise ValueError("ap array must have exactly 7 elements")
    
    # Prepare output arrays
    d_out = np.zeros(9, dtype=np.float32)
    t_out = np.zeros(2, dtype=np.float32)
    
    # Call the Fortran function
    _gtd7d_eval(
        ctypes.c_int(iyd),
        ctypes.c_float(sec),
        ctypes.c_float(alt),
        ctypes.c_float(glat),
        ctypes.c_float(glong),
        ctypes.c_float(stl),
        ctypes.c_float(f107a),
        ctypes.c_float(f107),
        ap_array,
        ctypes.c_int(mass),
        d_out,
        t_out
    )
    
    return d_out, t_out

def gtd7_batch(iyd: Union[int, np.ndarray], sec: Union[float, np.ndarray], 
               alt: Union[float, np.ndarray], glat: Union[float, np.ndarray], 
               glong: Union[float, np.ndarray], stl: Union[float, np.ndarray], 
               f107a: Union[float, np.ndarray], f107: Union[float, np.ndarray], 
               ap: Union[np.ndarray, list], mass: int = 48) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate neutral atmospheric densities and temperatures for multiple points.
    
    Parameters can be scalars or arrays. All array inputs must have the same length.
    
    Parameters are the same as gtd7(), but can be arrays for batch processing.
    
    Returns:
    --------
    d : ndarray
        Densities for 9 species (n_points, 9)
    t : ndarray
        Temperatures (n_points, 2)
    """
    # Convert inputs to arrays
    iyd_arr = np.atleast_1d(iyd)
    sec_arr = np.atleast_1d(sec)
    alt_arr = np.atleast_1d(alt)
    glat_arr = np.atleast_1d(glat)
    glong_arr = np.atleast_1d(glong)
    stl_arr = np.atleast_1d(stl)
    f107a_arr = np.atleast_1d(f107a)
    f107_arr = np.atleast_1d(f107)
    ap_arr = np.atleast_2d(ap)
    
    # Check array shapes
    n_points = max(len(iyd_arr), len(sec_arr), len(alt_arr), len(glat_arr), 
                   len(glong_arr), len(stl_arr), len(f107a_arr), len(f107_arr), ap_arr.shape[0])
    
    # Broadcast scalars to arrays
    if len(iyd_arr) == 1:
        iyd_arr = np.full(n_points, iyd_arr[0])
    if len(sec_arr) == 1:
        sec_arr = np.full(n_points, sec_arr[0])
    if len(alt_arr) == 1:
        alt_arr = np.full(n_points, alt_arr[0])
    if len(glat_arr) == 1:
        glat_arr = np.full(n_points, glat_arr[0])
    if len(glong_arr) == 1:
        glong_arr = np.full(n_points, glong_arr[0])
    if len(stl_arr) == 1:
        stl_arr = np.full(n_points, stl_arr[0])
    if len(f107a_arr) == 1:
        f107a_arr = np.full(n_points, f107a_arr[0])
    if len(f107_arr) == 1:
        f107_arr = np.full(n_points, f107_arr[0])
    if ap_arr.shape[0] == 1:
        ap_arr = np.repeat(ap_arr, n_points, axis=0)
    
    # Prepare output arrays
    d_out = np.zeros((n_points, 9), dtype=np.float32)
    t_out = np.zeros((n_points, 2), dtype=np.float32)
    
    # Process each point
    for i in range(n_points):
        d, t = gtd7(iyd_arr[i], sec_arr[i], alt_arr[i], glat_arr[i], 
                   glong_arr[i], stl_arr[i], f107a_arr[i], f107_arr[i], 
                   ap_arr[i], mass)
        d_out[i] = d
        t_out[i] = t
    
    return d_out, t_out

# Create a convenient class-based interface
class MSIS00:
    """
    Class-based interface for MSIS00 model.
    
    This class provides a convenient way to set default values and
    calculate atmospheric properties.
    """
    
    def __init__(self):
        """Initialize MSIS00 model with default parameters."""
        self.default_ap = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], dtype=np.float32)
        self.default_f107a = 150.0
        self.default_f107 = 150.0
        self.default_mass = 48
    
    def calculate(self, iyd: int, sec: float, alt: float, glat: float, glong: float, 
                  stl: float, f107a: Optional[float] = None, f107: Optional[float] = None, 
                  ap: Optional[Union[np.ndarray, list]] = None, mass: Optional[int] = None,
                  use_anomalous_o: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate atmospheric properties with optional default parameters.
        
        Parameters are the same as gtd7(), but with optional defaults.
        
        Parameters:
        -----------
        use_anomalous_o : bool, optional
            If True, use GTD7D model which includes anomalous oxygen in total mass density.
            
        Returns:
        --------
        d : ndarray
            Densities for 9 species (cm^-3)
        t : ndarray
            Temperatures (K)
        """
        if f107a is None:
            f107a = self.default_f107a
        if f107 is None:
            f107 = self.default_f107
        if ap is None:
            ap = self.default_ap
        if mass is None:
            mass = self.default_mass
        
        if use_anomalous_o:
            return gtd7d(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
        else:
            return gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)

# Create a default instance
msis00 = MSIS00()

# Export the main functions and classes
__all__ = ['gtd7', 'gtd7d', 'gtd7_batch', 'MSIS00', 'msis00', 'SPECIES', 'TEMPERATURE']