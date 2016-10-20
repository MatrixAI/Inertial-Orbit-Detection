import numpy as np

def create_accel_convert(accel_unit_max, volt_max, volt_base, volt_per_g, g_units):

    def accel_convert(accel_units):

        """Converts acceleration units from the controller devices to acceleration meters per second squared."""
        accel_volts = accel_units / (accel_unit_max / volt_max)
        accel = ((accel_volts - volt_base) / volt_per_g) * g_units
        return accel

    return accel_convert

accel_sensors = {
    # from: www.freetronics.com.au/pages/am3x-quickstart-guide
    "am3x-1.5g": {
        "g_units": 9.80665,
        "volt_base": 1.65,
        "volt_max": 5,
        "volt_per_g": 0.8,
        "accel_unit_max": 1023
    },
    # from: www.freetronics.com.au/pages/am3x-quickstart-guide
    "am3x-6g": {
        "g_units": 9.80665,
        "volt_base": 1.65,
        "volt_max": 5,
        "volt_per_g": 0.206,
        "accel_unit_max": 1023
    }
}

for device in accel_sensors:

    accel_sensors[device]["accel_convert"] = create_accel_convert(
        accel_sensors[device]["accel_unit_max"], 
        accel_sensors[device]["volt_max"],
        accel_sensors[device]["volt_base"],
        accel_sensors[device]["volt_per_g"],
        accel_sensors[device]["g_units"]
    )
    accel_sensors[device]["accel_convert_map_np"] = np.vectorize(accel_sensors[device]["accel_convert"])
    accel_sensors[device]["accel_max"] = accel_sensors[device]["accel_convert"](accel_sensors[device]["accel_unit_max"])
