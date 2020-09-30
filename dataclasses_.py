from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Any


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
        return r"-?\d"

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

    def __init__(self):
        self.true_values = ("да", "yes", "д", "y", "1", "+", "истина", "true")
        self.false_values = ("нет", "no", "н", "n", "0", "-", "ложь", "false")

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
        if arg in self.true_values:
            return True
        return False


@dataclass
class Arg:

    name: str
    type: BaseArgType
    description: str


@dataclass
class Command:

    name: str
    description: str
    arguments: Tuple[Arg] = ()
