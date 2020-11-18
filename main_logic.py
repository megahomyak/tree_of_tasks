import functools
from configparser import ConfigParser
from typing import NoReturn, Dict, List, Callable

from handlers.handler_helpers import BooleanTaskFields, HandlingResult
from handlers.handlers import Handlers
from ini_worker import MyINIWorker
from lexer import (
    arg_implementations, constant_metadata_implementations, lexer_classes,
    exceptions
)
from orm import db_apis


class MainLogic:

    # noinspection PyShadowingNames
    # Because I don't care, it's the same object
    def __init__(
            self, ini_worker: MyINIWorker, handlers: Handlers) -> None:
        ini_worker.load(default_contents=(
            "[DEFAULT]\n"
            "auto_showing = True"
        ))
        self.ini_worker = ini_worker
        self.handlers = handlers
        if self.ini_worker.get_auto_showing_state():
            print(self.handlers.get_tasks_as_string().message)
        self.commands = (
            lexer_classes.Command(
                names=("автопоказ", "autoshowing"),
                description=(
                    "включает/выключает показ дерева задач после каждого "
                    "изменения"
                ),
                handler=handlers.change_auto_showing,
                arguments=(lexer_classes.Arg(
                    "состояние настройки",
                    arg_implementations.BoolArgType()
                ),)
            ),
            lexer_classes.Command(
                names=("помощь", "команды", "help", "commands"),
                description="показывает список команд",
                handler=handlers.get_help_message,
                constant_metadata=(
                    constant_metadata_implementations.CommandsConstantMetadata,
                )
            ),
            lexer_classes.Command(
                names=("помощь", "команды", "help", "commands"),
                description="показывает помощь по конкретным командам",
                handler=handlers.get_help_message_for_specific_commands,
                constant_metadata=((
                    constant_metadata_implementations
                    .CommandDescriptionsConstantMetadata,
                )),
                arguments=(lexer_classes.Arg(
                    "названия команд",
                    arg_implementations.SequenceArgType(
                        arg_implementations.StringArgType()
                    ), (
                        "названия команд должны быть через запятую; название "
                        "только одной команды тоже можно написать; в качестве "
                        "имени команды можно использовать еще и любой "
                        "псевдоним этой команды"
                    )
                ),)
            ),
            lexer_classes.Command(
                names=("добавить", "add", "+"),
                description=(
                    "добавляет задачу с указанным "
                    "родителем (необязательно) и текстом"
                ),
                handler=handlers.add_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID родителя",
                        arg_implementations.OptionalIntArgType(is_signed=False),
                        "ID задачи, в которую будет вложена добавляемая задача"
                    ),
                    lexer_classes.Arg(
                        "текст новой задачи",
                        arg_implementations.StringArgType()
                    )
                )
            ),
            lexer_classes.Command(
                names=("показать", "show", "дерево", "tree"),
                description="выводит в консоль дерево задач",
                handler=handlers.get_tasks_as_string
            ),
            lexer_classes.Command(
                names=(
                    "удалить", "delete", "del", "-", "remove", "убрать", "rm"
                ),
                description="удаляет задачу с указанным ID",
                handler=handlers.delete_tasks,
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно удалить",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ), (
                            "ID задач должны быть через запятую; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                names=(
                    "пометить", "чек", "отметить", "выполнить",
                    "check", "mark", "complete", "x", "х", "X", "Х"
                ),
                description="помечает задачи как выполненные",
                handler=functools.partial(
                    handlers.change_bool_field_state,
                    BooleanTaskFields.IS_CHECKED, True
                ),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно пометить выполненными",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ), (
                            "ID задач должны быть через запятую; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                names=("убрать метку", "снять метку", "uncheck"),
                description="помечает задачи как невыполненные",
                handler=functools.partial(
                    handlers.change_bool_field_state,
                    BooleanTaskFields.IS_CHECKED, False
                ),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно пометить невыполненными",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ), (
                            "ID задач должны быть через запятую; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                names=("свернуть", "collapse"),
                description=(
                    "сворачивает задачу, так что все дочерние задачи не будут "
                    "видны"
                ),
                handler=functools.partial(
                    handlers.change_bool_field_state,
                    BooleanTaskFields.IS_COLLAPSED, True
                ),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно свернуть",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ), (
                            "ID задач должны быть через запятую; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                names=("развернуть", "expand"),
                description=(
                    "разворачивает задачу, так что все дочерние задачи будут "
                    "видны"
                ),
                handler=functools.partial(
                    handlers.change_bool_field_state,
                    BooleanTaskFields.IS_COLLAPSED, False
                ),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно свернуть",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ), (
                            "ID задач должны быть через запятую; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                names=("изменить", "отредактировать", "change", "edit"),
                description="изменяет текст указанной задачи",
                handler=handlers.edit_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID задачи",
                        arg_implementations.IntArgType(is_signed=False)
                    ),
                    lexer_classes.Arg(
                        "текст задачи",
                        arg_implementations.StringArgType()
                    )
                )
            ),
            lexer_classes.Command(
                names=(
                    "переместить", "двинуть", "сдвинуть", "передвинуть", "move",
                    "удочерить", "adopt"
                ),
                description=(
                    "изменяет ID родителя указанных задач (задачи "
                    "\"переезжают\" в дочерние к другой задаче); "
                    "ID родителя может быть пропущено (-), тогда задачи "
                    "станут корневыми; задачи нужно прописывать через запятую"
                ),
                handler=handlers.change_parent_of_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID нового родителя",
                        arg_implementations.OptionalIntArgType(is_signed=False),
                        "к кому переезжает"
                    ),
                    lexer_classes.Arg(
                        "ID задач",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType(is_signed=False)
                        ),
                        "что переезжает"
                    )
                )
            ),
            lexer_classes.Command(
                names=("дата", "date", "time", "время"),
                description="показывает дату (и время) создания задачи",
                handler=handlers.show_date,
                arguments=(
                    lexer_classes.Arg(
                        "ID задачи",
                        arg_implementations.IntArgType(is_signed=False)
                    ),
                )
            )
        )
        commands_description: Dict[str, List[Callable]] = {}
        for command in self.commands:
            for name in command.names:
                try:
                    commands_description[name].append(
                        command.get_full_description
                    )
                except KeyError:
                    commands_description[name] = [
                        command.get_full_description
                    ]
        self.constant_context = lexer_classes.ConstantContext(
            self.commands, commands_description
        )

    def listen_for_commands_infinitely(self) -> NoReturn:
        while True:
            entered_command = input(">>> ")
            result: HandlingResult = self.handle_command(entered_command)
            if (
                result.whether_to_print_a_tree
                and self.ini_worker.get_auto_showing_state()
            ):
                print(self.handlers.get_tasks_as_string().message)
            print(result.message)

    def handle_command(self, command: str) -> HandlingResult:
        error_args_amount = 0
        for command_ in self.commands:
            try:
                converted_command = command_.convert_command_to_args(command)
            except exceptions.ParsingError as parsing_error:
                if parsing_error.args_num > error_args_amount:
                    error_args_amount = parsing_error.args_num
            else:
                return command_.handler(
                    *command_.get_all_constant_metadata_as_converted(
                        self.constant_context
                    ),
                    *converted_command.arguments
                )
        if error_args_amount == 0:
            return HandlingResult(
                "Ошибка обработки команды на её названии!",
                whether_to_print_a_tree=False
            )
        else:
            return HandlingResult(
                (
                    f"Ошибка обработки команды на аргументе номер "
                    f"{error_args_amount} (он неправильный или пропущен)"
                ), whether_to_print_a_tree=False
            )


if __name__ == '__main__':
    ini_worker = MyINIWorker(ConfigParser(), "tree_of_tasks_config.ini")
    main_logic = MainLogic(
        ini_worker,
        Handlers(
            ini_worker,
            db_apis.TasksManager(
                db_apis.get_sqlalchemy_db_session("sqlite:///tree_of_tasks.db")
            )
        )
    )
    main_logic.listen_for_commands_infinitely()
