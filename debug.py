"""
Debug script to check UTM conversion for USBL data
Usage: python debug_utm.py path/to/usbl.csv
"""
import sys
import pandas as pd
from pyproj import Transformer

if len(sys.argv) < 2:
    print("Usage: python debug_utm.py path/to/usbl.csv")
    sys.exit(1)

filename = sys.argv[1]

print("=" * 60)
print("USBL UTM CONVERSION DEBUG")
print("=" * 60)

# Load data
df = pd.read_csv(filename)
print(f"\n✓ Loaded {len(df)} rows")
print(f"  Columns: {list(df.columns)}")

# Check for required columns
if 'longitude_deg' not in df.columns or 'latitude_deg' not in df.columns:
    print("\n✗ ERROR: Missing longitude_deg or latitude_deg columns!")
    sys.exit(1)

# Get first point
lon = df['longitude_deg'].iloc[0]
lat = df['latitude_deg'].iloc[0]

print(f"\n📍 First point (lat/lon):")
print(f"   Latitude:  {lat:.8f}°")
print(f"   Longitude: {lon:.8f}°")

# Calculate UTM zone
utm_zone = int((lon + 180) / 6) + 1
hemisphere = 'north' if lat >= 0 else 'south'

print(f"\n🌍 UTM Zone: {utm_zone}{hemisphere[0].upper()}")

# Create transformer
epsg_code = f"326{utm_zone:02d}" if hemisphere == 'north' else f"327{utm_zone:02d}"
print(f"   EPSG Code: {epsg_code}")

transformer = Transformer.from_crs(
    "EPSG:4326",  # WGS84
    f"EPSG:{epsg_code}",
    always_xy=True
)

# Transform all points
print(f"\n⚙️  Converting all {len(df)} points...")
easting, northing = transformer.transform(
    df['longitude_deg'].values,
    df['latitude_deg'].values
)

# Add to dataframe
df['easting'] = easting
df['northing'] = northing

# Show statistics
print(f"\n📊 UTM Coordinates (meters):")
print(f"   Easting:  {df['easting'].min():.2f} to {df['easting'].max():.2f}")
print(f"   Range:    {df['easting'].max() - df['easting'].min():.2f} m")
print(f"   Northing: {df['northing'].min():.2f} to {df['northing'].max():.2f}")
print(f"   Range:    {df['northing'].max() - df['northing'].min():.2f} m")

# Show first few points
print(f"\n📋 First 5 converted points:")
print(df[['latitude_deg', 'longitude_deg', 'easting', 'northing']].head())

# Check if beacons exist
if 'beacon_name' in df.columns:
    print(f"\n🔷 Beacons found:")
    for beacon in df['beacon_name'].unique():
        beacon_df = df[df['beacon_name'] == beacon]
        print(f"   {beacon}: {len(beacon_df)} points")
        print(f"      Easting range: {beacon_df['easting'].min():.2f} to {beacon_df['easting'].max():.2f}")
        print(f"      Northing range: {beacon_df['northing'].min():.2f} to {beacon_df['northing'].max():.2f}")

print("\n" + "=" * 60)
print("✓ Conversion successful!")
print("=" * 60)