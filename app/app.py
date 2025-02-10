import serial
import socket
from argparse import ArgumentParser
import logging
from collections import OrderedDict
import sys
import time
from waggle.plugin import Plugin, get_timestamp
import os

# Configure logging for the script
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Timeout duration in seconds
TIMEOUT_SECONDS = 300

class DeviceConnection:
    def __init__(self, args):
        self.connection_type = args.connection_type
        self.buffer = b""  # Initialize buffer for storing received byte strings

        # Establish connection based on the type specified
        if self.connection_type == "usb":
            # Set up USB-Serial connection
            self.connection = serial.Serial(
                args.device,
                baudrate=args.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            logging.info("Connected to USB-Serial device.")
        elif self.connection_type == "tcp":
            # Set up TCP connection
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((args.ip, args.port))
            
            # Authenticate with the TCP device
            response = self.connection.recv(4096).decode("utf-8")
            self.connection.sendall(f"{args.username}\r\n".encode())
            response = self.connection.recv(4096).decode("utf-8")
            self.connection.sendall(f"{args.password}\r\n".encode())
            
            response = self.connection.recv(4096).decode("utf-8")
            if "authentication successful" not in response.lower():
                raise Exception("Authentication failed.")
                
            logging.info("Connected to TCP device.")
        else:
            raise ValueError("Unsupported connection type.")
    
    def read_and_parse_data(self, data_names):
        try:
            # Read data based on connection type
            if self.connection_type == "usb":
                # Read and parse line from USB-Serial connection
                line = self.connection.readline().decode("utf8").rstrip().split(";")[1:5]
            elif self.connection_type == "tcp":
                # Ensure the buffer has a complete line
                while b"\r\n" not in self.buffer:
                    self.buffer += self.connection.recv(4096)
                # Extract the first complete line from the buffer
                line, self.buffer = self.buffer.split(b"\r\n", 1)
                line = line.decode("utf-8").rstrip().split(";")[1:5]
            else:
                raise ValueError("Unsupported connection type.")
            
            # Check for valid data line
            if not line or len(line) < len(data_names):
                logging.warning("Empty or incomplete data line received.")
                raise ValueError("Empty or incomplete data line.")
            
            # Map the parsed values to their respective keys
            keys = data_names.keys()
            values = [float(value) for value in line]
            data_dict = dict(zip(keys, values))
            return data_dict
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            raise

def publish_data(plugin, data, data_names, meta, additional_meta=None):
    timestamp = get_timestamp()

    if not data:
        logging.warning("No data to publish.")
        plugin.publish("status", "NoData", meta={"timestamp": timestamp})
        return

    # Publish each data item with its metadata
    for key, value in data.items():
        if key in data_names:
            try:
                # Prepare metadata for publishing
                meta_data = {
                    "missing": "-9999.0",
                    "units": meta["units"][data_names[key]],
                    "description": meta["description"][data_names[key]],
                    "name": data_names[key],
                    "sensor": meta["sensor"],
                }
                if additional_meta:
                    meta_data.update(additional_meta)

                plugin.publish(
                    data_names[key], value, meta=meta_data, timestamp=timestamp
                )
            except KeyError as e:
                plugin.publish('status', f'{e}')
                print(f"Error: Missing key in meta data - {e}")

def run_device_interface(args, data_names, meta):
    with Plugin() as plugin:
        device_connection = DeviceConnection(args)
        while True:
            time.sleep(2)  # Introduce delay between data readings
            while True:
                try:
                    # Read and publish data continuously
                    data = device_connection.read_and_parse_data(data_names)
                    if args.debug:
                        print(data)
                    publish_data(plugin, data, data_names, meta)
                except Exception as e:
                    logging.error(f"Error: {e} while reading data.")
                    plugin.publish('status', f'{e}')
                    continue

if __name__ == "__main__":
    # Set up argument parser for command line arguments
    arg_parser = ArgumentParser(description="Universal Device Interface")
    arg_parser.add_argument("--connection_type", type=str, choices=["usb", "tcp"], required=True, help="Type of connection (usb-serial or tcp)")
    arg_parser.add_argument("--device", type=str, default='NA', help="Device to read for USB-Serial")
    arg_parser.add_argument("--baud_rate", type=int, default=-999, help="Baud rate for the USB-Serial device")
    arg_parser.add_argument('--ip', type=str, default='10.31.81.9999', help='Device IP address for TCP')
    arg_parser.add_argument('--port', type=int, default=5001, help='TCP connection port (default: 5001)')
    arg_parser.add_argument('--username', type=str, default="data", help='Username for TCP connection')
    arg_parser.add_argument('--password', type=str, default="METEKGMBH", help='Password for TCP connection')
    arg_parser.add_argument('--debug', action="store_true", help="Run script in debug mode")
    args = arg_parser.parse_args()

    # Define data names and metadata for the sonic sensor
    sonic_data_names = OrderedDict(
        [
            ("U", "sonic3d.uwind"),
            ("V", "sonic3d.vwind"),
            ("W", "sonic3d.wwind"),
            ("T", "sonic3d.temp"),
        ]
    )
    sonic_meta = {
        "connection": args.connection_type,
        "sensor": "METEK-sonic3D",
        "units": {
            "sonic3d.uwind": "m/s",
            "sonic3d.vwind": "m/s",
            "sonic3d.wwind": "m/s",
            "sonic3d.temp": "degrees Celsius",
        },
        "description": {
            "sonic3d.uwind": "zonal wind",
            "sonic3d.vwind": "meridional wind",
            "sonic3d.wwind": "vertical wind",
            "sonic3d.temp": "Ambient Temperature",
        },
    }

    try:
        run_device_interface(args, sonic_data_names, sonic_meta)
    except Exception as e:
        logging.error(f"Error running device interface: {e}")
