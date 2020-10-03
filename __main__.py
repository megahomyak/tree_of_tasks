from configparser import ConfigParser
from typing import NoReturn

import dataclasses_
import db_apis
import exceptions
import orm_classes
from default_fields_for_settings_file import DEFAULT_FIELDS_FOR_SETTINGS
from ini_worker import INIWorker
from text_task_tree_printer import TextTaskTreePrinter as TasksPrinter
from types_converter import TypesConverter


class MainLogic:

    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            tasks_printer: TasksPrinter,
            ini_worker: INIWorker,
            types_converter: TypesConverter) -> None:
        self.tasks_manager = tasks_manager
        self.tasks_printer = tasks_printer
        self.types_converter = types_converter
        ini_worker.load_fields_if_not_exists(DEFAULT_FIELDS_FOR_SETTINGS)
        self.settings = ini_worker
        self.commands = (
            dataclasses_.Command(
                ("автопоказ", "autoshowing", "авто показ", "auto showing"),
                "переключает показ дерева задач после каждого изменения",
                self.switch_auto_showing
            ),
            dataclasses_.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает список команд",
                self.show_help_message
            ),
            dataclasses_.Command(
                ("добавить", "add", "+"),
                (
                    "добавляет задачу с указанным "
                    "родителем (необязательно) и текстом"
                ),
                self.add_task,
                (
                    dataclasses_.Arg(
                        "ID родителя",
                        dataclasses_.OptionalIntArgType(is_signed=False),
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
                self.print_tasks
            )
        )

    def add_task(self, parent_id: int, text: str) -> None:
        if (
            parent_id is None
            or
            self.tasks_manager.check_existence(
                orm_classes.Task.id == parent_id
            )
        ):
            task = orm_classes.Task(text=text, parent_task_id=parent_id)
            self.tasks_manager.append(task)
            self.tasks_manager.commit()
            self.print_tasks()
        else:
            print(
                f"Задачи с id {parent_id} нет, поэтому новая задача не может"
                f"быть создана"
            )

    def show_help_message(self) -> None:
        print("\n\n".join(
            [
                command.get_full_description(include_heading=True)
                for command in self.commands
            ]
        ))

    def switch_auto_showing(self) -> None:
        is_auto_showing_enabled = self.types_converter.str_to_bool(
            self.settings["auto_showing"]
        )
        print(
            "Автопоказ дерева задач после каждой команды теперь "
            f"{'включен' if not is_auto_showing_enabled else 'выключен'}"
        )
        self.settings["auto_showing"] = str(not is_auto_showing_enabled)

    def print_tasks(self) -> None:
        self.tasks_printer.print_tasks_recursively(
            self.tasks_manager.get_root_tasks()
        )

    def listen_for_commands_infinitely(self) -> NoReturn:
        while True:
            entered_command = input(">>> ")
            for command in self.commands:
                try:
                    command.attached_function(
                        *command.convert_command_to_args(entered_command)
                    )
                except exceptions.ParsingError:
                    pass
                else:
                    break
            else:
                print("Что?")


if __name__ == '__main__':
    main_logic = MainLogic(
        db_apis.TasksManager(
            db_apis.get_sqlalchemy_db_session("sqlite:///tree_of_tasks.db")
        ),
        TasksPrinter(),
        INIWorker(
            ConfigParser(),
            "tree_of_tasks_config.ini"
        ),
        TypesConverter()
    )
    main_logic.listen_for_commands_infinitely()
