import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Any, Callable

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
    def description(self) -> str:
        return "<описание отсутствует>"

    @abstractmethod
    def convert(self, arg: str) -> Any:
        """
        Checks if some value corresponds to the argument type described by class

        Returns:
            bool - check passed or not
        """
        pass


class IntArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.is_signed:
            return "целое число"
        return "неотрицательное целое число"

    @property
    def regex(self) -> str:
        if self.is_signed:
            return r"-?\d+"
        return r"\d+"

    def __init__(self, is_signed: bool = True):
        self.is_signed = is_signed

    def convert(self, arg: str) -> int:
        return int(arg)


class StringArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.length_limit is None:
            return "строка"
        return f"строка с лимитом {self.length_limit}"

    @property
    def regex(self) -> str:
        if self.length_limit is None:
            return r".+?"
        return fr"(?:.+?){{1,{self.length_limit}}}"

    def __init__(self, length_limit: int = None):
        self.length_limit = length_limit

    def convert(self, arg: str) -> str:
        return arg


class BoolArgType(BaseArgType):

    def __init__(
            self,
            true_values: Tuple[str, ...] = (
                "да", "yes", "д", "y", "1", "+", "истина", "true"
            ),
            false_values: Tuple[str, ...] = (
                "нет", "no", "н", "n", "0", "-", "ложь", "false"
            )
    ):
        self.true_values = true_values
        self.false_values = false_values

    @property
    def name(self) -> str:
        return "логическое значение (boolean)"

    @property
    def description(self) -> str:
        return (
            f"Истина: {', '.join(self.true_values)}; "
            f"ложь: {', '.join(self.false_values)}"
        )

    @property
    def regex(self) -> str:
        return "|".join(self.true_values + self.false_values)

    def convert(self, arg: str) -> Any:
        if arg.lower() in self.true_values:
            return True
        return False


@dataclass
class Arg:

    name: str
    type: BaseArgType
    description: str


@dataclass
class Command:

    names: Tuple[str, ...]
    description: str
    attached_function: Callable
    arguments: Tuple[Arg, ...] = ()

    def convert_command_to_args(self, command: str) -> Tuple[Any, ...]:
        rgx_result = re.fullmatch(
            pattern=" ".join(
                [
                    f"(?:{'|'.join(self.names)})",
                    *[
                        f"({arg.type.regex})"
                        for arg in self.arguments
                    ]
                ]  # Something like (\d\d)
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

    def get_full_description(
            self, include_type_descriptions: bool = False,
            include_heading: bool = False) -> str:
        if include_type_descriptions:
            args_description = "\n".join(
                f"{argument.name}"
                f" ({argument.type.name} - {argument.type.description})"
                f" - {argument.description}"
                for argument in self.arguments
            )
        else:
            args_description = "\n".join(
                f"{argument.name} ({argument.type.name})"
                f" - {argument.description}"
                for argument in self.arguments
            )
        if include_heading:
            if len(self.names) > 1:
                return (
                    f"Описание команды {self.names[0]}:\n"
                    f"{self.description}\n\n"
                    f"Псевдонимы:\n{''.join(self.names[1:])}\n\n"
                    "Аргументы:\n"
                    f"{args_description}"
                )
            else:
                return (
                    f"Описание команды {self.names[0]}:\n"
                    f"{self.description}\n\n"
                    "Аргументы:\n"
                    f"{args_description}"
                )
        return args_description
