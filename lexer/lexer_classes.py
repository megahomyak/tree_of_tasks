import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Any, Callable, Optional, Type, Dict, List

import exceptions


class BaseArgType(ABC):

    """
    Base class for arguments (aka fields) in commands from the user
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def regex(self) -> str:
        pass

    @property
    def description(self) -> Optional[str]:
        return None

    @abstractmethod
    def convert(self, arg: str) -> Any:
        """
        Converts incoming argument to the corresponding type

        Args:
            arg: str with some argument

        Returns:
            arg converted to some type
        """
        pass


@dataclass
class Arg:

    name: str
    type: BaseArgType
    description: Optional[str] = None


@dataclass
class ConstantContext:

    commands: Tuple["Command", ...]
    command_descriptions: Dict[str, List[Callable]]


class BaseMetadata(ABC):

    @staticmethod
    @abstractmethod
    def get_data_from_context(context: ConstantContext) -> Any:
        pass


@dataclass
class Command:

    names: Tuple[str, ...]
    description: str
    attached_function: Callable
    metadata_tuple: Tuple[Type[BaseMetadata], ...] = ()
    arguments: Tuple[Arg, ...] = ()

    def convert_command_to_args(
            self, command: str, separator: str = " ") -> Tuple[Any, ...]:
        rgx_result = re.fullmatch(
            pattern=separator.join(
                [
                    f"(?:{'|'.join(re.escape(name) for name in self.names)})",
                    *[
                        f"({arg.type.regex})"
                        for arg in self.arguments
                    ]  # Something like (\d\d)
                ]  # Something like (?:command) (\d\d)
            ),
            string=command
        )
        if rgx_result is None:
            raise exceptions.ParsingError
        # noinspection PyArgumentList
        # because IDK why it thinks that `arg` argument is already filled
        # (like `self`)
        return tuple(
            converter(group)
            for group, converter in zip(
                rgx_result.groups(),
                [
                    arg.type.convert
                    for arg in self.arguments
                ]
            )
        )

    def get_all_metadata_as_converted(
            self, context: ConstantContext) -> Tuple[Any]:
        return tuple(
            one_metadata.get_data_from_context(context)
            for one_metadata in self.metadata_tuple
        )

    def get_full_description(
            self, include_type_descriptions: bool = False,
            include_heading: bool = False) -> str:
        heading_str = (
            f"Описание команды '{self.names[0]}': "
            f"{self.description}"
        ) if include_heading else None
        aliases_str = (
            f"Псевдонимы: "
            f"{', '.join(self.names[1:])}"
        ) if len(self.names) > 1 else None
        args = []
        for argument in self.arguments:
            temp_desc = (
                f" - {argument.description}"
                if argument.description is not None else
                ""
            )
            temp_type_desc = (
                f" - {argument.type.description}"
                if argument.type.description is not None else
                ""
            )
            args.append(
                f"{argument.name} ({argument.type.name}"
                f"{temp_type_desc}){temp_desc}"
                if include_type_descriptions else
                f"{argument.name} ({argument.type.name}){temp_desc}"
            )
        if args:
            temp_args_str = "\n".join(args)
            args_str = f"Аргументы:\n{temp_args_str}"
            del temp_args_str
        else:
            args_str = None
        return "\n".join(
            filter(
                lambda string: string is not None,
                (heading_str, aliases_str, args_str)
            )
        )
