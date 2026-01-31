"""
Dredge App - USBL Location and Time Series Data Visualization
Minimal Skeleton v1.1

Requirements:
    pip install pyside6 pyqtgraph pandas pyproj numpy

Architecture:
    - Top: Location plot (USBL data with error ellipses)
    - Bottom: Time series plot(s) (high-frequency sensor data)
    - Linked selection: drag region on time series → highlight on location plot
"""

import sys
import pandas as pd
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from pyproj import Transformer
from datetime import datetime


class DredgeApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dredge App - USBL & Time Series Viewer")
        self.resize(1400, 900)
        
        # Data storage
        self.usbl_df = None
        self.sensor_df = None
        self.utm_transformer = None
        self.utm_zone = None  # String like "10N"
        self.utm_epsg = None  # EPSG code like "EPSG:32610"
        self.core_name = None  # Extracted from USBL filename
        
        # Annotations storage
        self.annotations = []  # List of annotation dictionaries with full metadata
        self.annotation_id_counter = 1  # For unique IDs
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget with splitter
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Control panel at top
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Horizontal splitter for main content and annotations panel
        h_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        h_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ccc;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #999;
            }
        """)
        
        # Vertical splitter for location and time series plots (left side)
        v_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        v_splitter.setHandleWidth(6)
        v_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bbb;
                height: 6px;
            }
            QSplitter::handle:hover {
                background-color: #4CAF50;
            }
        """)
        
        # Location plot (top)
        self.location_plot_widget = self.create_location_plot()
        v_splitter.addWidget(self.location_plot_widget)
        
        # Time series plot (bottom)
        self.timeseries_plot_widget = self.create_timeseries_plot()
        v_splitter.addWidget(self.timeseries_plot_widget)
        
        # Set initial sizes for vertical splitter (40% location, 60% time series)
        v_splitter.setSizes([360, 540])
        
        h_splitter.addWidget(v_splitter)
        
        # Annotations panel (right side)
        self.annotations_panel = self.create_annotations_panel()
        h_splitter.addWidget(self.annotations_panel)
        
        # Set initial sizes for horizontal splitter (75% plots, 25% annotations)
        h_splitter.setSizes([900, 300])
        
        main_layout.addWidget(h_splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready - Load data files to begin")
        
    def create_control_panel(self):
        """Create the control panel with file loading buttons"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(panel)
        
        # USBL file loading
        usbl_btn = QtWidgets.QPushButton("Load USBL Data")
        usbl_btn.clicked.connect(self.load_usbl_data)
        layout.addWidget(usbl_btn)
        
        self.usbl_label = QtWidgets.QLabel("No USBL data")
        self.usbl_label.setStyleSheet("color: gray;")
        layout.addWidget(self.usbl_label)
        
        # Beacon filter
        layout.addWidget(QtWidgets.QLabel("Beacon:"))
        self.beacon_selector = QtWidgets.QComboBox()
        self.beacon_selector.addItem("All Beacons")
        self.beacon_selector.currentTextChanged.connect(self.update_beacon_filter)
        layout.addWidget(self.beacon_selector)
        
        layout.addSpacing(20)
        
        # Sensor file loading
        sensor_btn = QtWidgets.QPushButton("Load Sensor Data")
        sensor_btn.clicked.connect(self.load_sensor_data)
        layout.addWidget(sensor_btn)
        
        self.sensor_label = QtWidgets.QLabel("No sensor data")
        self.sensor_label.setStyleSheet("color: gray;")
        layout.addWidget(self.sensor_label)
        
        layout.addStretch()
        
        return panel
    
    def create_annotations_panel(self):
        """Create the annotations management panel (right side)"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QtWidgets.QLabel("Saved Annotations")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Annotations list
        self.annotations_list = QtWidgets.QListWidget()
        self.annotations_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.annotations_list)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.delete_annotation_btn = QtWidgets.QPushButton("Delete")
        self.delete_annotation_btn.clicked.connect(self.delete_annotation)
        self.delete_annotation_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_annotation_btn)
        
        self.clear_annotations_btn = QtWidgets.QPushButton("Clear All")
        self.clear_annotations_btn.clicked.connect(self.clear_annotations)
        btn_layout.addWidget(self.clear_annotations_btn)
        
        layout.addLayout(btn_layout)
        
        layout.addSpacing(10)
        
        # Export section
        export_label = QtWidgets.QLabel("Export")
        export_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(export_label)
        
        # Export format checkboxes
        format_label = QtWidgets.QLabel("Export Format:")
        format_label.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(format_label)
        
        self.export_csv_checkbox = QtWidgets.QCheckBox("CSV (metadata + annotated USBL)")
        self.export_csv_checkbox.setChecked(True)
        layout.addWidget(self.export_csv_checkbox)
        
        # Check if geopandas is available
        try:
            import geopandas
            gpkg_available = True
            gpkg_tooltip = "Export as GeoPackage with UTM coordinates"
        except ImportError:
            gpkg_available = False
            gpkg_tooltip = "GeoPackage export requires 'geopandas' library\nInstall with: pip install geopandas"
        
        self.export_gpkg_checkbox = QtWidgets.QCheckBox("GeoPackage (spatial points)")
        self.export_gpkg_checkbox.setChecked(False)
        self.export_gpkg_checkbox.setEnabled(gpkg_available)
        self.export_gpkg_checkbox.setToolTip(gpkg_tooltip)
        if not gpkg_available:
            self.export_gpkg_checkbox.setStyleSheet("color: gray;")
        layout.addWidget(self.export_gpkg_checkbox)
        
        layout.addSpacing(5)
        
        self.export_annotated_btn = QtWidgets.QPushButton("Export Annotated Data")
        self.export_annotated_btn.clicked.connect(self.export_annotated_data)
        self.export_annotated_btn.setEnabled(True)  # Always enabled now (can export without annotations)
        layout.addWidget(self.export_annotated_btn)
        
        # Enable selection handling
        self.annotations_list.itemSelectionChanged.connect(self.on_annotation_selected)
        
        return panel
        
    def create_location_plot(self):
        """Create the location plot widget (top panel)"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QtWidgets.QLabel("Location Plot (USBL Data)")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # PyQtGraph plot widget with OpenGL
        self.location_plot = pg.PlotWidget()
        self.location_plot.setBackground('w')
        self.location_plot.showGrid(x=True, y=True, alpha=0.3)
        self.location_plot.setLabel('left', 'Northing (m)')
        self.location_plot.setLabel('bottom', 'Easting (m)')
        self.location_plot.setAspectLocked(True)  # Equal aspect ratio for maps
        
        # Enable mouse controls
        viewbox = self.location_plot.getViewBox()
        viewbox.setMouseMode(pg.ViewBox.PanMode)
        viewbox.setMenuEnabled(True)
        
        layout.addWidget(self.location_plot)
        
        # Scatter plot items
        self.location_scatter = pg.ScatterPlotItem(
            size=6, 
            pen=pg.mkPen(None), 
            brush=pg.mkBrush(0, 100, 200, 120)
        )
        self.location_plot.addItem(self.location_scatter)
        
        # Highlighted selection scatter
        self.location_selection_scatter = pg.ScatterPlotItem(
            size=8,
            pen=pg.mkPen('r', width=2),
            brush=pg.mkBrush(255, 0, 0, 180)
        )
        self.location_plot.addItem(self.location_selection_scatter)
        
        return widget
        
    def create_timeseries_plot(self):
        """Create dynamic time series plot widget with add/remove capability"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header row with all controls in one line
        header = QtWidgets.QHBoxLayout()
        
        label = QtWidgets.QLabel("Time Series:")
        label.setStyleSheet("font-weight: bold;")
        header.addWidget(label)
        
        # Container for plot selectors (will be dynamically populated)
        self.plot_selectors_layout = QtWidgets.QHBoxLayout()
        header.addLayout(self.plot_selectors_layout)
        
        # Add plot button
        self.add_plot_btn = QtWidgets.QPushButton("+ Add Plot")
        self.add_plot_btn.clicked.connect(self.add_plot)
        self.add_plot_btn.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        header.addWidget(self.add_plot_btn)
        
        header.addSpacing(20)
        
        # Brush selection toggle
        self.brush_mode_btn = QtWidgets.QPushButton("🖌️ Brush Selection")
        self.brush_mode_btn.setCheckable(True)
        self.brush_mode_btn.setStyleSheet("""
            QPushButton { padding: 5px 10px; }
            QPushButton:checked { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold;
            }
        """)
        self.brush_mode_btn.clicked.connect(self.toggle_brush_mode)
        header.addWidget(self.brush_mode_btn)
        
        # Save annotation button
        self.save_annotation_btn = QtWidgets.QPushButton("💾 Save Annotation")
        self.save_annotation_btn.setEnabled(False)
        self.save_annotation_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        self.save_annotation_btn.clicked.connect(self.save_annotation)
        header.addWidget(self.save_annotation_btn)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Container for plots (will hold dynamically added plots)
        self.plots_container = QtWidgets.QWidget()
        self.plots_layout = QtWidgets.QVBoxLayout(self.plots_container)
        self.plots_layout.setContentsMargins(0, 5, 0, 0)
        self.plots_layout.setSpacing(2)
        layout.addWidget(self.plots_container)
        
        # Storage for plot objects
        self.plot_widgets = []  # List of PlotWidget objects
        self.plot_curves = []   # List of curve objects
        self.plot_selectors = []  # List of combo boxes
        self.plot_regions = []  # List of brush regions
        
        # Store current X-range for keeping axis fixed when changing columns
        self.fixed_x_range = None
        
        # Initialize with 2 plots
        self.add_plot()  # Plot 1
        self.add_plot()  # Plot 2
        
        return widget
    
    def add_plot(self):
        """Add a new time series plot"""
        plot_num = len(self.plot_widgets) + 1
        
        # Maximum 4 plots
        if plot_num > 4:
            QtWidgets.QMessageBox.information(
                self, "Maximum Plots",
                "Maximum of 4 time series plots allowed."
            )
            return
        
        # Disable add button if we're at max
        if plot_num >= 4:
            self.add_plot_btn.setEnabled(False)
        
        # Create selector in header row
        selector_container = QtWidgets.QWidget()
        selector_layout = QtWidgets.QHBoxLayout(selector_container)
        selector_layout.setContentsMargins(0, 0, 10, 0)
        
        selector_label = QtWidgets.QLabel(f"Plot {plot_num}:")
        selector_label.setStyleSheet("font-size: 11px;")
        selector_layout.addWidget(selector_label)
        
        selector = QtWidgets.QComboBox()
        selector.setMinimumWidth(150)
        selector.currentTextChanged.connect(lambda: self.update_timeseries_plot(plot_num - 1))
        selector_layout.addWidget(selector)
        
        # Remove button (disabled for first 2 plots)
        remove_btn = QtWidgets.QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("font-weight: bold; font-size: 14px; padding: 0px;")
        remove_btn.clicked.connect(lambda: self.remove_plot(plot_num - 1))
        if plot_num <= 2:
            remove_btn.setEnabled(False)
            remove_btn.setVisible(False)
        selector_layout.addWidget(remove_btn)
        
        self.plot_selectors_layout.addWidget(selector_container)
        self.plot_selectors.append(selector)
        
        # Create plot widget - each needs its own axis item
        # Only the last plot shows axis labels
        is_last_plot = True  # This will be the last plot after adding
        
        if is_last_plot:
            # Create new DateAxisItem for this plot
            date_axis = pg.DateAxisItem(orientation='bottom')
            plot_widget = pg.PlotWidget(axisItems={'bottom': date_axis})
            plot_widget.setLabel('bottom', 'Time')
            
            # Hide labels on previous last plot if it exists
            if len(self.plot_widgets) > 0:
                prev_last = self.plot_widgets[-1]
                prev_last.getAxis('bottom').setStyle(showValues=False)
        else:
            plot_widget = pg.PlotWidget()
            plot_widget.getAxis('bottom').setStyle(showValues=False)
        
        plot_widget.setBackground('w')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Link to first plot's X-axis (so they all zoom together)
        if len(self.plot_widgets) > 0:
            plot_widget.setXLink(self.plot_widgets[0])
        
        # Enable performance features
        plot_widget.setClipToView(True)
        plot_widget.setDownsampling(auto=True, mode='peak')
        
        # Enable mouse controls
        viewbox = plot_widget.getViewBox()
        viewbox.setMouseMode(pg.ViewBox.PanMode)
        viewbox.setMenuEnabled(True)
        viewbox.setAspectLocked(False)
        
        self.plots_layout.addWidget(plot_widget)
        self.plot_widgets.append(plot_widget)
        
        # Create curve
        # Colors: Blue, Red, Orange, Purple (easier on eyes than green/magenta)
        colors = [
            (31, 119, 180),   # Blue
            (214, 39, 40),    # Red
            (255, 127, 14),   # Orange
            (148, 103, 189)   # Purple
        ]
        curve = plot_widget.plot(
            pen=pg.mkPen(colors[plot_num - 1], width=1.5),
            connect='finite'
        )
        self.plot_curves.append(curve)
        
        # Create brush region
        region = pg.LinearRegionItem(
            brush=pg.mkBrush(100, 150, 255, 80),
            movable=True
        )
        region.setZValue(10)
        region.setVisible(False)
        region.sigRegionChanged.connect(lambda: self._sync_regions(plot_num - 1))
        plot_widget.addItem(region)
        self.plot_regions.append(region)
        
        # Populate selector if we have data
        if self.sensor_df is not None:
            numeric_columns = [col for col in self.sensor_df.columns 
                             if col != 'datetime' and pd.api.types.is_numeric_dtype(self.sensor_df[col])]
            selector.blockSignals(True)
            selector.clear()
            selector.addItems(numeric_columns)
            if plot_num <= len(numeric_columns):
                selector.setCurrentIndex(plot_num - 1)
            selector.blockSignals(False)
            self.update_timeseries_plot(plot_num - 1)
    
    def remove_plot(self, plot_idx):
        """Remove a plot (can't remove first 2)"""
        if plot_idx < 2:
            return
        
        # Remove widgets
        selector_widget = self.plot_selectors_layout.itemAt(plot_idx).widget()
        self.plot_selectors_layout.removeWidget(selector_widget)
        selector_widget.deleteLater()
        
        plot_widget = self.plot_widgets[plot_idx]
        self.plots_layout.removeWidget(plot_widget)
        plot_widget.deleteLater()
        
        # Remove from lists
        del self.plot_selectors[plot_idx]
        del self.plot_widgets[plot_idx]
        del self.plot_curves[plot_idx]
        del self.plot_regions[plot_idx]
        
        # Re-enable add button
        self.add_plot_btn.setEnabled(True)
        
        # Update the last plot to have the date axis
        if len(self.plot_widgets) > 0:
            # Remove date axis from all plots
            for pw in self.plot_widgets[:-1]:
                pw.getAxis('bottom').setStyle(showValues=False)
            # Add to last plot
            # Note: Can't easily reassign axis items, so just show values
            self.plot_widgets[-1].getAxis('bottom').setStyle(showValues=True)
    
    def _sync_regions(self, source_idx):
        """Synchronize brush regions between all plots"""
        if not hasattr(self, 'plot_regions') or len(self.plot_regions) == 0:
            return
        
        source_region = self.plot_regions[source_idx]
        new_range = source_region.getRegion()
        
        # Update all other regions
        for i, region in enumerate(self.plot_regions):
            if i != source_idx:
                region.blockSignals(True)
                region.setRegion(new_range)
                region.blockSignals(False)
        
        # Trigger annotation highlight update
        self.on_region_changed()
        
    def load_usbl_data(self):
        """Load USBL data from CSV file"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select USBL Data File", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
            
        try:
            # Extract core name from filename (e.g., "RR2509-D13" from "RR2509-D13_usbl.csv")
            import os
            basename = os.path.basename(filename)
            # Remove extension and common suffixes
            core_name = basename.replace('.csv', '').replace('_usbl', '').replace('_USBL', '')
            self.core_name = core_name
            
            # Load data
            self.usbl_df = pd.read_csv(filename)
            
            # Parse datetime with mixed format support
            self.usbl_df['datetime'] = pd.to_datetime(self.usbl_df['datetime'], format='mixed', utc=True)
            
            # Convert lat/lon to UTM
            self.convert_to_utm()
            
            # Update UI
            self.usbl_label.setText(f"✓ {len(self.usbl_df)} USBL points")
            self.usbl_label.setStyleSheet("color: green;")
            
            # Populate beacon selector
            if 'beacon_name' in self.usbl_df.columns:
                beacons = self.usbl_df['beacon_name'].unique()
                self.beacon_selector.clear()
                self.beacon_selector.addItem("All Beacons")
                for beacon in beacons:
                    count = (self.usbl_df['beacon_name'] == beacon).sum()
                    self.beacon_selector.addItem(f"{beacon} ({count})")
            
            # Plot location data
            self.plot_location_data()
            
            self.statusBar().showMessage(f"Loaded USBL data: {len(self.usbl_df)} points")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load USBL data:\n{str(e)}")
            
    def load_sensor_data(self):
        """Load sensor data from CSV file"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Sensor Data File", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
            
        try:
            # Load data, skipping comment lines
            with open(filename, 'r') as f:
                lines = f.readlines()
                # Find where actual data starts (after # comments)
                data_start = 0
                for i, line in enumerate(lines):
                    if not line.startswith('#'):
                        data_start = i
                        break
            
            self.sensor_df = pd.read_csv(filename, skiprows=data_start)
            
            # Parse datetime with mixed format to handle inconsistent microseconds
            self.sensor_df['datetime'] = pd.to_datetime(self.sensor_df['datetime'], format='mixed')
            # Make timezone-aware if it's timezone-naive
            if self.sensor_df['datetime'].dt.tz is None:
                self.sensor_df['datetime'] = self.sensor_df['datetime'].dt.tz_localize('UTC')
            
            # Update all plot column selectors
            numeric_columns = [col for col in self.sensor_df.columns 
                             if col != 'datetime' and pd.api.types.is_numeric_dtype(self.sensor_df[col])]
            
            # Block signals while populating
            for selector in self.plot_selectors:
                selector.blockSignals(True)
                selector.clear()
                selector.addItems(numeric_columns)
            
            # Set different defaults for each plot
            for i, selector in enumerate(self.plot_selectors):
                if i < len(numeric_columns):
                    selector.setCurrentIndex(i)
                selector.blockSignals(False)
            
            # Manually trigger updates for all plots
            for i in range(len(self.plot_widgets)):
                self.update_timeseries_plot(i)
            
            # Update UI
            self.sensor_label.setText(f"✓ {len(self.sensor_df)} sensor points ({len(numeric_columns)} columns)")
            self.sensor_label.setStyleSheet("color: green;")
                
            self.statusBar().showMessage(f"Loaded sensor data: {len(self.sensor_df)} points")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load sensor data:\n{str(e)}")
            
    def convert_to_utm(self):
        """Convert lat/lon to UTM coordinates"""
        if self.usbl_df is None:
            return
            
        # Determine UTM zone from first point
        lon = self.usbl_df['longitude_deg'].iloc[0]
        lat = self.usbl_df['latitude_deg'].iloc[0]
        
        # Calculate UTM zone
        utm_zone = int((lon + 180) / 6) + 1
        hemisphere = 'north' if lat >= 0 else 'south'
        
        # Store zone with hemisphere (e.g., "10N")
        self.utm_zone = f"{utm_zone}{hemisphere[0].upper()}"
        
        # Store EPSG code for easy access
        self.utm_epsg = f"EPSG:326{utm_zone:02d}" if hemisphere == 'north' else f"EPSG:327{utm_zone:02d}"
        
        # Create transformer
        self.utm_transformer = Transformer.from_crs(
            "EPSG:4326",  # WGS84
            self.utm_epsg,
            always_xy=True
        )
        
        # Transform coordinates
        easting, northing = self.utm_transformer.transform(
            self.usbl_df['longitude_deg'].values,
            self.usbl_df['latitude_deg'].values
        )
        
        self.usbl_df['easting'] = easting
        self.usbl_df['northing'] = northing
        
        print(f"Converted to UTM Zone {utm_zone}{hemisphere[0].upper()}")
        
    def plot_location_data(self):
        """Plot USBL location data"""
        if self.usbl_df is None:
            return
        
        # Filter by beacon if selected
        df_to_plot = self.usbl_df
        selected_beacon = self.beacon_selector.currentText()
        if selected_beacon != "All Beacons" and 'beacon_name' in self.usbl_df.columns:
            # Extract beacon name (before the count in parentheses)
            beacon_name = selected_beacon.split(' (')[0]
            df_to_plot = self.usbl_df[self.usbl_df['beacon_name'] == beacon_name]
            
        # Plot all points
        spots = [{
            'pos': (row['easting'], row['northing']),
            'data': i
        } for i, row in df_to_plot.iterrows()]
        
        self.location_scatter.setData(spots=spots)
        
        # Auto-range to fit data
        self.location_plot.autoRange()
        
    def update_beacon_filter(self):
        """Update location plot when beacon filter changes"""
        self.plot_location_data()
        # Also update the selected region highlight if brush mode is active
        if len(self.plot_regions) > 0 and self.plot_regions[0].isVisible():
            self.on_region_changed()
        
    def update_timeseries_plot(self, plot_idx):
        """Update time series plot with selected column
        
        Args:
            plot_idx: 0-based index of which plot to update
        """
        if self.sensor_df is None:
            return
        
        if plot_idx >= len(self.plot_widgets):
            return
            
        # Get the appropriate selector and plot objects
        column = self.plot_selectors[plot_idx].currentText()
        plot_widget = self.plot_widgets[plot_idx]
        curve = self.plot_curves[plot_idx]
            
        if not column:
            return
            
        # Store current X-range before updating (to keep axis fixed)
        viewbox = plot_widget.getViewBox()
        current_x_range = viewbox.viewRange()[0]
            
        # Filter out NaN values (common with sparse data from outer merge)
        valid_mask = self.sensor_df[column].notna()
        valid_data = self.sensor_df[valid_mask].reset_index(drop=True)
        
        if len(valid_data) == 0:
            # No data to plot
            curve.setData([], [])
            return
            
        # Convert datetime to timestamp (seconds since epoch) for x-axis
        time_values = valid_data['datetime'].values.astype('datetime64[s]').astype(np.float64)
        y_values = valid_data[column].values
        
        # Update the curve
        curve.setData(time_values, y_values)
        
        # Update axis labels
        plot_widget.setLabel('left', column)
        
        # Restore X-range to keep axis fixed when switching columns
        # Only do this if we had a previous range and it's valid
        if self.fixed_x_range is not None:
            viewbox.setXRange(*self.fixed_x_range, padding=0)
        elif current_x_range[0] != current_x_range[1]:
            # First time plotting - store the auto-range
            viewbox.enableAutoRange(axis='x')
            viewbox.enableAutoRange(axis='y')
            # After auto-range, store it
            QtCore.QTimer.singleShot(100, lambda: self._store_x_range(plot_widget))
    
    def _store_x_range(self, plot_widget):
        """Helper to store the current X-range after auto-ranging"""
        viewbox = plot_widget.getViewBox()
        self.fixed_x_range = viewbox.viewRange()[0]
        
    def toggle_brush_mode(self, checked):
        """Toggle between pan mode and brush selection mode"""
        if checked:
            # Enable brush selection mode on all plots
            self.brush_mode_btn.setText("🖌️ Brush Mode ON")
            self.save_annotation_btn.setEnabled(True)
            
            for plot_widget in self.plot_widgets:
                viewbox = plot_widget.getViewBox()
                viewbox.setMouseMode(pg.ViewBox.RectMode)
            
            # Show region selectors if we have data
            if self.sensor_df is not None and len(self.sensor_df) > 0 and len(self.plot_widgets) > 0:
                # Initialize region to middle of current view
                viewbox = self.plot_widgets[0].getViewBox()
                x_range = viewbox.viewRange()[0]
                center = (x_range[0] + x_range[1]) / 2
                width = (x_range[1] - x_range[0]) * 0.2
                region_range = [center - width/2, center + width/2]
                
                # Set all regions to same range and show them
                for region in self.plot_regions:
                    region.setRegion(region_range)
                    region.setVisible(True)
        else:
            # Back to pan mode on all plots
            self.brush_mode_btn.setText("🖌️ Brush Selection")
            self.save_annotation_btn.setEnabled(False)
            
            for plot_widget in self.plot_widgets:
                viewbox = plot_widget.getViewBox()
                viewbox.setMouseMode(pg.ViewBox.PanMode)
            
            # Hide all regions
            for region in self.plot_regions:
                region.setVisible(False)
            
            # Clear selection highlighting
            self.location_selection_scatter.setData([])
            self.statusBar().showMessage("Brush selection disabled")
        
    def on_region_changed(self):
        """Handle region selection change - update location plot"""
        if self.sensor_df is None or self.usbl_df is None:
            return
        
        if len(self.plot_regions) == 0:
            return
            
        # Get region bounds from first plot (all are synchronized)
        min_time, max_time = self.plot_regions[0].getRegion()
        
        # Convert back to datetime with UTC timezone to match USBL data
        min_dt = pd.Timestamp(min_time, unit='s', tz='UTC')
        max_dt = pd.Timestamp(max_time, unit='s', tz='UTC')
        
        # Filter USBL data by time range
        mask = (self.usbl_df['datetime'] >= min_dt) & (self.usbl_df['datetime'] <= max_dt)
        selected_usbl = self.usbl_df[mask]
        
        # Also filter by beacon if selected
        selected_beacon = self.beacon_selector.currentText()
        if selected_beacon != "All Beacons" and 'beacon_name' in selected_usbl.columns:
            beacon_name = selected_beacon.split(' (')[0]
            selected_usbl = selected_usbl[selected_usbl['beacon_name'] == beacon_name]
        
        # Update highlighted scatter plot
        if len(selected_usbl) > 0:
            spots = [{
                'pos': (row['easting'], row['northing']),
                'data': i
            } for i, row in selected_usbl.iterrows()]
            self.location_selection_scatter.setData(spots=spots)
        else:
            self.location_selection_scatter.setData([])
            
        # Update status
        self.statusBar().showMessage(
            f"Selected: {len(selected_usbl)} USBL points | "
            f"Time range: {min_dt.strftime('%H:%M:%S')} - {max_dt.strftime('%H:%M:%S')}"
        )
    
    @staticmethod
    def sanitize_field_name(name):
        """Sanitize annotation name for use as GIS field name
        
        Rules:
        - Replace spaces with underscores
        - Remove special characters (keep only alphanumeric and underscore)
        - Convert to lowercase
        - Truncate to 50 characters
        """
        import re
        # Replace spaces with underscores
        sanitized = name.replace(' ', '_')
        # Remove special characters
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
        # Convert to lowercase
        sanitized = sanitized.lower()
        # Truncate to 50 chars
        sanitized = sanitized[:50]
        return sanitized
        
    def save_annotation(self):
        """Save the current selected region as an annotation with full metadata"""
        if self.usbl_df is None or self.sensor_df is None:
            QtWidgets.QMessageBox.warning(self, "No Data", "Please load both USBL and sensor data first.")
            return
        
        # Check if we have any regions and if they're visible
        if len(self.plot_regions) == 0 or not self.plot_regions[0].isVisible():
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please enable brush mode and select a region first.")
            return
        
        # Get region bounds from first plot (all are synchronized)
        min_time, max_time = self.plot_regions[0].getRegion()
        min_dt = pd.Timestamp(min_time, unit='s', tz='UTC')
        max_dt = pd.Timestamp(max_time, unit='s', tz='UTC')
        
        # Filter USBL data by time range
        mask = (self.usbl_df['datetime'] >= min_dt) & (self.usbl_df['datetime'] <= max_dt)
        selected_usbl = self.usbl_df[mask]
        
        if len(selected_usbl) == 0:
            QtWidgets.QMessageBox.warning(self, "No Data", "No USBL points found in selected time range.")
            return
        
        # Prompt for annotation name and notes
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Save Annotation")
        dialog_layout = QtWidgets.QVBoxLayout(dialog)
        
        dialog_layout.addWidget(QtWidgets.QLabel("Annotation Name:"))
        name_input = QtWidgets.QLineEdit()
        name_input.setPlaceholderText("e.g., effective_dredging, transit, on_bottom")
        dialog_layout.addWidget(name_input)
        
        dialog_layout.addWidget(QtWidgets.QLabel("Notes (optional):"))
        notes_input = QtWidgets.QTextEdit()
        notes_input.setPlaceholderText("Additional details about this annotation...")
        notes_input.setMaximumHeight(80)
        dialog_layout.addWidget(notes_input)
        
        # Show preview
        preview_label = QtWidgets.QLabel(
            f"Time range: {min_dt.strftime('%Y-%m-%d %H:%M:%S')} to {max_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"USBL points: {len(selected_usbl)}"
        )
        preview_label.setStyleSheet("color: gray; font-size: 10px;")
        dialog_layout.addWidget(preview_label)
        
        # Buttons
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(btn_box)
        
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            name = name_input.text().strip()
            if not name:
                QtWidgets.QMessageBox.warning(self, "Invalid Name", "Please enter an annotation name.")
                return
            
            # Check for duplicate names
            existing_names = [ann['annotation_name'] for ann in self.annotations]
            if name in existing_names:
                QtWidgets.QMessageBox.warning(
                    self, "Duplicate Name", 
                    f"An annotation named '{name}' already exists.\n\n"
                    "Please choose a different name."
                )
                return
                
            # Get start/end coordinates (first and last USBL points in selection)
            start_point = selected_usbl.iloc[0]
            end_point = selected_usbl.iloc[-1]
            
            # Create annotation record with full metadata
            annotation = {
                'annotation_id': self.annotation_id_counter,
                'annotation_name': name,  # Original name for display
                'start_datetime': min_dt,
                'end_datetime': max_dt,
                'start_lat': start_point.get('latitude', None),
                'start_lon': start_point.get('longitude', None),
                'end_lat': end_point.get('latitude', None),
                'end_lon': end_point.get('longitude', None),
                'start_easting': start_point['easting'],
                'start_northing': start_point['northing'],
                'end_easting': end_point['easting'],
                'end_northing': end_point['northing'],
                'utm_zone': self.utm_zone,
                'num_usbl_points': len(selected_usbl),
                'notes': notes_input.toPlainText().strip()
            }
            
            self.annotations.append(annotation)
            self.annotation_id_counter += 1
            
            # Update annotations list UI
            self.refresh_annotations_list()
            
            self.statusBar().showMessage(f"Annotation '{name}' saved ({len(selected_usbl)} points)")
    
    def refresh_annotations_list(self):
        """Refresh the annotations list widget"""
        self.annotations_list.clear()
        for ann in self.annotations:
            item_text = f"[{ann['annotation_id']}] {ann['annotation_name']} ({ann['num_usbl_points']} pts)"
            self.annotations_list.addItem(item_text)
    
    def on_annotation_selected(self):
        """Handle annotation selection in the list"""
        self.delete_annotation_btn.setEnabled(len(self.annotations_list.selectedItems()) > 0)
    
    def delete_annotation(self):
        """Delete the selected annotation"""
        selected_items = self.annotations_list.selectedItems()
        if not selected_items:
            return
            
        selected_index = self.annotations_list.row(selected_items[0])
        ann = self.annotations[selected_index]
        
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Annotation",
            f"Delete annotation '{ann['annotation_name']}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.annotations.pop(selected_index)
            self.refresh_annotations_list()
                
            self.statusBar().showMessage(f"Annotation '{ann['annotation_name']}' deleted")
    
    def clear_annotations(self):
        """Clear all annotations"""
        if len(self.annotations) == 0:
            return
            
        reply = QtWidgets.QMessageBox.question(
            self, "Clear All Annotations",
            f"Delete all {len(self.annotations)} annotations?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.annotations = []
            self.refresh_annotations_list()
            self.statusBar().showMessage("All annotations cleared")
            
    def export_annotated_data(self):
        """Export USBL data with annotations in selected format(s)"""
        # Check format selection
        export_csv = self.export_csv_checkbox.isChecked()
        export_gpkg = self.export_gpkg_checkbox.isChecked()
        
        if not export_csv and not export_gpkg:
            QtWidgets.QMessageBox.warning(
                self, "No Format Selected",
                "Please select at least one export format (CSV or GeoPackage)."
            )
            return
            
        if self.usbl_df is None:
            QtWidgets.QMessageBox.warning(self, "No Data", "No USBL data loaded.")
            return
        
        # Get output directory
        output_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
        
        try:
            import os
            from datetime import datetime as dt
            
            # Normalize the path
            output_dir = os.path.normpath(output_dir)
            
            # Ensure output_dir is a directory
            if not os.path.isdir(output_dir):
                raise ValueError(f"Selected path is not a directory: {output_dir}")
            
            # Test write permissions
            test_file = os.path.join(output_dir, ".write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except (PermissionError, IOError) as e:
                raise PermissionError(f"Cannot write to directory: {output_dir}\n\n{str(e)}")
            
            # Create filename prefix from core name + timestamp
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"{self.core_name}_{timestamp}" if self.core_name else f"export_{timestamp}"
            
            exported_files = []
            
            # Prepare USBL data with annotation columns
            usbl_export = self.usbl_df.copy()
            
            # Add boolean columns for each annotation (using sanitized names for GeoPackage)
            for ann in self.annotations:
                original_name = ann['annotation_name']
                sanitized_name = self.sanitize_field_name(original_name)
                
                # Mark TRUE for USBL points within annotation time range
                mask = (usbl_export['datetime'] >= ann['start_datetime']) & \
                       (usbl_export['datetime'] <= ann['end_datetime'])
                
                # Use sanitized name for column (GIS-compatible)
                usbl_export[sanitized_name] = mask
            
            # === CSV EXPORT ===
            if export_csv:
                # 1. Metadata CSV
                if len(self.annotations) > 0:
                    annotations_df = pd.DataFrame(self.annotations)
                    metadata_filename = f"{prefix}_metadata.csv"
                    metadata_path = os.path.normpath(os.path.join(output_dir, metadata_filename))
                    annotations_df.to_csv(metadata_path, index=False)
                    exported_files.append(f"✓ {metadata_filename} ({len(self.annotations)} annotations)")
                
                # 2. Annotated USBL CSV
                usbl_csv_filename = f"{prefix}_usbl_annotated.csv"
                usbl_csv_path = os.path.normpath(os.path.join(output_dir, usbl_csv_filename))
                usbl_export.to_csv(usbl_csv_path, index=False)
                ann_count = len(self.annotations) if self.annotations else 0
                exported_files.append(f"✓ {usbl_csv_filename} ({len(usbl_export)} points, {ann_count} annotation columns)")
            
            # === GEOPACKAGE EXPORT ===
            if export_gpkg:
                try:
                    import geopandas as gpd
                    from shapely.geometry import Point
                    
                    # Create GeoDataFrame from USBL data
                    geometry = [Point(row['easting'], row['northing']) for _, row in usbl_export.iterrows()]
                    
                    gdf = gpd.GeoDataFrame(
                        usbl_export,
                        geometry=geometry,
                        crs=self.utm_epsg if self.utm_epsg else "EPSG:32610"  # Use stored EPSG code
                    )
                    
                    # Export to GeoPackage
                    gpkg_filename = f"{prefix}.gpkg"
                    gpkg_path = os.path.normpath(os.path.join(output_dir, gpkg_filename))
                    gdf.to_file(gpkg_path, layer='usbl_points', driver='GPKG')
                    
                    ann_count = len(self.annotations) if self.annotations else 0
                    exported_files.append(f"✓ {gpkg_filename} (Point layer: {len(gdf)} points, {ann_count} annotation columns)")
                    
                except ImportError:
                    QtWidgets.QMessageBox.warning(
                        self, "GeoPackage Not Available",
                        "GeoPackage export requires 'geopandas' library.\n\n"
                        "Install with: pip install geopandas\n\n"
                        "CSV export will proceed without GeoPackage."
                    )
            
            # Success message
            files_list = "\n".join(exported_files)
            QtWidgets.QMessageBox.information(
                self, "Export Complete",
                f"Exported to: {output_dir}\n\n{files_list}"
            )
            
            self.statusBar().showMessage(f"Export complete: {len(exported_files)} file(s)")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
            
    def save_current_region(self):
        """Deprecated - replaced by save_annotation"""
        pass
            
    def export_data(self):
        """Deprecated - use export_annotated_data instead"""
        QtWidgets.QMessageBox.information(self, "Note", "Please use 'Export Annotated Data' button in the Annotations panel.")
            
    def tag_data_with_regions(self):
        """Deprecated - functionality moved to export_annotated_data"""
        pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    viewer = DredgeApp()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()