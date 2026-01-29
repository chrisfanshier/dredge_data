# Dual Data Viewer - USBL & Time Series Visualization

A PySide6 application for visualizing and analyzing USBL location data alongside high-frequency sensor data.

## Installation

```bash
pip install pyside6 pyqtgraph pandas pyproj numpy
```

## Running the Application

```bash
python dual_data_viewer.py
```

## Current Features (Skeleton v1.0)

### ✅ Implemented
- [x] Dual-panel layout (location top, time series bottom)
- [x] Load USBL CSV data with automatic lat/lon → UTM conversion
- [x] Load high-frequency sensor CSV data
- [x] Plot location data as scatter plot
- [x] Plot time series with selectable columns
- [x] Linear region selector on time series
- [x] Linked selection: drag region → highlight corresponding location points
- [x] PyQtGraph with OpenGL backend for performance
- [x] Auto-downsampling for large datasets
- [x] Save named regions
- [x] Basic CSV export with region tags

### 🔄 Architecture Overview

```
DualDataViewer (QMainWindow)
│
├── Control Panel
│   ├── Load USBL Data button
│   ├── Load Sensor Data button
│   ├── Save Region button
│   └── Export Data button
│
├── Location Plot (40% height)
│   ├── PlotWidget (PyQtGraph)
│   ├── ScatterPlotItem (all USBL points, blue)
│   └── ScatterPlotItem (selected points, red)
│
└── Time Series Plot (60% height)
    ├── Column selector dropdown
    ├── PlotWidget (PyQtGraph with DateAxisItem)
    ├── PlotCurveItem (time series data)
    └── LinearRegionItem (draggable selection)
```

### 📊 Data Flow

1. **Load USBL Data**
   - Parse CSV → pandas DataFrame
   - Convert datetime strings → datetime objects
   - Convert lat/lon → UTM (auto-detect zone)
   - Store: easting, northing, error ellipse params

2. **Load Sensor Data**
   - Parse CSV (skip comment lines)
   - Convert datetime strings → datetime objects
   - Populate column selector with numeric columns

3. **Link Selection**
   - User drags LinearRegionItem on time series
   - Get time range from region
   - Filter USBL dataframe by datetime range
   - Update highlighted scatter plot on location map

4. **Save Regions**
   - User clicks "Save Region"
   - Prompt for region name
   - Store {name, start_time, end_time}

5. **Export**
   - Add boolean columns to dataframes (one per region)
   - Export to CSV

## Performance Optimizations

- **OpenGL acceleration**: Enabled for both plots
- **Auto-downsampling**: PyQtGraph automatically downsamples when zoomed out
- **ClipToView**: Only renders visible data
- **Peak mode**: Preserves min/max when downsampling

Tested with:
- USBL: ~1 Hz, 6-8 hours = ~30k points ✓
- Sensor: 20 Hz, 6-8 hours = ~500k points ✓

## Next Steps - Incremental Implementation

### Phase 2: Error Ellipses
- [ ] Add `EllipseROI` items to location plot
- [ ] Calculate ellipse parameters from hor_err_major/minor/dir
- [ ] Render ellipses with transparency
- [ ] Toggle ellipse visibility

### Phase 3: Multi-Pane Time Series
- [ ] Add "Add Plot Pane" button
- [ ] Create QVBoxLayout container for multiple plots
- [ ] Link all plot X-axes with `setXLink()`
- [ ] Share single LinearRegionItem across all panes
- [ ] Independent column selectors per pane

### Phase 4: Enhanced Region Management
- [ ] Region list widget showing all saved regions
- [ ] Edit/delete regions
- [ ] Color-code regions on time series
- [ ] Multiple simultaneous regions with different colors
- [ ] Region metadata (notes, tags)

### Phase 5: Shapefile Export
- [ ] Add `geopandas` and `shapely` dependencies
- [ ] Create Point geometries from easting/northing
- [ ] Create Polygon geometries from error ellipses
- [ ] Export as .shp with all attributes
- [ ] Preserve coordinate reference system (UTM zone)

### Phase 6: Advanced Features
- [ ] Zoom/pan synchronization options
- [ ] Statistics panel (mean, std, etc. for selected region)
- [ ] Export plots as images
- [ ] Session save/load (persist regions and selections)
- [ ] Beacon filtering (ship vs. MARSS)
- [ ] Fix status filtering

## File Structure

```
dual_data_viewer.py          # Main application
README.md                    # This file
examples/
    RR2509-D18_usbl.csv     # Example USBL data
    sensor_export_*.csv      # Example sensor data
```

## Data Format Requirements

### USBL Data CSV
Required columns:
- `datetime`: Timestamp (parseable by pandas)
- `latitude_deg`: Latitude in decimal degrees
- `longitude_deg`: Longitude in decimal degrees
- `hor_err_major`: Horizontal error major axis (meters)
- `hor_err_minor`: Horizontal error minor axis (meters)
- `hor_err_dir`: Horizontal error direction (degrees)

### Sensor Data CSV
Required columns:
- `datetime`: Timestamp (parseable by pandas)
- Any number of numeric columns for time series plotting

## Known Limitations (To Be Addressed)

1. **Error ellipses not rendered** - Coming in Phase 2
2. **Single time series pane only** - Coming in Phase 3
3. **CSV export only** - Shapefiles coming in Phase 5
4. **No zoom history/controls** - Built-in to PyQtGraph (mouse wheel, right-drag)
5. **No session persistence** - Coming in Phase 6

## Design Decisions

### Why PyQtGraph + OpenGL?
- Native support for large datasets (100k+ points)
- Auto-downsampling with level-of-detail
- DateAxisItem for proper time formatting
- LinearRegionItem for selection
- Active development and good documentation

### Why UTM Conversion?
- Error ellipses require projected coordinates (meters)
- Equal-distance plotting for spatial accuracy
- Standard in marine/subsea applications

### Why Pandas?
- Efficient datetime parsing and filtering
- Boolean indexing for region tagging
- Easy CSV I/O
- Integration with geopandas for shapefiles

## Contributing

This is structured for incremental development. Each phase can be implemented and tested independently.

## Testing with Your Data

```python
# Load your files
viewer.load_usbl_data()  # Select: RR2509-D18_usbl.csv
viewer.load_sensor_data()  # Select: sensor_export_*.csv

# Interact
1. Drag the red region on time series plot
2. Watch location plot highlight corresponding points
3. Click "Save Region" and name it
4. Repeat for multiple regions
5. Click "Export Data" to save tagged CSVs
```

## Questions/Feedback

- Ellipse rendering style preferences?
- Max number of simultaneous plot panes?
- Additional metadata for regions?
- Preferred shapefile structure?
