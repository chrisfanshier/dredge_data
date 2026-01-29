"""
Test script for data loading and processing
Run this to verify data structures without launching GUI
"""

import pandas as pd
import numpy as np
from pyproj import Transformer

def test_usbl_data(filepath):
    """Test loading and processing USBL data"""
    print("=" * 60)
    print("TESTING USBL DATA")
    print("=" * 60)
    
    # Load
    df = pd.read_csv(filepath)
    print(f"\n✓ Loaded {len(df)} rows")
    print(f"  Columns: {list(df.columns)}")
    
    # Parse datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    print(f"\n✓ Parsed datetime column")
    print(f"  Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Duration: {df['datetime'].max() - df['datetime'].min()}")
    
    # UTM conversion
    lon = df['longitude_deg'].iloc[0]
    lat = df['latitude_deg'].iloc[0]
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = 'north' if lat >= 0 else 'south'
    
    transformer = Transformer.from_crs(
        "EPSG:4326",
        f"EPSG:326{utm_zone:02d}" if hemisphere == 'north' else f"EPSG:327{utm_zone:02d}",
        always_xy=True
    )
    
    easting, northing = transformer.transform(
        df['longitude_deg'].values,
        df['latitude_deg'].values
    )
    
    df['easting'] = easting
    df['northing'] = northing
    
    print(f"\n✓ Converted to UTM Zone {utm_zone}{hemisphere[0].upper()}")
    print(f"  Easting range: {df['easting'].min():.2f} to {df['easting'].max():.2f} m")
    print(f"  Northing range: {df['northing'].min():.2f} to {df['northing'].max():.2f} m")
    
    # Error ellipse info
    print(f"\n✓ Error ellipse parameters:")
    print(f"  Major axis: {df['hor_err_major'].mean():.2f} ± {df['hor_err_major'].std():.2f} m")
    print(f"  Minor axis: {df['hor_err_minor'].mean():.2f} ± {df['hor_err_minor'].std():.2f} m")
    
    # Beacons
    if 'beacon_name' in df.columns:
        beacons = df['beacon_name'].unique()
        print(f"\n✓ Beacons found: {len(beacons)}")
        for beacon in beacons:
            count = (df['beacon_name'] == beacon).sum()
            print(f"  - {beacon}: {count} points")
    
    return df


def test_sensor_data(filepath):
    """Test loading and processing sensor data"""
    print("\n" + "=" * 60)
    print("TESTING SENSOR DATA")
    print("=" * 60)
    
    # Find data start (skip comments)
    with open(filepath, 'r') as f:
        lines = f.readlines()
        data_start = 0
        for i, line in enumerate(lines):
            if not line.startswith('#'):
                data_start = i
                break
    
    print(f"\n✓ Skipped {data_start} comment lines")
    
    # Load
    df = pd.read_csv(filepath, skiprows=data_start)
    print(f"✓ Loaded {len(df)} rows")
    print(f"  Columns: {list(df.columns)}")
    
    # Parse datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    print(f"\n✓ Parsed datetime column")
    print(f"  Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Duration: {df['datetime'].max() - df['datetime'].min()}")
    
    # Calculate sampling rate
    time_diffs = df['datetime'].diff().dt.total_seconds()
    median_dt = time_diffs.median()
    freq = 1 / median_dt if median_dt > 0 else 0
    print(f"  Median sampling rate: {freq:.1f} Hz")
    
    # Numeric columns
    numeric_cols = [col for col in df.columns 
                    if col != 'datetime' and pd.api.types.is_numeric_dtype(df[col])]
    print(f"\n✓ Found {len(numeric_cols)} numeric columns:")
    for col in numeric_cols:
        non_null = df[col].notna().sum()
        print(f"  - {col}: {non_null}/{len(df)} non-null values")
    
    return df


def test_time_alignment(usbl_df, sensor_df):
    """Test time alignment between datasets"""
    print("\n" + "=" * 60)
    print("TESTING TIME ALIGNMENT")
    print("=" * 60)
    
    usbl_start = usbl_df['datetime'].min()
    usbl_end = usbl_df['datetime'].max()
    sensor_start = sensor_df['datetime'].min()
    sensor_end = sensor_df['datetime'].max()
    
    print(f"\nUSBL time range:   {usbl_start} to {usbl_end}")
    print(f"Sensor time range: {sensor_start} to {sensor_end}")
    
    # Find overlap
    overlap_start = max(usbl_start, sensor_start)
    overlap_end = min(usbl_end, sensor_end)
    
    if overlap_start < overlap_end:
        overlap_duration = overlap_end - overlap_start
        print(f"\n✓ Overlap found: {overlap_duration}")
        print(f"  Start: {overlap_start}")
        print(f"  End:   {overlap_end}")
        
        # Count points in overlap
        usbl_overlap = ((usbl_df['datetime'] >= overlap_start) & 
                       (usbl_df['datetime'] <= overlap_end)).sum()
        sensor_overlap = ((sensor_df['datetime'] >= overlap_start) & 
                         (sensor_df['datetime'] <= overlap_end)).sum()
        
        print(f"\n  USBL points in overlap: {usbl_overlap}")
        print(f"  Sensor points in overlap: {sensor_overlap}")
    else:
        print("\n✗ NO OVERLAP - datasets do not overlap in time!")


def test_region_selection(usbl_df, sensor_df):
    """Test region selection logic"""
    print("\n" + "=" * 60)
    print("TESTING REGION SELECTION")
    print("=" * 60)
    
    # Simulate selecting middle 10% of time range
    time_min = sensor_df['datetime'].min()
    time_max = sensor_df['datetime'].max()
    duration = (time_max - time_min).total_seconds()
    
    region_start = time_min + pd.Timedelta(seconds=duration * 0.45)
    region_end = time_min + pd.Timedelta(seconds=duration * 0.55)
    
    print(f"\nSimulated region: {region_start} to {region_end}")
    
    # Filter USBL data
    usbl_mask = (usbl_df['datetime'] >= region_start) & (usbl_df['datetime'] <= region_end)
    usbl_selected = usbl_df[usbl_mask]
    
    # Filter sensor data
    sensor_mask = (sensor_df['datetime'] >= region_start) & (sensor_df['datetime'] <= region_end)
    sensor_selected = sensor_df[sensor_mask]
    
    print(f"\n✓ Selected {len(usbl_selected)} USBL points")
    print(f"✓ Selected {len(sensor_selected)} sensor points")
    
    # Add region tag
    usbl_df['region_test'] = usbl_mask
    sensor_df['region_test'] = sensor_mask
    
    print("\n✓ Tagged data with 'region_test' column")
    print(f"  USBL: {usbl_df['region_test'].sum()} True values")
    print(f"  Sensor: {sensor_df['region_test'].sum()} True values")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_data_loading.py <usbl_csv> <sensor_csv>")
        print("\nExample:")
        print("  python test_data_loading.py RR2509-D18_usbl.csv sensor_export_*.csv")
        sys.exit(1)
    
    usbl_file = sys.argv[1]
    sensor_file = sys.argv[2]
    
    # Test each dataset
    usbl_df = test_usbl_data(usbl_file)
    sensor_df = test_sensor_data(sensor_file)
    
    # Test alignment
    test_time_alignment(usbl_df, sensor_df)
    
    # Test region selection
    test_region_selection(usbl_df, sensor_df)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
    print("\n✓ Data structures validated")
    print("✓ Ready to run GUI application")
