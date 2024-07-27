import serial
import socket
from argparse import ArgumentParser
import logging
from collections import OrderedDict
import sys
import time
from waggle.plugin import Plugin, get_timestamp
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

TIMEOUT_SECONDS = 300

class DeviceConnection:
    def __init__(self, args):
        self.connection_type = args.connection_type
        self.buffer = b"" # buffer for byte string

        if self.connection_type == "usb":
            self.connection = serial.Serial(
                args.device,
                baudrate=args.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            logging.info("Connected to USB-Serial device.")
        elif self.connection_type == "tcp":
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((args.ip, args.port))
            
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
            if self.connection_type == "usb":
                line = self.connection.readline().decode("utf8").rstrip().split(";")[1:5]
            elif self.connection_type == "tcp":
                # when buffer is enmpty
                while b"\r\n" not in self.buffer:
                    self.buffer += self.connection.recv(4096)
                # get the first line
                line, self.buffer = self.buffer.split(b"\r\n", 1)
                line = line.decode("utf-8").rstrip().split(";")[1:5]
            else:
                raise ValueError("Unsupported connection type.")
            
            if not line or len(line) < len(data_names):
                logging.warning("Empty or incomplete data line received.")
                raise ValueError("Empty or incomplete data line.")
            
            keys = data_names.keys()
            values = [float(value) for value in line]
            data_dict = dict(zip(keys, values))
            return data_dict
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            raise

def publish_data(plugin, data, data_names, meta, additional_meta=None):
    if not data:
        logging.warning("No data to publish.")
        plugin.publish("status", "NoData", meta={"timestamp": get_timestamp()})
        return

    for key, value in data.items():
        if key in data_names:
            try:
                meta_data = {
                    "missing": "-9999.0",
                    "units": meta["units"][data_names[key]],
                    "description": meta["description"][data_names[key]],
                    "name": data_names[key],
                    "sensor": meta["sensor"],
                }
                if additional_meta:
                    meta_data.update(additional_meta)

                timestamp = get_timestamp()
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
            time.sleep(2)
            while True:
                try:
                    data = device_connection.read_and_parse_data(data_names)
                    if args.debug:
                        print(data)
                    publish_data(plugin, data, data_names, meta)
                except Exception as e:
                    logging.error(f"Error: {e} while reading data.")
                    plugin.publish('status', f'{e}')
                    continue
            #if device_connection.connection and not device_connection.connection.closed:
            #    device_connection.connection.close()
            #logging.info("Attempting to reconnect in 30 seconds...")
            #time.sleep(30)

if __name__ == "__main__":
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
