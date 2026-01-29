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
        
        # Current selection
        self.selected_regions = []  # List of {name, start_time, end_time}
        
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
        
        # Splitter for location and time series plots
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        
        # Location plot (top)
        self.location_plot_widget = self.create_location_plot()
        splitter.addWidget(self.location_plot_widget)
        
        # Time series plot (bottom)
        self.timeseries_plot_widget = self.create_timeseries_plot()
        splitter.addWidget(self.timeseries_plot_widget)
        
        # Set initial sizes (40% location, 60% time series)
        splitter.setSizes([360, 540])
        
        main_layout.addWidget(splitter)
        
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
        
        # Region management
        self.save_region_btn = QtWidgets.QPushButton("Save Selected Region")
        self.save_region_btn.clicked.connect(self.save_current_region)
        self.save_region_btn.setEnabled(False)
        layout.addWidget(self.save_region_btn)
        
        export_btn = QtWidgets.QPushButton("Export Data")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)
        
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
        """Create the time series plot widget (bottom panel)"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with column selector
        header = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Time Series Plot")
        label.setStyleSheet("font-weight: bold;")
        header.addWidget(label)
        
        header.addWidget(QtWidgets.QLabel("Column:"))
        self.column_selector = QtWidgets.QComboBox()
        self.column_selector.currentTextChanged.connect(self.update_timeseries_plot)
        header.addWidget(self.column_selector)
        
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
        
        header.addStretch()
        layout.addLayout(header)
        
        # PyQtGraph plot widget with OpenGL for performance
        date_axis = pg.DateAxisItem(orientation='bottom')
        self.timeseries_plot = pg.PlotWidget(axisItems={'bottom': date_axis})
        self.timeseries_plot.setBackground('w')
        self.timeseries_plot.showGrid(x=True, y=True, alpha=0.3)
        self.timeseries_plot.setLabel('bottom', 'Time')
        
        # Store reference to date axis for debugging
        self.date_axis = date_axis
        
        # Enable OpenGL for better performance with large datasets
        self.timeseries_plot.setClipToView(True)
        self.timeseries_plot.setDownsampling(auto=True, mode='peak')
        
        # Enable better mouse controls
        # - Mouse wheel zooms Y axis
        # - Ctrl+wheel zooms X axis
        # - Left drag pans
        # - Right-click menu for autoscale/zoom out
        viewbox = self.timeseries_plot.getViewBox()
        viewbox.setMouseMode(pg.ViewBox.PanMode)  # Left drag = pan
        viewbox.setMenuEnabled(True)  # Right-click menu
        
        # Allow independent X/Y scaling (not aspect-locked)
        viewbox.setAspectLocked(False)
        
        layout.addWidget(self.timeseries_plot)
        
        # Data curve
        self.timeseries_curve = self.timeseries_plot.plot(
            pen=pg.mkPen('b', width=1),
            connect='finite'  # Don't connect over NaN values
        )
        
        # Brush selection region (hidden by default)
        self.region = pg.LinearRegionItem(
            brush=pg.mkBrush(100, 150, 255, 80),  # Light blue, semi-transparent
            movable=True
        )
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self.on_region_changed)
        self.region.setVisible(False)  # Hidden until brush mode activated
        self.timeseries_plot.addItem(self.region)
        self.region.setVisible(False)  # Hidden until data is loaded
        
        return widget
        
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
            
            # Update column selector (exclude datetime)
            numeric_columns = [col for col in self.sensor_df.columns 
                             if col != 'datetime' and pd.api.types.is_numeric_dtype(self.sensor_df[col])]
            self.column_selector.clear()
            self.column_selector.addItems(numeric_columns)
            
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
        
    def update_timeseries_plot(self):
        """Update time series plot with selected column"""
        if self.sensor_df is None:
            return
            
        column = self.column_selector.currentText()
        if not column:
            return
            
        # Filter out NaN values (common with sparse data from outer merge)
        valid_mask = self.sensor_df[column].notna()
        valid_data = self.sensor_df[valid_mask].reset_index(drop=True)
        
        if len(valid_data) == 0:
            # No data to plot
            self.timeseries_curve.setData([], [])
            return
            
        # Convert datetime to timestamp (seconds since epoch) for x-axis
        time_values = valid_data['datetime'].values.astype('datetime64[s]').astype(np.float64)
        y_values = valid_data[column].values
        
        # Debug: print time range
        print(f"Plotting {column}: time range = {time_values.min():.2f} to {time_values.max():.2f}")
        print(f"  As datetime: {pd.Timestamp(time_values.min(), unit='s')} to {pd.Timestamp(time_values.max(), unit='s')}")
        
        self.timeseries_curve.setData(time_values, y_values)
        
        # Update axis labels
        self.timeseries_plot.setLabel('left', column)
        
    def toggle_brush_mode(self, checked):
        """Toggle between pan mode and brush selection mode"""
        viewbox = self.timeseries_plot.getViewBox()
        
        if checked:
            # Enable brush selection mode
            self.brush_mode_btn.setText("🖌️ Brush Mode ON (Click drag to select)")
            viewbox.setMouseMode(pg.ViewBox.RectMode)  # Rectangle selection mode
            
            # Show region selector if we have data
            if self.sensor_df is not None and len(self.sensor_df) > 0:
                # Initialize region to middle of current view
                x_range = viewbox.viewRange()[0]
                center = (x_range[0] + x_range[1]) / 2
                width = (x_range[1] - x_range[0]) * 0.2
                self.region.setRegion([center - width/2, center + width/2])
                self.region.setVisible(True)
        else:
            # Back to pan mode
            self.brush_mode_btn.setText("🖌️ Brush Selection Mode")
            viewbox.setMouseMode(pg.ViewBox.PanMode)
            self.region.setVisible(False)
            
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
        
    def save_current_region(self):
        """Save the current selected region with a name"""
        min_time, max_time = self.region.getRegion()
        min_dt = pd.Timestamp(min_time, unit='s')
        max_dt = pd.Timestamp(max_time, unit='s')
        
        # Prompt for region name
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Region", "Enter region name:"
        )
        
        if ok and name:
            region_info = {
                'name': name,
                'start_time': min_dt,
                'end_time': max_dt
            }
            self.selected_regions.append(region_info)
            
            QtWidgets.QMessageBox.information(
                self, "Region Saved",
                f"Region '{name}' saved:\n{min_dt} to {max_dt}"
            )
            
    def export_data(self):
        """Export data with tagged regions"""
        if not self.selected_regions:
            QtWidgets.QMessageBox.warning(
                self, "No Regions",
                "No regions have been saved. Please select and save regions first."
            )
            return
            
        # Choose export directory
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Export Directory"
        )
        
        if not directory:
            return
            
        try:
            # Tag data with regions
            self.tag_data_with_regions()
            
            # Export USBL data as CSV
            usbl_output = f"{directory}/usbl_tagged.csv"
            self.usbl_df.to_csv(usbl_output, index=False)
            
            # Export sensor data as CSV
            sensor_output = f"{directory}/sensor_tagged.csv"
            self.sensor_df.to_csv(sensor_output, index=False)
            
            QtWidgets.QMessageBox.information(
                self, "Export Complete",
                f"Data exported to:\n{usbl_output}\n{sensor_output}\n\n"
                "Shapefile export will be implemented in next iteration."
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", str(e))
            
    def tag_data_with_regions(self):
        """Add region tags as columns to dataframes"""
        # Add a column for each saved region
        for region in self.selected_regions:
            col_name = f"region_{region['name']}"
            
            # Tag USBL data
            if self.usbl_df is not None:
                mask = (self.usbl_df['datetime'] >= region['start_time']) & \
                       (self.usbl_df['datetime'] <= region['end_time'])
                self.usbl_df[col_name] = mask
                
            # Tag sensor data
            if self.sensor_df is not None:
                mask = (self.sensor_df['datetime'] >= region['start_time']) & \
                       (self.sensor_df['datetime'] <= region['end_time'])
                self.sensor_df[col_name] = mask


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    viewer = DredgeApp()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
