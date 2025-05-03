"""unitary testing for the `utils_config` functions."""
from collections import namedtuple
from unittest import TestCase, mock


import utils_config


class TestCalculator(TestCase):

    def setUp(self) -> None:
        """
        Test setUp
        """
        self.test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",
            "key5": "value5"
        }

        self.test_config = namedtuple(
            "configuration",
            self.test_data.keys()
        )(*self.test_data.values())

        self.base_dir = "/path/to/file/"
        self.filename = "/config.json"
        self.test_config_file = self.base_dir + self.filename

    def test_save_config(self):
        """Test the `config_operations.save_config` function.

        See if the configuration is saved into a file.

        """

        # Execute the method from the module.
        with mock.patch(
                "utils_config.open",
                mock.mock_open(read_data=str(self.test_data).replace("'", '"'))
        ) as mock_open_file:
            utils_config.save_config(file_dir=self.test_config_file, config=self.test_config)
            mock_open_file.assert_called_once_with(self.test_config_file, "w")

    def test_serialize_config(self):
        """Test the `utils_config.serialize_config` function.

        Verifies that the returned value is the same as `namedtuple._asdict`
        method call.
        """

        # Execute the method from the module.
        obtained = utils_config.serialize_config(self.test_config)

        self.assertEqual(
            self.test_config._asdict(),
            obtained,
            msg="Expected: {}, Obtained: {}".format(self.test_config._asdict(), obtained)
        )

    @mock.patch("utils_config.os")
    def test_load_config(self, os_mocked):
        """Test the `utils_config.load_config` function in its normal operation.

        Args:
            os_mocked: os built-in module mocked.

        """

        os_mocked.path.exists.return_value = True
        # Execute the method from the module.
        with mock.patch(
                "utils_config.open",
                mock.mock_open(read_data=str(self.test_data).replace("'", '"'))
        ) as mock_open:
            obtained = utils_config.load_config(self.test_config_file)
            self.assertEqual(
                self.test_config,
                obtained,
                msg="Expected: {}, Obtained: {}".format(self.test_config.key1, obtained.key1)
            )

    @mock.patch("utils_config.os")
    def test_load_config_abnormal(self, os_mocked):
        """Test the `utils_config.load_config` function in its abnormal operation.

            Args:
                os_mocked: os built-in module mocked.

            """
        os_mocked.path.exists.return_value = False
        # Execute the method from the module.
        with self.assertRaises(ValueError):
            utils_config.load_config(self.test_config_file)

    def test_edit_config(self):
        """Test the `utils_config.edit_config` function.

        See if it works as expected calling the `namedtuple._replace` method passing
        the arguments as Keyword Arguments.
        """

        new_values = dict(key1="value2")

        # Execute the method from the module.
        obtained = utils_config.edit_config(config=self.test_config, new_values=new_values)

        self.assertNotEqual(
            self.test_config.key1,
            obtained.key1,
            msg="Expected: {}, Obtained: {}".format(self.test_config.key1, obtained.key1)
        )
