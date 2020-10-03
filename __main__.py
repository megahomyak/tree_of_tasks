from configparser import ConfigParser
from typing import NoReturn, Tuple

from sqlalchemy.orm.exc import NoResultFound

import dataclasses_
import db_apis
import exceptions
import orm_classes
from default_fields_for_settings_file import DEFAULT_FIELDS_FOR_SETTINGS
from ini_worker import MyINIWorker
from text_task_tree_printer import TextTaskTreePrinter as TasksPrinter
from types_converter import TypesConverter


class MainLogic:

    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            tasks_printer: TasksPrinter,
            ini_worker: MyINIWorker) -> None:
        self.tasks_manager = tasks_manager
        self.tasks_printer = tasks_printer
        ini_worker.load_fields_if_not_exists(DEFAULT_FIELDS_FOR_SETTINGS)
        ini_worker.save()
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
                self.print_tasks
            ),
            dataclasses_.Command(
                ("удалить", "delete", "del", "-", "remove", "убрать", "rm"),
                "удаляет задачу с указанным ID",
                self.delete_task,
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно удалить",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType(),
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
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
            if self.settings.get_auto_showing_state():
                self.print_tasks()
        else:
            print(
                f"Задачи с ID {parent_id} нет, поэтому новая задача не может "
                f"быть создана"
            )

    def delete_task(self, task_ids: Tuple[int]) -> None:
        at_least_one_task_is_deleted = False
        for task_id in task_ids:
            try:
                self.tasks_manager.delete(
                    self.tasks_manager.get_task_by_id(task_id)
                )
                self.tasks_manager.commit()
                at_least_one_task_is_deleted = True
            except NoResultFound:
                print(
                    f"Задачи с ID {task_id} нет, поэтому она не может быть "
                    f"удалена"
                )
        if at_least_one_task_is_deleted:
            if self.settings.get_auto_showing_state():
                self.print_tasks()

    def show_help_message(self) -> None:
        print("\n\n".join(
            [
                command.get_full_description(include_heading=True)
                for command in self.commands
            ]
        ))

    def switch_auto_showing(self) -> None:
        is_auto_showing_enabled = self.settings.get_auto_showing_state()
        print(
            "Автопоказ дерева задач после каждой команды теперь "
            f"{'включен' if not is_auto_showing_enabled else 'выключен'}"
        )
        self.settings["auto_showing"] = str(not is_auto_showing_enabled)
        self.settings.save()

    def print_tasks(self) -> None:
        root_tasks = self.tasks_manager.get_root_tasks()
        if root_tasks:
            self.tasks_printer.print_tasks_recursively(
                root_tasks
            )
        else:
            print("<дерево пустое>")

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
        MyINIWorker(
            ConfigParser(),
            "tree_of_tasks_config.ini",
            TypesConverter()
        )
    )
    main_logic.listen_for_commands_infinitely()
