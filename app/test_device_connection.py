import unittest
from unittest.mock import MagicMock, patch
from collections import OrderedDict
from itertools import cycle

# Import DeviceConnection from the app module
from app import DeviceConnection

class TestDeviceConnection(unittest.TestCase):

    @patch('app.serial.Serial')
    def test_read_and_parse_data_usb(self, mock_serial):
        # Mock the readline method to return the test string
        test_string = b'010000320000000000000000000000;-0.001;-0.036;0.012;23.602;0.036;1.525;0.036;1.525\r\n'
        mock_serial_instance = mock_serial.return_value
        mock_serial_instance.readline.return_value = test_string

        # Create the args object
        args = MagicMock()
        args.connection_type = 'usb'
        args.device = 'dummy_device'
        args.baud_rate = 9600

        # Instantiate the DeviceConnection
        device_connection = DeviceConnection(args)

        # Define the data names
        data_names = OrderedDict(
            [
                ("U", "sonic3d.uwind"),
                ("V", "sonic3d.vwind"),
                ("W", "sonic3d.wwind"),
                ("T", "sonic3d.temp"),
            ]
        )

        # Call the read_and_parse_data method
        parsed_data = device_connection.read_and_parse_data(data_names)

        # Assert the parsed data
        expected_data = {
            "U": -0.001,
            "V": -0.036,
            "W": 0.012,
            "T": 23.602
        }
        self.assertEqual(parsed_data, expected_data)



    @patch('app.socket.socket')
    def test_read_and_parse_data_tcp(self, mock_socket):
        # Mock the recv method to return the test string continuously
        test_string = b'010000320000000000000000000000;-0.001;-0.036;0.012;23.602;0.036;1.525;0.036;1.525\r\n'
        authentication_response = b"authentication successful"
        
        # Create a generator that will continuously return the test string
        continuous_data = cycle([test_string])

        # Ensure there are enough responses for each recv call
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.recv.side_effect = [
            b"username prompt",  # Username prompt
            b"password prompt",  # Password prompt
            authentication_response,  # Authentication response
            next(continuous_data)  # Start continuous data stream
        ] + [next(continuous_data) for _ in range(100)]  # Add more data responses to cover extended testing

        # Create the args object
        args = MagicMock()
        args.connection_type = 'tcp'
        args.ip = 'dummy_ip'
        args.port = 1234
        args.username = 'dummy_user'
        args.password = 'dummy_pass'

        # Instantiate the DeviceConnection
        device_connection = DeviceConnection(args)

        # Define the data names
        data_names = OrderedDict([
            ("U", "sonic3d.uwind"),
            ("V", "sonic3d.vwind"),
            ("W", "sonic3d.wwind"),
            ("T", "sonic3d.temp"),
        ])

        # Call the read_and_parse_data method
        parsed_data = device_connection.read_and_parse_data(data_names)

        # Assert the parsed data
        expected_data = {
            "U": -0.001,
            "V": -0.036,
            "W": 0.012,
            "T": 23.602
        }
        self.assertEqual(parsed_data, expected_data)