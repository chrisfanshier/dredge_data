"""
Dual Data Viewer - USBL Location and Time Series Data Visualization
Minimal Skeleton v1.0

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


class DualDataViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dual Data Viewer - USBL & Time Series")
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
        
        header.addStretch()
        layout.addLayout(header)
        
        # PyQtGraph plot widget with OpenGL for performance
        self.timeseries_plot = pg.PlotWidget()
        self.timeseries_plot.setBackground('w')
        self.timeseries_plot.showGrid(x=True, y=True, alpha=0.3)
        self.timeseries_plot.setLabel('bottom', 'Time')
        
        # Enable OpenGL for better performance with large datasets
        self.timeseries_plot.setClipToView(True)
        self.timeseries_plot.setDownsampling(auto=True, mode='peak')
        
        layout.addWidget(self.timeseries_plot)
        
        # Data curve
        self.timeseries_curve = self.timeseries_plot.plot(
            pen=pg.mkPen('b', width=1),
            connect='finite'  # Don't connect over NaN values
        )
        
        # Linear region for selection
        self.region = pg.LinearRegionItem(
            brush=pg.mkBrush(255, 0, 0, 50),
            movable=True
        )
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self.on_region_changed)
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
            
            # Parse datetime and make timezone-aware to match USBL data
            self.sensor_df['datetime'] = pd.to_datetime(self.sensor_df['datetime'], utc=True)
            
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
            
        # Plot all points
        spots = [{
            'pos': (row['easting'], row['northing']),
            'data': i
        } for i, row in self.usbl_df.iterrows()]
        
        self.location_scatter.setData(spots=spots)
        
        # Auto-range to fit data
        self.location_plot.autoRange()
        
    def update_timeseries_plot(self):
        """Update time series plot with selected column"""
        if self.sensor_df is None:
            return
            
        column = self.column_selector.currentText()
        if not column:
            return
            
        # Convert datetime to timestamp (seconds since epoch) for x-axis
        time_values = self.sensor_df['datetime'].astype(np.int64) / 1e9  # Convert to seconds
        y_values = self.sensor_df[column].values
        
        self.timeseries_curve.setData(time_values, y_values)
        
        # Update axis labels
        self.timeseries_plot.setLabel('left', column)
        
        # Set up time axis
        axis = pg.DateAxisItem(orientation='bottom')
        self.timeseries_plot.setAxisItems({'bottom': axis})
        
        # Initialize region selector to middle 20% of data
        if not self.region.isVisible():
            x_range = time_values.max() - time_values.min()
            center = time_values.min() + x_range / 2
            self.region.setRegion([center - x_range * 0.1, center + x_range * 0.1])
            self.region.setVisible(True)
            
        # Trigger initial region update
        self.on_region_changed()
        
    def on_region_changed(self):
        """Handle region selection change - update location plot"""
        if self.sensor_df is None or self.usbl_df is None:
            return
            
        # Get region bounds (in seconds since epoch)
        min_time, max_time = self.region.getRegion()
        
        # Convert back to datetime
        min_dt = pd.Timestamp(min_time, unit='s')
        max_dt = pd.Timestamp(max_time, unit='s')
        
        # Filter USBL data by time range
        mask = (self.usbl_df['datetime'] >= min_dt) & (self.usbl_df['datetime'] <= max_dt)
        selected_usbl = self.usbl_df[mask]
        
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
    
    viewer = DualDataViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
