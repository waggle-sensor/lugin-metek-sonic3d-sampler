# Plugin for METEK Sonic3D

# METEK Sonic3D
The METEK Sonic3D is an advanced sonic anemometer designed to provide accurate measurements of three-dimensional wind vectors and sonic temperature. It is widely used in meteorological research and environmental monitoring to study turbulent airflows and atmospheric boundary layer processes.

## Usage in Meteorological Measurements
The METEK Sonic3D anemometer is used to measure the three components of wind velocity (U, V, W) and temperature in the atmosphere. This information is crucial for understanding the dynamics of atmospheric turbulence, energy exchange, and pollutant dispersion. The high-frequency data collected by the Sonic3D allows for detailed analysis of turbulent eddies and their impact on atmospheric processes.

## Waggle Plugin for METEK Sonic3D via TCP
The plugin collects data from the METEK Sonic3D anemometer over USB-Serial or TCP/IP networks. It enables the reading, parsing, and publishing of the data to the Waggle beehive for further analysis and storage. The plugin connects to the METEK device using its IP address and port number. It then listens for data transmitted over the network. Incoming data from the Sonic3D is parsed, extracting wind components and temperature. Parsed data is published with appropriate metadata.

### Example Command

```bash
python3 /app/app.py --connection_type tcp --ip 192.168.1.100 --port 5001 --username data --password METEKGMBH --debug
```

```bash
python3 /app/app.py --connection_type usb --device /dev/ttyUSB0 --baud_rate 9600 --debug
```


* --connection_type: Type of connection, which should be set to tcp or usb.
* --ip: IP address of the METEK Sonic3D device.
* --port: Port number for TCP/IP connection (default: 5001).
* --device: Device path for USB-Serial connection.
* --baud_rate: Baud rate for the USB-Serial connection.
* --username: Username for TCP connection (default: data).
* --password: Password for TCP connection (default: METEKGMBH).
* --debug: Flag to enable debug mode for additional logging.

Parameters:

    U: Zonal wind component (m/s).
    V: Meridional wind component (m/s).
    W: Vertical wind component (m/s).
    T: Sonic temperature (degrees Celsius).

The plugin allows continuous data collection, retries connections if they fail, and publishes the data to the Waggle network for real-time analysis and archiving.