from typing import Tuple, List, Dict, Callable

from lexer.lexer_classes import BaseConstantMetadata, ConstantContext, Command


class CommandsConstantMetadata(BaseConstantMetadata):

    @staticmethod
    def get_data_from_context(
            context: ConstantContext) -> Tuple["Command", ...]:
        return context.commands


class CommandDescriptionsConstantMetadata(BaseConstantMetadata):

    @staticmethod
    def get_data_from_context(
            context: ConstantContext) -> Dict[str, List[Callable]]:
        return context.command_descriptions
