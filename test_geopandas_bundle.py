"""
Diagnostic script to test if geopandas works in the bundled executable
Run this INSIDE the built .exe (after adding it to your app)

Or run standalone to test your environment
"""

import sys
import os

print("="*60)
print("GEOPANDAS DIAGNOSTIC TEST")
print("="*60)
print()

# Check if running in PyInstaller bundle
if getattr(sys, 'frozen', False):
    print("✓ Running in PyInstaller bundle")
    bundle_dir = sys._MEIPASS
    print(f"  Bundle directory: {bundle_dir}")
else:
    print("✗ Running from source (not bundled)")
    print()

# Test 1: Import geopandas
print("\n[1] Testing geopandas import...")
try:
    import geopandas as gpd
    print(f"✓ geopandas imported successfully")
    print(f"  Version: {gpd.__version__}")
    print(f"  Location: {gpd.__file__}")
except ImportError as e:
    print(f"✗ Failed to import geopandas")
    print(f"  Error: {e}")
    sys.exit(1)

# Test 2: Import shapely
print("\n[2] Testing shapely import...")
try:
    from shapely.geometry import Point, Polygon
    print(f"✓ shapely imported successfully")
    import shapely
    print(f"  Version: {shapely.__version__}")
    print(f"  Location: {shapely.__file__}")
except ImportError as e:
    print(f"✗ Failed to import shapely")
    print(f"  Error: {e}")
    sys.exit(1)

# Test 3: Import fiona
print("\n[3] Testing fiona import...")
try:
    import fiona
    print(f"✓ fiona imported successfully")
    print(f"  Version: {fiona.__version__}")
    print(f"  Location: {fiona.__file__}")
    print(f"  Supported drivers: {', '.join(list(fiona.supported_drivers.keys())[:5])}...")
except ImportError as e:
    print(f"✗ Failed to import fiona")
    print(f"  Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️  fiona imported but error accessing drivers:")
    print(f"  Error: {e}")

# Test 4: Import pyproj
print("\n[4] Testing pyproj import...")
try:
    import pyproj
    print(f"✓ pyproj imported successfully")
    print(f"  Version: {pyproj.__version__}")
    print(f"  Location: {pyproj.__file__}")
    print(f"  Data dir: {pyproj.datadir.get_data_dir()}")
except ImportError as e:
    print(f"✗ Failed to import pyproj")
    print(f"  Error: {e}")
    sys.exit(1)

# Test 5: Create a GeoDataFrame
print("\n[5] Testing GeoDataFrame creation...")
try:
    import pandas as pd
    
    # Create test data
    df = pd.DataFrame({
        'name': ['Point A', 'Point B'],
        'x': [100.0, 200.0],
        'y': [50.0, 75.0]
    })
    
    # Create geometries
    geometry = [Point(x, y) for x, y in zip(df['x'], df['y'])]
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    print(f"✓ GeoDataFrame created successfully")
    print(f"  Rows: {len(gdf)}")
    print(f"  CRS: {gdf.crs}")
    print(f"  Geometry type: {gdf.geometry.type[0]}")
    
except Exception as e:
    print(f"✗ Failed to create GeoDataFrame")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test GeoPackage export
print("\n[6] Testing GeoPackage export...")
try:
    import tempfile
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.gpkg', delete=False) as tmp:
        temp_path = tmp.name
    
    # Export to GeoPackage
    gdf.to_file(temp_path, layer='test_layer', driver='GPKG')
    
    print(f"✓ GeoPackage export successful")
    print(f"  File: {temp_path}")
    print(f"  Size: {os.path.getsize(temp_path)} bytes")
    
    # Read it back
    gdf_read = gpd.read_file(temp_path)
    print(f"✓ GeoPackage read back successfully")
    print(f"  Rows: {len(gdf_read)}")
    
    # Clean up
    os.remove(temp_path)
    print(f"✓ Test file cleaned up")
    
except Exception as e:
    print(f"✗ Failed GeoPackage test")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Test ellipse creation
print("\n[7] Testing ellipse polygon creation...")
try:
    import numpy as np
    
    def test_ellipse(center_x, center_y, semi_major, semi_minor, orientation_deg, n_points=36):
        """Test ellipse creation"""
        a = semi_major
        b = semi_minor
        theta = np.radians(orientation_deg)
        
        t = np.linspace(0, 2*np.pi, n_points)
        x = a * np.cos(t)
        y = b * np.sin(t)
        
        x_rot = x * np.cos(theta) - y * np.sin(theta) + center_x
        y_rot = x * np.sin(theta) + y * np.cos(theta) + center_y
        
        return Polygon(zip(x_rot, y_rot))
    
    ellipse = test_ellipse(100, 50, 10, 5, 45)
    print(f"✓ Ellipse created successfully")
    print(f"  Type: {ellipse.geom_type}")
    print(f"  Area: {ellipse.area:.2f}")
    
except Exception as e:
    print(f"✗ Failed to create ellipse")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print()
print("Geopandas is working correctly in this environment.")
print("If running in bundled .exe, GeoPackage export should work.")
