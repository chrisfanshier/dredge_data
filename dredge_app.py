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
        self.utm_zone = None
        
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
        
        self.export_annotated_btn = QtWidgets.QPushButton("Export Annotated Data")
        self.export_annotated_btn.clicked.connect(self.export_annotated_data)
        self.export_annotated_btn.setEnabled(False)
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
        """Create the time series plot widget with two stacked plots (bottom panel)"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with controls
        header = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Time Series Plots")
        label.setStyleSheet("font-weight: bold;")
        header.addWidget(label)
        
        # Add brush selection toggle button
        self.brush_mode_btn = QtWidgets.QPushButton("🖌️ Brush Selection Mode")
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
        
        # Add Save Annotation button (only enabled when brush mode active)
        self.save_annotation_btn = QtWidgets.QPushButton("💾 Save Annotation")
        self.save_annotation_btn.setEnabled(False)
        self.save_annotation_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        self.save_annotation_btn.clicked.connect(self.save_annotation)
        header.addWidget(self.save_annotation_btn)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Create shared date axis for bottom plot
        self.shared_date_axis = pg.DateAxisItem(orientation='bottom')
        
        # === PLOT 1 ===
        plot1_container = QtWidgets.QWidget()
        plot1_layout = QtWidgets.QVBoxLayout(plot1_container)
        plot1_layout.setContentsMargins(0, 5, 0, 5)
        
        # Plot 1 header
        plot1_header = QtWidgets.QHBoxLayout()
        plot1_header.addWidget(QtWidgets.QLabel("Plot 1:"))
        self.column_selector_1 = QtWidgets.QComboBox()
        self.column_selector_1.currentTextChanged.connect(lambda: self.update_timeseries_plot(1))
        plot1_header.addWidget(self.column_selector_1)
        plot1_header.addStretch()
        plot1_layout.addLayout(plot1_header)
        
        # Plot 1 widget (no bottom axis labels, will be shared)
        self.timeseries_plot_1 = pg.PlotWidget()
        self.timeseries_plot_1.setBackground('w')
        self.timeseries_plot_1.showGrid(x=True, y=True, alpha=0.3)
        self.timeseries_plot_1.getAxis('bottom').setStyle(showValues=False)  # Hide bottom labels
        
        # Enable performance features
        self.timeseries_plot_1.setClipToView(True)
        self.timeseries_plot_1.setDownsampling(auto=True, mode='peak')
        
        # Enable mouse controls
        viewbox1 = self.timeseries_plot_1.getViewBox()
        viewbox1.setMouseMode(pg.ViewBox.PanMode)
        viewbox1.setMenuEnabled(True)
        viewbox1.setAspectLocked(False)
        
        plot1_layout.addWidget(self.timeseries_plot_1)
        
        # Plot 1 curve
        self.timeseries_curve_1 = self.timeseries_plot_1.plot(
            pen=pg.mkPen('b', width=1),
            connect='finite'
        )
        
        layout.addWidget(plot1_container)
        
        # === PLOT 2 ===
        plot2_container = QtWidgets.QWidget()
        plot2_layout = QtWidgets.QVBoxLayout(plot2_container)
        plot2_layout.setContentsMargins(0, 5, 0, 0)
        
        # Plot 2 header
        plot2_header = QtWidgets.QHBoxLayout()
        plot2_header.addWidget(QtWidgets.QLabel("Plot 2:"))
        self.column_selector_2 = QtWidgets.QComboBox()
        self.column_selector_2.currentTextChanged.connect(lambda: self.update_timeseries_plot(2))
        plot2_header.addWidget(self.column_selector_2)
        plot2_header.addStretch()
        plot2_layout.addLayout(plot2_header)
        
        # Plot 2 widget with shared date axis
        self.timeseries_plot_2 = pg.PlotWidget(axisItems={'bottom': self.shared_date_axis})
        self.timeseries_plot_2.setBackground('w')
        self.timeseries_plot_2.showGrid(x=True, y=True, alpha=0.3)
        self.timeseries_plot_2.setLabel('bottom', 'Time')
        
        # Link X-axes between plots so they zoom/pan together
        self.timeseries_plot_2.setXLink(self.timeseries_plot_1)
        
        # Enable performance features
        self.timeseries_plot_2.setClipToView(True)
        self.timeseries_plot_2.setDownsampling(auto=True, mode='peak')
        
        # Enable mouse controls
        viewbox2 = self.timeseries_plot_2.getViewBox()
        viewbox2.setMouseMode(pg.ViewBox.PanMode)
        viewbox2.setMenuEnabled(True)
        viewbox2.setAspectLocked(False)
        
        plot2_layout.addWidget(self.timeseries_plot_2)
        
        # Plot 2 curve
        self.timeseries_curve_2 = self.timeseries_plot_2.plot(
            pen=pg.mkPen('r', width=1),
            connect='finite'
        )
        
        layout.addWidget(plot2_container)
        
        # Brush selection regions (one for each plot, synchronized)
        self.region_1 = pg.LinearRegionItem(
            brush=pg.mkBrush(100, 150, 255, 80),
            movable=True
        )
        self.region_1.setZValue(10)
        self.region_1.setVisible(False)
        self.timeseries_plot_1.addItem(self.region_1)
        
        self.region_2 = pg.LinearRegionItem(
            brush=pg.mkBrush(100, 150, 255, 80),
            movable=True
        )
        self.region_2.setZValue(10)
        self.region_2.setVisible(False)
        self.timeseries_plot_2.addItem(self.region_2)
        
        # Link the regions so they move together
        self.region_1.sigRegionChanged.connect(lambda: self._sync_regions(1))
        self.region_2.sigRegionChanged.connect(lambda: self._sync_regions(2))
        
        # Keep reference to "main" region for compatibility
        self.region = self.region_2
        
        # Store current X-range for keeping axis fixed when changing columns
        self.fixed_x_range = None
        
        return widget
    
    def _sync_regions(self, source):
        """Synchronize brush regions between plots"""
        if source == 1:
            # Region 1 moved, update region 2
            self.region_2.blockSignals(True)
            self.region_2.setRegion(self.region_1.getRegion())
            self.region_2.blockSignals(False)
        else:
            # Region 2 moved, update region 1
            self.region_1.blockSignals(True)
            self.region_1.setRegion(self.region_2.getRegion())
            self.region_1.blockSignals(False)
        
        # Trigger the annotation highlight update
        self.on_region_changed()
        
    def load_usbl_data(self):
        """Load USBL data from CSV file"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select USBL Data File", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
            
        try:
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
            
            # Update column selectors for both plots (exclude datetime)
            numeric_columns = [col for col in self.sensor_df.columns 
                             if col != 'datetime' and pd.api.types.is_numeric_dtype(self.sensor_df[col])]
            
            # Block signals while populating to avoid triggering updates prematurely
            self.column_selector_1.blockSignals(True)
            self.column_selector_2.blockSignals(True)
            
            self.column_selector_1.clear()
            self.column_selector_1.addItems(numeric_columns)
            self.column_selector_2.clear()
            self.column_selector_2.addItems(numeric_columns)
            
            # Set different defaults for each plot if possible
            if len(numeric_columns) >= 2:
                self.column_selector_2.setCurrentIndex(1)  # Second column in plot 2
            
            # Re-enable signals
            self.column_selector_1.blockSignals(False)
            self.column_selector_2.blockSignals(False)
            
            # Now manually trigger the initial plots
            self.update_timeseries_plot(1)
            self.update_timeseries_plot(2)
            
            # Update UI
            self.sensor_label.setText(f"✓ {len(self.sensor_df)} sensor points ({len(numeric_columns)} columns)")
            self.sensor_label.setStyleSheet("color: green;")
            
            # Plot first column
            if numeric_columns:
                self.update_timeseries_plot()
                
            self.statusBar().showMessage(f"Loaded sensor data: {len(self.sensor_df)} points")
            
            # Enable region selection
            self.save_region_btn.setEnabled(True)
            
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
        
        # Create transformer
        self.utm_zone = utm_zone
        self.utm_transformer = Transformer.from_crs(
            "EPSG:4326",  # WGS84
            f"EPSG:326{utm_zone:02d}" if hemisphere == 'north' else f"EPSG:327{utm_zone:02d}",
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
        # Also update the selected region highlight
        if self.region.isVisible():
            self.on_region_changed()
        
    def update_timeseries_plot(self, plot_num):
        """Update time series plot with selected column
        
        Args:
            plot_num: 1 or 2, indicating which plot to update
        """
        if self.sensor_df is None:
            return
            
        # Get the appropriate selector and plot objects
        if plot_num == 1:
            column = self.column_selector_1.currentText()
            plot_widget = self.timeseries_plot_1
            curve = self.timeseries_curve_1
        else:
            column = self.column_selector_2.currentText()
            plot_widget = self.timeseries_plot_2
            curve = self.timeseries_curve_2
            
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
        # Both plots share the same viewbox behavior
        viewbox1 = self.timeseries_plot_1.getViewBox()
        viewbox2 = self.timeseries_plot_2.getViewBox()
        
        if checked:
            # Enable brush selection mode on both plots
            self.brush_mode_btn.setText("🖌️ Brush Mode ON (Click drag to select)")
            viewbox1.setMouseMode(pg.ViewBox.RectMode)
            viewbox2.setMouseMode(pg.ViewBox.RectMode)
            self.save_annotation_btn.setEnabled(True)
            
            # Show region selectors if we have data
            if self.sensor_df is not None and len(self.sensor_df) > 0:
                # Initialize region to middle of current view
                x_range = viewbox2.viewRange()[0]
                center = (x_range[0] + x_range[1]) / 2
                width = (x_range[1] - x_range[0]) * 0.2
                region_range = [center - width/2, center + width/2]
                
                # Set both regions to same range
                self.region_1.setRegion(region_range)
                self.region_2.setRegion(region_range)
                
                # Show both regions
                self.region_1.setVisible(True)
                self.region_2.setVisible(True)
        else:
            # Back to pan mode on both plots
            self.brush_mode_btn.setText("🖌️ Brush Selection Mode")
            viewbox1.setMouseMode(pg.ViewBox.PanMode)
            viewbox2.setMouseMode(pg.ViewBox.PanMode)
            
            # Hide both regions
            self.region_1.setVisible(False)
            self.region_2.setVisible(False)
            self.save_annotation_btn.setEnabled(False)
            
            # Clear selection highlighting
            self.location_selection_scatter.setData([])
            self.statusBar().showMessage("Brush selection disabled")
        
    def on_region_changed(self):
        """Handle region selection change - update location plot"""
        if self.sensor_df is None or self.usbl_df is None:
            return
            
        # Get region bounds (in seconds since epoch)
        min_time, max_time = self.region.getRegion()
        
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
        
    def save_annotation(self):
        """Save the current selected region as an annotation with full metadata"""
        if self.usbl_df is None or self.sensor_df is None:
            QtWidgets.QMessageBox.warning(self, "No Data", "Please load both USBL and sensor data first.")
            return
            
        if not self.region.isVisible():
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please enable brush mode and select a region first.")
            return
        
        # Get region bounds
        min_time, max_time = self.region.getRegion()
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
                
            # Get start/end coordinates (first and last USBL points in selection)
            start_point = selected_usbl.iloc[0]
            end_point = selected_usbl.iloc[-1]
            
            # Create annotation record with full metadata
            annotation = {
                'annotation_id': self.annotation_id_counter,
                'annotation_name': name,
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
            
            # Enable export button
            self.export_annotated_btn.setEnabled(True)
            
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
            
            if len(self.annotations) == 0:
                self.export_annotated_btn.setEnabled(False)
                
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
            self.export_annotated_btn.setEnabled(False)
            self.statusBar().showMessage("All annotations cleared")
            
    def export_annotated_data(self):
        """Export both annotation metadata and USBL data with annotation columns"""
        if len(self.annotations) == 0:
            QtWidgets.QMessageBox.warning(self, "No Annotations", "Please save at least one annotation before exporting.")
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
            
            # Ensure output_dir is actually a directory
            if not os.path.isdir(output_dir):
                raise ValueError(f"Selected path is not a directory: {output_dir}")
            
            # 1. Export annotation metadata
            annotations_df = pd.DataFrame(self.annotations)
            metadata_path = os.path.join(output_dir, "annotations_metadata.csv")
            annotations_df.to_csv(metadata_path, index=False)
            
            # 2. Create USBL data with boolean annotation columns
            usbl_export = self.usbl_df.copy()
            
            # Add a boolean column for each annotation
            for ann in self.annotations:
                col_name = ann['annotation_name']
                # Mark TRUE for any USBL point within the annotation's time range
                mask = (usbl_export['datetime'] >= ann['start_datetime']) & \
                       (usbl_export['datetime'] <= ann['end_datetime'])
                usbl_export[col_name] = mask
            
            usbl_path = os.path.join(output_dir, "usbl_with_annotations.csv")
            usbl_export.to_csv(usbl_path, index=False)
            
            QtWidgets.QMessageBox.information(
                self, "Export Complete",
                f"Exported:\n\n"
                f"1. {metadata_path}\n"
                f"   ({len(self.annotations)} annotations)\n\n"
                f"2. {usbl_path}\n"
                f"   ({len(usbl_export)} USBL points with {len(self.annotations)} annotation columns)"
            )
            
            self.statusBar().showMessage(f"Exported annotated data to {output_dir}")
            
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