# RMYong Sonic 3D Anemometer Sampler
Waggle Plugin for the R.M. Young Model 81000 Ultrasonic Anemometer.

# Science
The R.M. Young Model 81000 measures 3D wind velocity and sonic temperature, providing accurate atmospheric observations. This data is crucial for analyzing wind patterns, atmospheric fluxes, eddie covariance measurement, air quality, and meteorological research.

In combination with additional sensors on a CROCUS Level 1 Node, the RMYong Sonic 3D Anemometer enables comprehensive environmental monitoring.

# Usage
**Determine Serial Port**
Use PySerial to list all active serial ports. To identify the port for the RMYong Sonic 3D, run:

```bash
python -m serial.tools.list_ports
```
Alternatively, check `ls /tty/devUSB*` for active ports.

Default serial settings for the RMYong Sonic 3D Anemometer are:
1. Baud Rate = 38400
2. Data Bits = 8
3. Parity = None
4. Stop Bits = 1

## Data Sample
A sample ASCII formatted data string from the anemometer:

```bash
b'U=5.2,V=-3.1,W=0.7,T=22.3\r'
```

## Deployment

Similar to other plugins, a Docker container can be set up using a Makefile:

1. Build the Container
```bash
make build
```

2. Deploy the Container in Background
```bash
make deploy
```

3. Test the plugin
```bash
make run
```

# Access the data
```py
import sage_data_client

df = sage_data_client.query(start="2024-01-01T12:00:00Z",
                            end="2024-01-01T15:00:02Z",
                            filter={
                                "plugin": "<plugin name>",
                                "vsn": "<w03x>",
                                "sensor": "rmyong-sonic3d"
                            }
)
```

<!--- For detailed examples, check [CROCUS Instrument Cookbooks](https://crocus-urban.github.io/instrument-cookbooks/notebooks/crocus_level1_node/sonic3d.html). --->
