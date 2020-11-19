import os
from configparser import ConfigParser, SectionProxy
from typing import Optional, Any, Tuple, Dict, Union

from config import type_converters


class INIWorker:

    def __init__(
            self, config_parser: ConfigParser,
            file_path: str, default_section: str = "DEFAULT"):
        self.config_parser = config_parser
        self.file_path = file_path
        self.default_section = default_section

    def load(
            self, file_path: Optional[str] = None,
            default_contents: Optional[str] = None) -> None:
        """
        Loads config from file. Can create a file if it not exists and
        default_contents is specified.

        Args:
            file_path: path to .ini file with config
            default_contents:
                if specified and file isn't found - creates a file with that
                contents
        """
        if file_path is None:
            file_path = self.file_path
        try:
            with open(file_path, "r") as f:
                self.config_parser.read_file(f)
        except FileNotFoundError:
            if default_contents is not None:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                self.load_from_string(default_contents)
                with open(file_path, "w") as f:
                    f.write(default_contents)
            else:
                raise

    def load_from_string(self, string: str) -> None:
        self.config_parser.read_string(string)

    def load_from_dict(self, dict_: Dict[str, Dict[str, Any]]) -> None:
        self.config_parser.read_dict(dict_)

    def save(self, file_path: Optional[str] = None) -> None:
        """
        Saves the current state of config parser to the file with the specified
        path.

        Args:
            file_path:
                path to the file, where config parser info should be saved
        """
        with open(self.file_path if file_path is None else file_path, "w") as f:
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
        return "\n\n".join([  # Joining all sections
            "\n".join([  # Joining one section
                f"{section_name}",
                *[
                    f"{key}={value}"
                    for key, value in self.config_parser[section_name]
                ]
            ]) for section_name in self.config_parser.sections()
        ])

    def as_dict(self) -> dict:
        """
        Dumps the current state of config parser to the dict.

        This method was written by me, it's not the delegation. Why I even
        have to make this? This should be implemented in the ConfigParser!
        Too bad!

        Returns:
            current state of the config parser as dict
        """
        return dict(map(
            lambda section_name, section: (section_name, dict(section.items())),
            self.config_parser.items()
        ))

    def __getitem__(self, section_and_key: Union[Tuple[str, str], str]) -> str:
        """
        Gets the value of the specified key.
        VALUES AND SECTION NAMES IS STORED AS STRINGS ONLY!

        Args:
            section_and_key:
                tuple of two strings - section name and key
                OR
                key, then section is self.default_section

        Returns:
            received value (as string, because they are stored as strings...)
        """
        if isinstance(section_and_key, str):
            section = self.default_section
            name = section_and_key
        else:
            section, name = section_and_key
        return self.config_parser[section][name]

    def __setitem__(
            self, section_and_key: Union[Tuple[str, str], str],
            value: Any) -> None:
        """
        Sets the value with the specified name to the specified section.
        VALUE WILL BE CONVERTED TO STRING!

        Args:
            section_and_key:
                tuple of two strings - section name and key
                OR
                key, then section is self.default_section
            value: you know what this is. Will be converted to string
        """
        if isinstance(section_and_key, str):
            section = self.default_section
            name = section_and_key
        else:
            section, name = section_and_key
        self.config_parser[section][name] = str(value)

    def get_section(
            self, name: str,
            none_on_error: bool = False) -> Optional[SectionProxy]:
        if none_on_error:
            try:
                return self.config_parser[name]
            except KeyError:
                return None
        return self.config_parser[name]

    def set_section(self, name: str, value: Dict[str, str]) -> None:
        self.config_parser[name] = value


class MyINIWorker(INIWorker):

    def get_auto_showing_state(self) -> bool:
        return type_converters.str_to_bool(self["auto_showing"])
