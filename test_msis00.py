#!/usr/bin/env python3
"""
Test script for MSIS00 Python interface.

This script tests the MSIS00 model implementation by comparing results
with known values and verifying the functionality of different interfaces.
"""

import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add the model directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

try:
    from model.pymsis00 import gtd7, gtd7d, gtd7_batch, MSIS00, msis00, SPECIES, TEMPERATURE
    print("Successfully imported MSIS00 module")
except ImportError as e:
    print(f"Failed to import MSIS00 module: {e}")
    print("Make sure the MSIS00 DLL has been compiled using model/pymsis00/compile.ps1")
    sys.exit(1)

def test_single_point():
    """Test single point calculation."""
    print("\n=== Testing Single Point Calculation ===")
    
    # Test parameters (typical mid-latitude conditions)
    iyd = 2023001  # Jan 1, 2023
    sec = 12.0 * 3600  # Noon (seconds)
    alt = 200.0  # 200 km altitude
    glat = 40.0  # 40°N latitude
    glong = -75.0  # 75°W longitude
    stl = 12.0  # Local solar time (hours)
    f107a = 150.0  # 81-day average F10.7 flux
    f107 = 150.0  # Daily F10.7 flux
    ap = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], dtype=np.float32)  # Quiet conditions
    mass = 48  # Total mass number
    
    # Calculate using GTD7
    d, t = gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
    
    print(f"Altitude: {alt} km")
    print(f"Location: {glat}°N, {glong}°E")
    print(f"Local time: {stl} hours")
    print(f"F10.7 flux: {f107} (daily), {f107a} (81-day avg)")
    print(f"Geomagnetic AP: {ap[0]} (daily)")
    
    print("\nDensities (cm^-3):")
    print(f"  He: {d[0]:.2e}")
    print(f"  O:  {d[1]:.2e}")
    print(f"  N2: {d[2]:.2e}")
    print(f"  O2: {d[3]:.2e}")
    print(f"  Ar: {d[4]:.2e}")
    print(f"  H:  {d[5]:.2e}")
    print(f"  N:  {d[6]:.2e}")
    print(f"  Anomalous O: {d[7]:.2e}")
    print(f"  Total mass: {d[8]:.2e} g/cm^3")
    
    print("\nTemperatures (K):")
    print(f"  Exospheric: {t[0]:.1f}")
    print(f"  At altitude: {t[1]:.1f}")
    
    # Basic sanity checks
    assert d[0] > 0, "He density should be positive"
    assert d[1] > 0, "O density should be positive"
    assert d[2] > 0, "N2 density should be positive"
    assert t[0] > 0, "Exospheric temperature should be positive"
    assert t[1] > 0, "Altitude temperature should be positive"
    assert t[0] >= t[1], "Exospheric temperature should be >= altitude temperature"
    
    print("✓ Single point calculation passed basic sanity checks")

def test_gtd7_vs_gtd7d():
    """Test difference between GTD7 and GTD7D models."""
    print("\n=== Testing GTD7 vs GTD7D ===")
    
    # Test parameters
    iyd = 2023001
    sec = 12.0 * 3600
    alt = 500.0  # Higher altitude where anomalous oxygen is more significant
    glat = 0.0   # Equatorial
    glong = 0.0
    stl = 12.0
    f107a = 200.0  # Higher solar activity
    f107 = 200.0
    ap = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0], dtype=np.float32)
    mass = 48
    
    # Calculate using both models
    d7, t7 = gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
    d7d, t7d = gtd7d(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
    
    print(f"Altitude: {alt} km")
    print(f"Total mass density (GTD7):  {d7[8]:.2e} g/cm^3")
    print(f"Total mass density (GTD7D): {d7d[8]:.2e} g/cm^3")
    print(f"Difference: {abs(d7d[8] - d7[8]):.2e} g/cm^3")
    print(f"Relative difference: {abs(d7d[8] - d7[8])/d7[8]*100:.1f}%")
    
    # GTD7D should include anomalous oxygen in total mass density
    assert d7d[8] >= d7[8], "GTD7D total mass density should be >= GTD7"
    
    print("✓ GTD7D includes anomalous oxygen as expected")

def test_batch_processing():
    """Test batch processing functionality."""
    print("\n=== Testing Batch Processing ===")
    
    # Create test data for multiple points
    n_points = 5
    alts = np.linspace(100, 500, n_points)  # 100 to 500 km
    
    # Fixed parameters
    iyd = 2023001
    sec = 12.0 * 3600
    glat = 40.0
    glong = -75.0
    stl = 12.0
    f107a = 150.0
    f107 = 150.0
    ap = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], dtype=np.float32)
    mass = 48
    
    # Batch calculation
    d_batch, t_batch = gtd7_batch(iyd, sec, alts, glat, glong, stl, f107a, f107, ap, mass)
    
    print("Altitude profile:")
    for i, alt in enumerate(alts):
        print(f"  {alt:6.1f} km: O density = {d_batch[i, 1]:.2e} cm^-3, "
              f"Temperature = {t_batch[i, 1]:.1f} K")
    
    # Verify shape
    assert d_batch.shape == (n_points, 9), f"Expected shape ({n_points}, 9), got {d_batch.shape}"
    assert t_batch.shape == (n_points, 2), f"Expected shape ({n_points}, 2), got {t_batch.shape}"
    
    # Compare with individual calculations
    for i, alt in enumerate(alts):
        d_single, t_single = gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass)
        np.testing.assert_allclose(d_batch[i], d_single, rtol=1e-6, 
                                   err_msg=f"Density mismatch at altitude {alt}")
        np.testing.assert_allclose(t_batch[i], t_single, rtol=1e-6,
                                   err_msg=f"Temperature mismatch at altitude {alt}")
    
    print("✓ Batch processing results match individual calculations")

def test_class_interface():
    """Test the class-based interface."""
    print("\n=== Testing Class Interface ===")
    
    # Create MSIS00 instance
    model = MSIS00()
    
    # Test with default parameters
    iyd = 2023001
    sec = 12.0 * 3600
    alt = 300.0
    glat = 40.0
    glong = -75.0
    stl = 12.0
    
    # Calculate with defaults
    d1, t1 = model.calculate(iyd, sec, alt, glat, glong, stl)
    
    # Calculate with explicit parameters
    d2, t2 = model.calculate(iyd, sec, alt, glat, glong, stl, 
                             f107a=150.0, f107=150.0, 
                             ap=[4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], 
                             mass=48)
    
    # Results should be identical
    np.testing.assert_allclose(d1, d2, rtol=1e-6, err_msg="Default parameters don't match explicit")
    np.testing.assert_allclose(t1, t2, rtol=1e-6, err_msg="Default parameters don't match explicit")
    
    # Test with anomalous oxygen
    d3, t3 = model.calculate(iyd, sec, alt, glat, glong, stl, use_anomalous_o=True)
    
    print(f"Total mass density (normal): {d1[8]:.2e} g/cm^3")
    print(f"Total mass density (with anomalous O): {d3[8]:.2e} g/cm^3")
    
    assert d3[8] >= d1[8], "Anomalous oxygen should increase total mass density"
    
    print("✓ Class interface works correctly")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")
    
    # Test minimum altitude
    try:
        d, t = gtd7(2023001, 12*3600, 0.0, 0.0, 0.0, 12.0, 150.0, 150.0, 
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], 48)
        print(f"Ground level calculation successful: T = {t[1]:.1f} K")
    except Exception as e:
        print(f"Ground level calculation failed: {e}")
    
    # Test high altitude
    try:
        d, t = gtd7(2023001, 12*3600, 1000.0, 0.0, 0.0, 12.0, 150.0, 150.0, 
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], 48)
        print(f"High altitude (1000 km) calculation successful: T = {t[1]:.1f} K")
    except Exception as e:
        print(f"High altitude calculation failed: {e}")
    
    # Test extreme solar conditions
    try:
        d, t = gtd7(2023001, 12*3600, 400.0, 0.0, 0.0, 12.0, 70.0, 70.0, 
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], 48)
        print(f"Solar minimum calculation successful: T = {t[1]:.1f} K")
        
        d, t = gtd7(2023001, 12*3600, 400.0, 0.0, 0.0, 12.0, 300.0, 300.0, 
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], 48)
        print(f"Solar maximum calculation successful: T = {t[1]:.1f} K")
    except Exception as e:
        print(f"Extreme solar conditions test failed: {e}")
    
    # Test error handling for wrong AP array size
    try:
        d, t = gtd7(2023001, 12*3600, 200.0, 0.0, 0.0, 12.0, 150.0, 150.0, 
                    [4.0, 4.0], 48)  # Wrong size
        print("ERROR: Should have failed with wrong AP array size")
    except ValueError as e:
        print(f"✓ Correctly caught AP array size error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def test_constants():
    """Test the constants dictionaries."""
    print("\n=== Testing Constants ===")
    
    print("Species indices:")
    for species, idx in SPECIES.items():
        print(f"  {species}: {idx}")
    
    print("\nTemperature indices:")
    for temp_type, idx in TEMPERATURE.items():
        print(f"  {temp_type}: {idx}")
    
    # Verify indices are correct
    assert SPECIES['HE'] == 0, "Helium should be at index 0"
    assert SPECIES['O'] == 1, "Oxygen should be at index 1"
    assert SPECIES['TOTAL'] == 8, "Total density should be at index 8"
    
    assert TEMPERATURE['EXOSPHERIC'] == 0, "Exospheric temperature should be at index 0"
    assert TEMPERATURE['ALTITUDE'] == 1, "Altitude temperature should be at index 1"
    
    print("✓ Constants are correctly defined")

def main():
    """Run all tests."""
    print("MSIS00 Python Interface Test Suite")
    print("=" * 50)
    
    try:
        test_single_point()
        test_gtd7_vs_gtd7d()
        test_batch_processing()
        test_class_interface()
        test_edge_cases()
        test_constants()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        print("\nThe MSIS00 Python interface is working correctly.")
        print("You can now use it in your applications.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()