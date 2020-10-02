from typing import NoReturn

import dataclasses_
import db_apis
import exceptions
from default_fields_for_settings_file import DEFAULT_FIELDS_FOR_SETTINGS
from ini_worker import INIWorker
from text_task_tree_printer import TextTaskTreePrinter
from types_converter import TypesConverter


class MainLogic:

    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            tasks_printer: TextTaskTreePrinter,
            ini_worker: INIWorker,
            types_converter: TypesConverter) -> None:
        self.tasks_manager = tasks_manager
        self.tasks_printer = tasks_printer
        self.types_converter = types_converter
        ini_worker.load_fields_if_not_exists(DEFAULT_FIELDS_FOR_SETTINGS)
        self.settings = ini_worker
        self.commands = (
            dataclasses_.Command(
                ("автопоказ",),
                "переключает показ дерева задач после каждого изменения",
                self.switch_auto_showing
            ),
            dataclasses_.Command(
                ("помощь", "команды"),
                "показывает список команд",
                self.show_help_message
            )
        )

    def show_help_message(self) -> None:
        print("\n\n".join(
            [
                command.get_full_description()
                for command in self.commands
            ]
        ))

    def switch_auto_showing(self) -> None:
        self.settings["auto_showing"] = str(
            not self.types_converter.str_to_bool(self.settings["auto_showing"])
        )

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
                        command.convert_command_to_args(entered_command)
                    )
                except exceptions.ParsingError:
                    pass
                else:
                    break
            else:
                print("Что?")
