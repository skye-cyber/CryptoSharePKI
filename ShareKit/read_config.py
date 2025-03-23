import configparser
import os
from pathlib import Path


# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
conf_path = os.path.join(os.path.relpath(
    Path(__file__).parent), "sharekit-conf.ini")
config.read(conf_path)


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


def _set_section_(section: str = "ShareKit"):
    # --------------Set default section to section--------------
    get_value = set_default_section(config, section)

    return get_value
