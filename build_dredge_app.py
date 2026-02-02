"""
Build script for Dredge App executables
Creates both Lite (CSV only) and Full (with GeoPackage) versions

Usage:
    python build_dredge_app_geo.py lite    # Build lite version (~100MB)
    python build_dredge_app_geo.py full    # Build full version (~400MB)
    python build_dredge_app_geo_geo.py both    # Build both versions

Requirements:
    pip install pyinstaller
"""

import sys
import subprocess
import os
import shutil


def clean_build_artifacts():
    """Remove previous build artifacts"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"🗑️  Removing {dir_name}/")
            shutil.rmtree(dir_name)
    
    import glob
    for pattern in files_to_remove:
        for file in glob.glob(pattern):
            print(f"🗑️  Removing {file}")
            os.remove(file)


def build_lite():
    """Build lite version without geopandas (CSV export only)"""
    print("\n" + "="*60)
    print("Building Dredge App LITE (CSV export only)")
    print("="*60 + "\n")
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable
        '--windowed',                   # No console window
        '--name=DredgeApp_Lite',        # Output name
        '--icon=NONE',                  # Add icon here if you have one
        
        # Add data files (if any)
        # '--add-data=skills:skills',
        
        # Hidden imports that PyInstaller might miss
        '--hidden-import=pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt6',
        '--hidden-import=pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt6',
        '--hidden-import=numpy.core._methods',
        '--hidden-import=numpy.lib.format',
        
        # Exclude geopandas and its heavy dependencies
        '--exclude-module=geopandas',
        '--exclude-module=fiona',
        '--exclude-module=shapely',
        '--exclude-module=rtree',
        '--exclude-module=pyogrio',
        
        'dredge_app_geo.py'
    ]
    
    print("📦 Running PyInstaller...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        exe_path = os.path.join('dist', 'DredgeApp_Lite.exe' if sys.platform == 'win32' else 'DredgeApp_Lite')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ Lite version built successfully!")
            print(f"   Location: {exe_path}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   Features: CSV export, all plotting features")
        else:
            print(f"\n❌ Build failed - executable not found")
            return False
    else:
        print(f"\n❌ PyInstaller failed with code {result.returncode}")
        return False
    
    return True


def build_full():
    """Build full version with geopandas (GeoPackage export)"""
    print("\n" + "="*60)
    print("Building Dredge App FULL (with GeoPackage support)")
    print("="*60 + "\n")
    
    # Check if geopandas is installed
    try:
        import geopandas
        print(f"✓ geopandas {geopandas.__version__} detected")
    except ImportError:
        print("❌ Error: geopandas not installed!")
        print("   Install with: pip install geopandas")
        return False
    
    # Get the directory where this script is located (for custom hooks)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=DredgeApp_Full',
        '--icon=NONE',
        
        # Add custom hooks directory
        f'--additional-hooks-dir={script_dir}',
        
        # Hidden imports
        '--hidden-import=pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt6',
        '--hidden-import=pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt6',
        '--hidden-import=numpy.core._methods',
        '--hidden-import=numpy.lib.format',
        
        # Core packages
        '--hidden-import=geopandas',
        '--hidden-import=pandas',
        '--hidden-import=shapely',
        '--hidden-import=shapely.geometry',
        '--hidden-import=pyproj',
        
        # Fiona - let the custom hook handle it
        '--hidden-import=fiona',
        
        # Collect everything
        '--collect-all=geopandas',
        '--collect-all=fiona',
        '--collect-all=pyproj',
        '--collect-all=shapely',
        '--collect-all=pandas',
        
        # Collect binaries (DLLs)
        '--collect-binaries=fiona',
        '--collect-binaries=shapely',
        '--collect-binaries=pyproj',
        '--collect-binaries=gdal',
        '--collect-binaries=osgeo',
        
        'dredge_app_geo.py'
    ]
    
    print("📦 Running PyInstaller (this may take 5-10 minutes)...")
    print(f"   Using custom hooks from: {script_dir}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        exe_path = os.path.join('dist', 'DredgeApp_Full.exe' if sys.platform == 'win32' else 'DredgeApp_Full')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ Full version built successfully!")
            print(f"   Location: {exe_path}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   Features: CSV + GeoPackage export (points + ellipses)")
        else:
            print(f"\n❌ Build failed - executable not found")
            return False
    else:
        print(f"\n❌ PyInstaller failed with code {result.returncode}")
        return False
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_dredge_app_geo.py [lite|full|both]")
        print()
        print("Options:")
        print("  lite  - Build lite version without GeoPackage (~100MB)")
        print("  full  - Build full version with GeoPackage (~400MB)")
        print("  both  - Build both versions")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode not in ['lite', 'full', 'both']:
        print(f"❌ Invalid option: {mode}")
        print("   Choose: lite, full, or both")
        sys.exit(1)
    
    # Clean previous builds
    print("🧹 Cleaning previous build artifacts...")
    clean_build_artifacts()
    
    success = True
    
    if mode in ['lite', 'both']:
        if not build_lite():
            success = False
    
    if mode in ['full', 'both']:
        if not build_full():
            success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ Build complete!")
        print("="*60)
        print()
        print("📁 Executables are in the 'dist/' folder")
        print()
        if mode == 'both' or mode == 'lite':
            print("   DredgeApp_Lite.exe  - Lightweight, CSV export only")
        if mode == 'both' or mode == 'full':
            print("   DredgeApp_Full.exe  - Full features, GeoPackage support")
        print()
        print("💡 Tip: Test both executables before distributing")
    else:
        print("❌ Build failed - see errors above")
        print("="*60)
        sys.exit(1)


if __name__ == '__main__':
    main()
