import serial
from argparse import ArgumentParser
import logging
from collections import OrderedDict
import sys
import time
from waggle.plugin import Plugin  # , get_timestamp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_device(device, baud_rate):
    """
    Establishes a serial connection to a device.

    :param device: The device path (e.g., '/dev/ttyUSB0').
    :param baud_rate: The baud rate for the serial connection.
    :return: A serial connection object.
    """
    try:
        serial_connection = serial.Serial(
            device,
            baudrate=baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
    except serial.SerialException as e:
        logging.error(f"Error connecting to device: {e}")
        raise
    return serial_connection


def publish_data(plugin, data, data_names, meta, additional_meta=None):
    """
    Publishes data to the plugin.

    :param plugin: Plugin object for publishing data.
    :param data: Dictionary of data to be published.
    :param data_names: Mapping of data keys to their publishing names.
    :param meta: Metadata associated with the data.
    :param additional_meta: Additional metadata to be included.
    """
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
                plugin.publish(data_names[key], value, meta=meta_data)
            except KeyError as e:
                print(f"Error: Missing key in meta data - {e}")


def run_device_interface(device, baud_rate, data_names, meta, debug=False):
    """
    Runs the device interface for reading and publishing data.

    :param device: The device path (e.g., '/dev/ttyUSB0').
    :param baud_rate: The baud rate for the serial connection.
    :param data_names: Mapping of data keys to their publishing names.
    :param meta: Metadata associated with the data.
    :param debug: Boolean flag to enable debug mode.
    """

    with Plugin() as plugin:
        serial_connection = connect_to_device(device, baud_rate)
        time.sleep(2)

        while True:
            try:
                data = read_and_parse_data(serial_connection, data_names)
                if debug:
                    print(data)
                publish_data(plugin, data, data_names, meta)
            except serial.SerialException as e:
                    logging.error(f"Serial error: {e} while reading data.")
            except ValueError as e:
                    logging.error(f"Value error: {e}")
            except KeyboardInterrupt:
                    logging.info("Key Interrupt received, shutting down.")
                    break
            except Exception as e:
                    logging.error(f"Unexpected error: {e}")
                    break

        if serial_connection and not serial_connection.closed:
            serial_connection.close()


def read_and_parse_data(serial_connection, data_names):
    """
    Reads and parses data from the serial connection. Assumes "\r" linebreak.

    :param serial_connection: The serial connection object.
    :return: A dictionary of parsed data.
    """
    try:
        line = serial_connection.read_until(b"\r").decode("utf-8").rstrip().split()
        keys = data_names.keys()
        values = [float(value) for value in line]
        data_dict = dict(zip(keys, values))
        return data_dict
    except serial.SerialException as e:
        logging.error(f"Serial error: {e}")
        raise
    except ValueError as e:
        logging.error(f"Value error: {e}")
        raise


if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Universal Serial Device Interface")
    arg_parser.add_argument("--device", type=str, help="Device to read", required=True)
    arg_parser.add_argument(
        "--baud_rate", type=int, help="Baud rate for the device", required=True
    )
    arg_parser.add_argument(
        "--debug", action="store_true", help="Run script in debug mode"
    )
    args = arg_parser.parse_args()

    # The `key` order should be same as the order of variables in the data stream.
    sonic_data_names = OrderedDict(
        [
            ("U", "sonic3d.uwind"),
            ("V", "sonic3d.vwind"),
            ("W", "sonic3d.wwind"),
            ("T", "sonic3d.temp"),
        ]
    )
    sonic_meta = {
        "sensor": "RMYong-sonic3D",
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
        run_device_interface(
            args.device, args.baud_rate, sonic_data_names, sonic_meta, debug=args.debug
        )
    except Exception as e:
        logging.error(f"Error running device interface: {e}")
