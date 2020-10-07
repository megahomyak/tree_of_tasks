import functools
from configparser import ConfigParser
from typing import NoReturn, Optional

import dataclasses_
import exceptions
import handlers
from orm import db_apis
from scripts_for_settings.default_fields_for_settings_file import (
    DEFAULT_FIELDS_FOR_SETTINGS
)
from scripts_for_settings.ini_worker import MyINIWorker
from types_converter import TypesConverter


class MainLogic:

    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            ini_worker: MyINIWorker) -> None:
        self.tasks_manager = tasks_manager
        ini_worker.load()
        ini_worker.load_fields_if_not_exists(DEFAULT_FIELDS_FOR_SETTINGS)
        ini_worker.save()
        self.settings = ini_worker
        if self.settings.get_auto_showing_state():
            print(self.get_local_tasks_as_string())
        self.commands = (
            dataclasses_.Command(
                ("автопоказ", "autoshowing"),
                "включает/выключает показ дерева задач после каждого изменения",
                handlers.change_auto_showing,
                (
                    dataclasses_.INIWorkerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "состояние настройки",
                        dataclasses_.BoolArgType()
                    ),
                )
            ),
            dataclasses_.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает список команд",
                handlers.get_help_message,
                (
                    dataclasses_.CommandsMetadata,
                )
            ),
            dataclasses_.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает помощь по конкретным командам",
                handlers.get_help_message_for_specific_commands,
                (
                    dataclasses_.CommandsMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "названия команд",
                        dataclasses_.SequenceArgType(
                            dataclasses_.StringArgType()
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
            dataclasses_.Command(
                ("добавить", "add", "+"),
                (
                    "добавляет задачу с указанным "
                    "родителем (необязательно) и текстом"
                ),
                handlers.add_task,
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID родителя",
                        dataclasses_.OptionalIntArgType(),
                        "ID задачи, в которую будет вложена добавляемая задача"
                    ),
                    dataclasses_.Arg(
                        "текст новой задачи",
                        dataclasses_.StringArgType()
                    )
                )
            ),
            dataclasses_.Command(
                ("показать", "show", "дерево", "tree"),
                "выводит в консоль дерево задач",
                handlers.get_tasks_as_string,
                (
                    dataclasses_.RootTasksMetadata,
                )
            ),
            dataclasses_.Command(
                ("удалить", "delete", "del", "-", "remove", "убрать", "rm"),
                "удаляет задачу с указанным ID",
                handlers.delete_tasks,
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно удалить",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                (
                    "пометить", "чек", "отметить", "выполнить",
                    "check", "mark", "complete", "x", "х", "X", "Х"
                ),
                "помечает задачи как выполненные",
                functools.partial(handlers.change_checked_state, True),
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно пометить выполненными",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("убрать метку", "снять метку", "uncheck"),
                "помечает задачи как невыполненные",
                functools.partial(handlers.change_checked_state, False),
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно пометить невыполненными",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("свернуть", "collapse"),
                (
                    "сворачивает задачу, так что все дочерние задачи не будут "
                    "видны"
                ),
                functools.partial(handlers.change_collapsing_state, True),
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно свернуть",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("развернуть", "expand"),
                (
                    "разворачивает задачу, так что все дочерние задачи будут "
                    "видны"
                ),
                functools.partial(handlers.change_collapsing_state, False),
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно свернуть",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                (
                    "изменить", "отредактировать",
                    "change", "edit"
                ),
                "изменяет текст указанной задачи",
                handlers.edit_task,
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задачи",
                        dataclasses_.IntArgType()
                    ),
                    dataclasses_.Arg(
                        "текст задачи",
                        dataclasses_.StringArgType()
                    )
                )
            ),
            dataclasses_.Command(
                (
                    "изменить ID родителя", "change parent ID",
                    "отредактировать ID родителя", "edit parent ID",
                    "установить ID родителя", "set parent ID"
                ),
                (
                    "изменяет ID родителя указанной задачи (задача "
                    "\"переезжает\" в дочерние к другой задаче); "
                    "ID родителя может быть пропущено (-), тогда задача "
                    "станет корневой"
                ),
                handlers.change_parent_of_task,
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задачи",
                        dataclasses_.IntArgType()
                    ),
                    dataclasses_.Arg(
                        "ID нового родителя",
                        dataclasses_.OptionalIntArgType()
                    )
                )
            ),
            dataclasses_.Command(
                ("дата", "date", "time", "время"),
                "показывает дату (и время) создания задачи",
                handlers.show_date,
                (
                    dataclasses_.TasksManagerMetadata,
                ),
                (
                    dataclasses_.Arg(
                        "ID задачи",
                        dataclasses_.IntArgType()
                    ),
                )
            )
        )

    def get_local_tasks_as_string(self):
        return handlers.get_tasks_as_string(
            self.tasks_manager.get_root_tasks()
        )

    def listen_for_commands_infinitely(self) -> NoReturn:
        while True:
            entered_command = input(">>> ")
            result = self.handle_command(entered_command)
            if result is None:
                if self.settings.get_auto_showing_state():
                    print(self.get_local_tasks_as_string())
            else:
                print(result)

    def handle_command(self, command: str) -> Optional[str]:
        context = dataclasses_.Context(
            self.tasks_manager,
            self.settings,
            self.commands
        )
        for command_ in self.commands:
            try:
                result: Optional[str] = command_.attached_function(
                    *command_.get_all_metadata_as_converted(context),
                    *command_.convert_command_to_args(command)
                )
            except exceptions.ParsingError:
                pass
            else:
                return result
        return "Что?"


if __name__ == '__main__':
    main_logic = MainLogic(
        db_apis.TasksManager(
            db_apis.get_sqlalchemy_db_session("sqlite:///tree_of_tasks.db")
        ),
        MyINIWorker(
            ConfigParser(),
            "tree_of_tasks_config.ini",
            TypesConverter()
        )
    )
    main_logic.listen_for_commands_infinitely()
