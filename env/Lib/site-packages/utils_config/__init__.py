"""
configuration operations purpose module, this is used to load configuration and
save new configuration to a file in order to reuse same configuration all over
the API and also for further implementations.
"""
import json
import os
from collections import namedtuple

CONFIG_INDENT = 2


# pylint: disable=W0212
def edit_config(config, new_values):
    """Edit values on the configuration with the new ones.

    This will return a NEW namedtuple with the changes applied to the
    `config` object based on the `new_values` dict argument.

    Args:
        config (namedtuple): Actual namedtuple configuration.
        new_values (dict): Dictionary with values to be changed.

    Returns:
        (namedtuple) New namedtuple with changes.
    """

    return config._replace(**new_values)


def load_config(file_dir):
    """Read configuration from a json file and return its content in namedtuple format.

    Args:
        file_dir (str): Full path of the file to be read.

    Returns:
        (namedtuple) configuration based on the file given.
    """

    if not os.path.exists(file_dir):
        raise ValueError("Seems like {} doesn't exists.".format(file_dir))

    with open(file_dir, 'r') as file_obj:
        file_data = file_obj.read()

    configuration = json.loads(
        file_data,
        object_hook=lambda data: namedtuple('configuration', data.keys())(*data.values())
    )

    return configuration


def save_config(file_dir, config):
    """Save configuration on file.

    Args:
        file_dir (str): Full path of the file on which to save configuration.
        config (namedtuple): Actual namedtuple configuration.

    Returns:
        None.
    """

    with open(file_dir, 'w') as file_obj:
        json.dump(config._asdict(), file_obj, indent=CONFIG_INDENT, separators=(',', ': '))


def serialize_config(config):
    """Representation of the configuration in dictionary format.

    Args:
        config (namedtuple): Actual namedtuple configuration.

    Returns:
        (dict) representation of the configuration.
    """

    return config._asdict()
