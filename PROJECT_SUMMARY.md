# Dual Data Viewer - Project Summary

## 🎯 What We Built (Skeleton v1.0)

A functional PySide6 application that:

1. **Loads two datasets**:
   - USBL location data (~4k points, ~1Hz, with error ellipse parameters)
   - High-frequency sensor data (~400k points, ~20Hz, multiple columns)

2. **Visualizes data in dual panels**:
   - Top: Scatter plot of location data (will convert lat/lon → UTM)
   - Bottom: Time series plot with selectable columns

3. **Links selection between panels**:
   - Drag LinearRegionItem on time series
   - Corresponding location points highlight in red

4. **Manages regions**:
   - Save named regions (with timestamp ranges)
   - Export tagged data as CSV

## 📊 Validated with Your Data

### USBL Data (`RR2509-D18_usbl.csv`)
- ✅ 3,910 rows loaded
- ✅ 3 beacons: RV R. Revelle (3773), MARSS 5212 (81), SNTRY 5206 (56)
- ✅ ~2h 48min duration
- ✅ Error ellipses: avg 2.11m major/minor axis
- ✅ Timezone-aware timestamps

### Sensor Data (`sensor_export_*.csv`)
- ✅ 391,886 rows loaded
- ✅ 24.4 Hz sampling rate
- ✅ ~4h 39min duration
- ✅ 4 columns: Tilt Z, Total G, tension, payout
- ✅ Handles missing data (some columns have gaps)
- ✅ Skips comment header automatically

### Time Alignment
- ✅ Overlap detected and validated
- ✅ Both datasets timezone-aware for proper comparison

## 🏗️ Architecture

```
DualDataViewer
│
├── Data Layer
│   ├── usbl_df (pandas DataFrame)
│   │   ├── datetime (tz-aware)
│   │   ├── lat/lon → easting/northing (via pyproj)
│   │   └── error ellipse params
│   │
│   └── sensor_df (pandas DataFrame)
│       ├── datetime (tz-aware)
│       └── multiple numeric columns
│
├── UI Layer
│   ├── Control Panel (load, save region, export)
│   ├── Location Plot (PyQtGraph ScatterPlot)
│   │   ├── All points (blue)
│   │   └── Selected points (red overlay)
│   │
│   └── Time Series Plot (PyQtGraph with DateAxis)
│       ├── PlotCurve (selected column)
│       └── LinearRegionItem (draggable selector)
│
└── Interaction
    └── region.sigRegionChanged → filter USBL by datetime
```

## 🚀 How to Use

### Installation
```bash
pip install -r requirements.txt
```

### Running
```bash
python dual_data_viewer.py
```

### Workflow
1. Click "Load USBL Data" → select `RR2509-D18_usbl.csv`
2. Click "Load Sensor Data" → select `sensor_export_*.csv`
3. Select column from dropdown (e.g., "Tilt Z")
4. Drag red region on time series plot
5. Watch location plot highlight corresponding points
6. Click "Save Selected Region" → name it
7. Repeat for multiple regions
8. Click "Export Data" → saves CSVs with region tags

## 📝 Key Implementation Details

### Performance Optimizations
- `setDownsampling(auto=True, mode='peak')` - Auto LOD for large datasets
- `setClipToView(True)` - Only render visible data
- OpenGL backend available (needs explicit enable in code)
- Tested with 400k+ points - smooth interaction

### Datetime Handling
- `format='mixed'` for USBL data (inconsistent microseconds)
- `utc=True` for both datasets (timezone-aware comparison)
- `DateAxisItem` for proper time formatting on x-axis

### Spatial Data
- UTM conversion via `pyproj`
- Auto-detect UTM zone from first lat/lon point
- Equal-aspect plotting for accurate spatial representation

## 🔧 Next Implementation Phases

### Phase 2: Error Ellipses (Next Priority)
**Goal**: Visualize uncertainty on location plot

**Tasks**:
1. Calculate ellipse polygons from major/minor/direction
2. Add `EllipseROI` or custom `QtGui.QPainterPath` items
3. Option to show/hide ellipses
4. Color-code by beacon or error magnitude

**Code additions** (~100 lines):
```python
# In plot_location_data()
for idx, row in self.usbl_df.iterrows():
    ellipse = create_error_ellipse(
        row['easting'], row['northing'],
        row['hor_err_major'], row['hor_err_minor'],
        row['hor_err_dir']
    )
    self.location_plot.addItem(ellipse)
```

### Phase 3: Multi-Pane Time Series
**Goal**: Plot multiple parameters simultaneously

**UI Changes**:
- "Add Plot Pane" button
- QVBoxLayout with dynamic plot widgets
- Link all X-axes: `plot.setXLink(master_plot)`
- Shared LinearRegionItem across all panes

**Benefit**: Compare Tilt Z vs. Total G vs. tension simultaneously

### Phase 4: Enhanced Region Management
**Goal**: Better region organization

**Features**:
- List widget showing all saved regions
- Edit/delete regions
- Color-code regions on time series
- Multiple simultaneous selections with different colors
- Region notes/metadata

### Phase 5: Shapefile Export
**Goal**: GIS-compatible output

**Requirements**: `geopandas`, `shapely`

**Output files**:
- `locations.shp` - Point geometries with all attributes
- `error_ellipses.shp` - Polygon geometries
- `regions.shp` - Linestrings or polygons for each region

**Coordinate System**: Preserve UTM zone in .prj file

### Phase 6: Polish
- Session save/load (pickle or JSON)
- Beacon filtering checkboxes
- Statistics panel for selected region
- Export plots as PNG/SVG
- Keyboard shortcuts
- Undo/redo for region edits

## 🐛 Known Issues & Workarounds

1. **No error ellipses yet** → Phase 2
2. **Single time series pane** → Phase 3
3. **CSV export only** → Phase 5 adds shapefiles
4. **No session persistence** → Phase 6

## 📦 Files Delivered

```
dual_data_viewer.py          # Main application (484 lines)
test_data_loading.py         # Standalone data validator
requirements.txt             # Dependencies
README.md                    # User documentation
PROJECT_SUMMARY.md          # This file
```

## 🎓 Design Rationale

### Why This Architecture?

1. **PyQtGraph over Matplotlib**:
   - 10-100x faster for large datasets
   - Built-in downsampling and LOD
   - Interactive by default (zoom, pan)
   - DateAxisItem for time series

2. **Pandas for data management**:
   - Efficient datetime operations
   - Boolean indexing for filtering
   - Easy CSV I/O
   - Integration with geopandas

3. **Incremental complexity**:
   - Start simple, add features piece by piece
   - Each phase is independently testable
   - User can provide feedback early

4. **Separation of concerns**:
   - Data loading separate from plotting
   - Region management separate from visualization
   - Export logic modular (easy to add formats)

## 🤝 Questions for Next Session

1. **Error ellipse styling**:
   - Fill color/transparency?
   - Show all or just selected?
   - Toggle on/off?

2. **Multi-pane layout**:
   - Max number of panes?
   - Fixed height or dynamic?
   - Individual y-axis labels?

3. **Region colors**:
   - Auto-assign or user-choose?
   - Maximum simultaneous regions?

4. **Shapefile structure**:
   - Separate files per region?
   - Single file with region attribute?
   - Include only selected regions or all data?

5. **Additional features**:
   - Depth profile plot for USBL?
   - 3D visualization option?
   - Real-time data loading?

## ✅ Ready to Run!

The skeleton is complete and tested with your actual data. You can:

1. Install dependencies: `pip install -r requirements.txt`
2. Run application: `python dual_data_viewer.py`
3. Load your files and interact with the selection

Then we can incrementally add:
- Phase 2 (error ellipses)
- Phase 3 (multi-pane)
- Phase 4 (region management)
- Phase 5 (shapefiles)

Each phase is ~1-2 hours of development and can be tested independently.

Let me know which phase you'd like to tackle next! 🚀
