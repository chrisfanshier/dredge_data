# Dredge App - User Guide

Quick start guide for analyzing dredge sample locations.

---

## 🚀 Getting Started

### First Time Setup
1. Download the appropriate version:
   - **DredgeApp_Lite.exe** - Smaller, CSV export only
   - **DredgeApp_Full.exe** - Larger, includes GeoPackage export

2. **Windows SmartScreen Warning?**
   - Right-click the .exe → Properties
   - Check "Unblock" → Apply → OK
   - Or click "More info" → "Run anyway"

3. Double-click to launch!

---

## 📂 Loading Data

### Step 1: Load USBL Data
1. Click **"Load USBL Data"**
2. Select your `*_usbl.csv` file
3. ✓ Green checkmark appears
4. See your cast name at top: **"Core: RR2509-D15"**

### Step 2: Load Sensor Data
1. Click **"Load Sensor Data"**
2. Select your sensor CSV file
3. ✓ Green checkmark appears
4. Time series plots appear automatically

---

## 📊 Working with Plots

### Location Plot (Top)
- **Pan:** Left-click and drag
- **Zoom:** Mouse wheel
- Shows USBL positions (blue dots)
- Red dots = selected time range

### Time Series Plots (Bottom)
- **Default:** 2 plots shown
- **Add more:** Click "+ Add Plot" (max 4)
- **Change data:** Use dropdown menus
- **Zoom/Pan:** Mouse controls

### Plot Performance
- **Right-click on plot** → Downsample
  - Check "subsample" for smoother curves
  - Check "mean" for averaging
  - Useful for large datasets

---

## 🖌️ Creating Annotations

### 1. Enable Brush Mode
- Click **"🖌️ Brush Selection"** button
- Button turns green
- Blue selection region appears on plots

### 2. Select Time Range
- **Drag region edges** to adjust
- **Drag middle** to move entire region
- Location map shows selected USBL points in red

### 3. Save Annotation
- Click **"💾 Save Annotation"**
- Enter name: `effective_dredging`, `transit`, etc.
- Add notes (optional)
- Click OK

### 4. Repeat
- Select new region
- Save with different name
- Build up your annotation set

---

## 💾 Exporting Data

### Choose Export Format

**CSV (always available):**
- ☑ CSV (metadata + annotated USBL)
  - Creates 2 files:
    - `*_metadata.csv` - Annotation details
    - `*_usbl_annotated.csv` - USBL data with boolean columns

**GeoPackage (Full version only):**
- ☑ GeoPackage (spatial points)
  - Creates 1 file with 3 layers:
    - `usbl_points` - Point geometries
    - `error_ellipses_1sigma` - 68% confidence ellipses
    - `error_ellipses_95pct` - 95% confidence ellipses

### Export Process
1. Select format(s) - can choose both!
2. Click **"Export Annotated Data"**
3. Choose output folder
4. Files are created with timestamp
5. Success message shows what was exported

### Filenames
```
RR2509-D15_20260202_143530_metadata.csv
RR2509-D15_20260202_143530_usbl_annotated.csv
RR2509-D15_20260202_143530.gpkg
```
Format: `<CoreName>_<Timestamp>_<Type>`

---

## 🗺️ Using Exported Data

### In QGIS (Lite version):
1. **Add Layer** → Add Delimited Text Layer
2. Select `*_usbl_annotated.csv`
3. Set Geometry: `X field = easting`, `Y field = northing`
4. Set CRS to your UTM zone
5. **Filter by annotation:**
   - Right-click layer → Filter
   - Example: `effective_dredging = 1`

### In QGIS (Full version):
1. **Add Layer** → Add Vector Layer
2. Select `*.gpkg` file
3. All 3 layers load automatically!
4. **Filter by annotation:**
   - Same as above
   - Works on all 3 layers

### In ArcGIS:
1. **Add Data** → Navigate to .gpkg or .csv
2. For CSV: Right-click → Display XY Data
3. Use Definition Query to filter by annotations

---

## 💡 Tips & Tricks

### Multiple Annotations
- You can have overlapping annotations!
- Same USBL point can be in multiple annotations
- Use descriptive names: `dredge_haul_1`, `transit_to_station`

### Annotation Management
- **View all:** Check "Saved Annotations" panel on right
- **Delete one:** Select → Click "Delete"
- **Delete all:** Click "Clear All"

### No Annotations?
- You can still export!
- Gets you USBL data in GeoPackage format
- Useful for quick GIS visualization

### Performance
- Large datasets (>100K points) may lag
- Right-click plots → Enable downsampling
- Close unused plot panes (remove 3rd/4th plot)

### Saving Your Work
- Annotations are NOT saved automatically
- Export before closing!
- Each export gets unique timestamp
- Can't overwrite previous exports

---

## ❓ FAQ

**Q: Can I edit annotations after saving?**
A: Not directly. Delete and recreate, or edit the CSV manually.

**Q: What if my files don't load?**
A: Check format:
- USBL: Must have `datetime`, `latitude_deg`, `longitude_deg`
- Sensor: Must have `datetime` + numeric columns

**Q: Lite vs Full - which do I need?**
A: 
- Lite if you're comfortable with QGIS/Arc and don't mind converting CSV
- Full if you want one-click GeoPackage export

**Q: Why are my plots boxy when zoomed in?**
A: Downsampling is on. Right-click → Downsample → Uncheck to see full detail.

**Q: Can I change annotation names after export?**
A: In CSV, yes - edit the column headers. In GeoPackage, use QGIS to rename fields.

**Q: Do I need Python installed?**
A: No! The .exe is standalone.

**Q: What are error ellipses?**
A: (Full version only) Visual representation of USBL position uncertainty.
- 1σ = 68% confidence the true position is within ellipse
- 95% = 95% confidence (2.45× larger)

---

## 🐛 Troubleshooting

### App Won't Launch
- Install Visual C++ Redistributables: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Right-click .exe → Run as Administrator
- Check antivirus isn't blocking

### "No USBL data" error
- File must be .csv format
- Must have required columns
- Check for # comment lines at top

### Export Creates Empty Files
- Make sure data is actually loaded (green checkmarks)
- For GeoPackage: Lite version doesn't support it

### GeoPackage Won't Open in QGIS
- Make sure you downloaded Full version
- Update QGIS to latest version
- Try re-exporting

---

## 📧 Support

If you encounter issues:
1. Take a screenshot of the error
2. Note which version (Lite or Full)
3. Describe what you were doing
4. Contact your lab/IT support

---

## ✨ Keyboard Shortcuts

- **Ctrl + Mouse Wheel** - Zoom time series X-axis
- **Mouse Wheel** - Zoom time series Y-axis
- **Left Click + Drag** - Pan
- **Right Click** - Context menu

---

**Version 1.0 - February 2026**

### Missing DLL Error (MSVCP140.dll, VCRUNTIME140.dll, etc.)

If you see an error about a missing DLL (such as `MSVCP140.dll` or `VCRUNTIME140.dll`) when launching the app, you need to install the **Microsoft Visual C++ Redistributable**. This package provides system libraries required by many Windows applications.

**How to fix:**
1. Download the latest [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) from Microsoft.
2. Run the installer and follow the prompts.
3. Try launching the app again.

This is rarely needed, but may be required on some Windows systems.
