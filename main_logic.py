import functools
from configparser import ConfigParser
from typing import NoReturn, Optional, Dict, List, Callable

from handlers.handlers import Handlers
from ini_worker import MyINIWorker
from lexer import (
    arg_implementations, constant_metadata_implementations,
    lexer_classes, exceptions
)
from orm import db_apis


class MainLogic:

    # noinspection PyShadowingNames
    # Because I don't care, it's the same object
    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            ini_worker: MyINIWorker, handlers: Handlers) -> None:
        self.tasks_manager = tasks_manager
        ini_worker.load(default_contents="[DEFAULT]\n"
                                         "auto_showing = True")
        self.ini_worker = ini_worker
        self.handlers = handlers
        if self.ini_worker.get_auto_showing_state():
            print(self.get_local_tasks_as_string())
        self.commands = (
            lexer_classes.Command(
                ("автопоказ", "autoshowing"),
                "включает/выключает показ дерева задач после каждого изменения",
                handlers.change_auto_showing,
                arguments=(
                    lexer_classes.Arg(
                        "состояние настройки",
                        arg_implementations.BoolArgType()
                    ),
                )
            ),
            lexer_classes.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает список команд",
                handlers.get_help_message,
                (constant_metadata_implementations.CommandsMetadata,)
            ),
            lexer_classes.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает помощь по конкретным командам",
                handlers.get_help_message_for_specific_commands,
                (constant_metadata_implementations.CommandsMetadata,),
                (
                    lexer_classes.Arg(
                        "названия команд",
                        arg_implementations.SequenceArgType(
                            arg_implementations.StringArgType()
                        ),
                        (
                            "названия команд должны быть через запятую без "
                            "пробела; название только одной команды тоже можно "
                            "написать; в качестве имени команды можно "
                            "использовать еще и любой псевдоним этой команды"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                ("добавить", "add", "+"),
                (
                    "добавляет задачу с указанным "
                    "родителем (необязательно) и текстом"
                ),
                handlers.add_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID родителя",
                        arg_implementations.OptionalIntArgType(),
                        "ID задачи, в которую будет вложена добавляемая задача"
                    ),
                    lexer_classes.Arg(
                        "текст новой задачи",
                        arg_implementations.StringArgType()
                    )
                )
            ),
            lexer_classes.Command(
                ("показать", "show", "дерево", "tree"),
                "выводит в консоль дерево задач",
                handlers.get_tasks_as_string
            ),
            lexer_classes.Command(
                ("удалить", "delete", "del", "-", "remove", "убрать", "rm"),
                "удаляет задачу с указанным ID",
                handlers.delete_tasks,
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно удалить",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                (
                    "пометить", "чек", "отметить", "выполнить",
                    "check", "mark", "complete", "x", "х", "X", "Х"
                ),
                "помечает задачи как выполненные",
                functools.partial(handlers.change_checked_state, True),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно пометить выполненными",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                ("убрать метку", "снять метку", "uncheck"),
                "помечает задачи как невыполненные",
                functools.partial(handlers.change_checked_state, False),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно пометить невыполненными",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                ("свернуть", "collapse"),
                (
                    "сворачивает задачу, так что все дочерние задачи не будут "
                    "видны"
                ),
                functools.partial(handlers.change_collapsing_state, True),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно свернуть",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                ("развернуть", "expand"),
                (
                    "разворачивает задачу, так что все дочерние задачи будут "
                    "видны"
                ),
                functools.partial(handlers.change_collapsing_state, False),
                arguments=(
                    lexer_classes.Arg(
                        "ID задач, которые нужно свернуть",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            lexer_classes.Command(
                (
                    "изменить", "отредактировать",
                    "change", "edit"
                ),
                "изменяет текст указанной задачи",
                handlers.edit_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID задачи",
                        arg_implementations.IntArgType()
                    ),
                    lexer_classes.Arg(
                        "текст задачи",
                        arg_implementations.StringArgType()
                    )
                )
            ),
            lexer_classes.Command(
                (
                    "переместить", "двинуть", "сдвинуть", "передвинуть", "move",
                    "удочерить", "adopt"
                ),
                (
                    "изменяет ID родителя указанных задач (задачи "
                    "\"переезжают\" в дочерние к другой задаче); "
                    "ID родителя может быть пропущено (-), тогда задачи "
                    "станут корневыми; задачи нужно прописывать через запятую "
                    "без пробела"
                ),
                handlers.change_parent_of_task,
                arguments=(
                    lexer_classes.Arg(
                        "ID нового родителя",
                        arg_implementations.OptionalIntArgType(),
                        "к кому переезжает"
                    ),
                    lexer_classes.Arg(
                        "ID задач",
                        arg_implementations.SequenceArgType(
                            arg_implementations.IntArgType()
                        ),
                        "что переезжает"
                    )
                )
            ),
            lexer_classes.Command(
                ("дата", "date", "time", "время"),
                "показывает дату (и время) создания задачи",
                handlers.show_date,
                arguments=(
                    lexer_classes.Arg(
                        "ID задачи",
                        arg_implementations.IntArgType()
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

    def get_local_tasks_as_string(self):
        return self.handlers.get_tasks_as_string()

    def listen_for_commands_infinitely(self) -> NoReturn:
        while True:
            entered_command = input(">>> ")
            result = self.handle_command(entered_command)
            if result is None:
                if self.ini_worker.get_auto_showing_state():
                    print(self.get_local_tasks_as_string())
            else:
                print(result)

    def handle_command(self, command: str) -> Optional[str]:
        error_args_amount = 0
        for command_ in self.commands:
            try:
                converted_command = command_.convert_command_to_args(command)
            except exceptions.ParsingError as parsing_error:
                if parsing_error.args_num > error_args_amount:
                    error_args_amount = parsing_error.args_num
            else:
                return command_.attached_function(
                    *command_.get_all_metadata_as_converted(
                        self.constant_context
                    ),
                    *converted_command.arguments
                )
        if error_args_amount == 0:
            return "Ошибка обработки команды на её названии!"
        else:
            return (
                f"Ошибка обработки команды на аргументе номер "
                f"{error_args_amount} (он неправильный или пропущен)"
            )


if __name__ == '__main__':
    ini_worker = MyINIWorker(
        ConfigParser(),
        "tree_of_tasks_config.ini"
    )
    tasks_manager = db_apis.TasksManager(
        db_apis.get_sqlalchemy_db_session("sqlite:///tree_of_tasks.db")
    )
    main_logic = MainLogic(
        tasks_manager,
        ini_worker,
        Handlers(ini_worker, tasks_manager)
    )
    main_logic.listen_for_commands_infinitely()
