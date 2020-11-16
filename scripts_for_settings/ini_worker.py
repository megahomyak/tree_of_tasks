from configparser import ConfigParser, SectionProxy
from typing import Optional, Any, Tuple, Dict, Union

import type_converters


class INIWorker:

    def __init__(
            self, config_parser: ConfigParser,
            file_path: str, default_section: str = "DEFAULT") -> None:
        self.config_parser = config_parser
        self.file_path = file_path
        self.default_section = default_section

    def load(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = self.file_path
        self.config_parser.read(file_path)

    def load_from_string(self, string: str) -> None:
        self.config_parser.read_string(string)

    def load_from_dict(self, dict_: Dict[str, Dict[str, Any]]) -> None:
        self.config_parser.read_dict(dict_)

    def load_fields_if_not_exists(
            self, sections_with_fields: Dict[str, Dict[str, str]]) -> None:
        """
        If some field does not exist - create it with the given value.

        Args:
            sections_with_fields: dict like {section_name: {field: value}}
        """
        for section_name, section_contents in sections_with_fields.items():
            if section_name not in self.config_parser:
                self.config_parser[section_name] = {}
            for key, value in section_contents.items():
                if key not in self.config_parser[section_name]:
                    self[section_name, key] = value

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
            self, name: str, none_on_error: bool = False
            ) -> Optional[SectionProxy]:
        if none_on_error:
            try:
                return self.config_parser[name]
            except KeyError:
                return None
        return self.config_parser[name]

    def set_section(self, name: str, value: Dict[str, str]) -> None:
        self.config_parser[name] = value


class MyINIWorker(INIWorker):

    def __init__(
            self, config_parser: ConfigParser,
            file_path: str, default_section: str = "DEFAULT"):
        super(MyINIWorker, self).__init__(
            config_parser, file_path, default_section
        )

    def get_auto_showing_state(self) -> bool:
        return type_converters.str_to_bool(self["auto_showing"])
