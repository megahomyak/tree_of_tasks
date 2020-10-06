import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Any, Callable, Union, Optional, Type

import exceptions
from orm.db_apis import TasksManager
from scripts_for_settings.ini_worker import MyINIWorker


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


class SequenceArgType(BaseArgType):

    @property
    def name(self) -> str:
        return f"последовательность <{self.element_type.name}>"

    @property
    def regex(self) -> str:
        return (
            f"{self.element_type.regex}"
            f"(?:{self.separator}{self.element_type.regex})*"
        )

    @property
    def description(self) -> str:
        return (
            f"От 1 до бесконечности элементов типа '{self.element_type.name}', "
            f"разделенных через '{self.separator}'"
        )

    def __init__(
            self, element_type: BaseArgType, separator: str = ",") -> None:
        self.element_type = element_type
        self.separator = separator

    def convert(self, arg: str) -> Tuple[Any]:
        return tuple(
            self.element_type.convert(element)
            for element in arg.split(self.separator)
        )


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

    def __init__(self, is_signed: bool = True) -> None:
        self.is_signed = is_signed

    def convert(self, arg: str) -> int:
        return int(arg)


class OptionalIntArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.is_signed:
            return "целое необязательное число"
        return r"неотрицательное целое необязательное число"

    @property
    def description(self) -> str:
        return (
            "число, вместо которого можно написать -, тогда при приведении "
            "строки к числу с помощью метода convert вернется None"
        )

    @property
    def regex(self) -> str:
        if self.is_signed:
            # There's a T-like ligature instead of |-,
            # it doesn't looks as intended... :(
            # But I like ligatures, I don't want to turn them off
            return r"(?:-?\d+|-)"
        return r"(?:\d+|-)"

    def __init__(self, is_signed: bool = True) -> None:
        self.is_signed = is_signed

    def convert(self, arg: str) -> Union[None, int]:
        return int(arg) if arg != "-" else None


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

    def __init__(self, length_limit: int = None) -> None:
        self.length_limit = length_limit

    def convert(self, arg: str) -> str:
        return arg


class BoolArgType(BaseArgType):

    def __init__(
            self,
            true_values: Tuple[str, ...] = (
                "да", "yes", "д", "y", "1", "+", "истина", "true", "False",
                "on", "вкл", "включено", "правда", "V", "v"
            ),
            false_values: Tuple[str, ...] = (
                "нет", "no", "н", "n", "0", "-", "ложь", "false", "True",
                "off", "выкл", "выключено", "X", "x", "х"
            )
    ) -> None:
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
        return "|".join(
            [
                re.escape(value)
                for value in self.true_values + self.false_values
            ]
        )

    def convert(self, arg: str) -> bool:
        if arg.lower() in self.true_values:
            return True
        return False


@dataclass
class Arg:

    name: str
    type: BaseArgType
    description: Optional[str] = None


@dataclass
class Context:

    tasks_manager: TasksManager
    ini_worker: MyINIWorker
    commands: Tuple["Command", ...]


class BaseMetadata(ABC):

    @staticmethod
    @abstractmethod
    def get_data_from_context(context: Context) -> Any:
        pass


class TasksManagerMetadata(BaseMetadata):

    @staticmethod
    def get_data_from_context(context: Context) -> Any:
        return context.tasks_manager


class CommandsMetadata(BaseMetadata):

    @staticmethod
    def get_data_from_context(context: Context) -> Any:
        return context.commands


class INIWorkerMetadata(BaseMetadata):

    @staticmethod
    def get_data_from_context(context: Context) -> Any:
        return context.ini_worker


class RootTasksMetadata(BaseMetadata):

    @staticmethod
    def get_data_from_context(context: Context) -> Any:
        return context.tasks_manager.get_root_tasks()


@dataclass
class Command:

    names: Tuple[str, ...]
    description: str
    attached_function: Callable
    arguments: Tuple[Arg, ...] = ()
    metadata_tuple: Tuple[Type[BaseMetadata], ...] = ()

    def convert_command_to_args(self, command: str) -> Tuple[Any, ...]:
        rgx_result = re.fullmatch(
            pattern=" ".join(
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

    def get_all_metadata_as_converted(self, context: Context) -> Tuple[Any]:
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
