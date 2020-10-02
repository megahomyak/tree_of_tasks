from configparser import ConfigParser
from typing import Optional, Any, Tuple


class SettingsManager:

    def __init__(self, filepath: str) -> None:
        self.config_parser = ConfigParser()
        self.file_path = filepath

    def load(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = self.file_path
        self.config_parser.read(file_path)

    def load_from_string(self, string: str) -> None:
        self.config_parser.read_string(string)

    def load_from_dict(self, dict_: dict) -> None:
        self.config_parser.read_dict(dict_)

    def save(self, file_path: Optional[str] = None) -> None:
        """
        Saves the current state of config parser to the file with the specified
        path.

        Args:
            file_path:
                path to the file, where config parser info should be saved
        """
        if file_path is None:
            file_path = self.file_path
        with open(file_path, "w") as f:
            self.config_parser.write(f)

    def as_str(self) -> str:
        """
        Dumps the current state of config parser to the string.

        This method was written fully by me, it's not the delegation. Why I even
        have to make this? This should be implemented in the ConfigParser!
        Too bad!

        Returns:
            current state of the config parser as string
        """
        return "\n\n".join(  # Joining all the sections
            [
                "\n".join(
                    [
                        f"{section_name}",
                        *[
                            f"{key}={value}"
                            for key, value in self.config_parser[section_name]
                        ]
                    ]
                )
                for section_name in self.config_parser.sections()
            ]
        )

    def as_dict(self) -> dict:
        """
        Dumps the current state of config parser to the dict.

        This method was written by me, it's not the delegation. Why I even
        have to make this? This should be implemented in the ConfigParser!
        Too bad!

        Returns:
            current state of the config parser as dict
        """
        return dict(
            map(
                lambda section_name, section: (
                    section_name, dict(section.items())
                ),
                self.config_parser.items()
            )
        )

    def __getitem__(self, section: str, name: str) -> str:
        """
        Gets the value (as string, how else) of the specified key

        Args:
            section: name of the section, where the value is
            name: name of the value (key to value)

        Returns:
            received value (as string, because they are stored as strings...)
        """
        return self.config_parser[section][name]

    def __setitem__(self, section_and_key: Tuple[str, str], value: Any) -> None:
        """
        Sets the value with the specified name to the specified section.
        VALUE WILL BE CONVERTED TO STRING!

        Args:
            section_and_key: tuple of two strings - section name and key
            value: you know what this is. Will be converted to string
        """
        section, name = section_and_key
        self.config_parser[section][name] = str(value)
