# Dredge App - USBL Data Visualization

## Installation

### Option 1: Lite Version (Executable - CSV Export Only)
Download and run `DredgeApp_Lite.exe` - no installation required.

### Option 2: Full Version (Python - with GeoPackage Support)

1. **Install Python 3.10 or later**
   - Download from https://www.python.org/downloads/

2. **Create a virtual environment**
   ```bash
   python -m venv venv_dredge_app
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv_dredge_app\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source venv_dredge_app/bin/activate
     ```

4. **Install dependencies**
   - For CSV export only:
     ```bash
     pip install -r requirements.txt
     ```
   - For GeoPackage export support:
     ```bash
     pip install -r requirements.txt
     pip install geopandas fiona shapely
     ```

5. **Run the application**
   ```bash
   python dredge_app_geo.py
   ```

## Features

- USBL location visualization with error ellipses
- Multiple time-series plots with linked selection
- Beacon filtering
- Data annotations
- Export options:
  - CSV (all versions)
  - GeoPackage with UTM coordinates (Python version with geopandas)

## Troubleshooting

### GeoPackage export not available
If you see "GeoPackage export requires geopandas", install it:
```bash
pip install geopandas
```

Note: On Windows, this may require additional dependencies. If installation fails, use CSV export instead.