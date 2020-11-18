from typing import Tuple, List

from lexer.lexer_classes import BaseConstantMetadata, ConstantContext, Command


class CommandsConstantMetadata(BaseConstantMetadata):

    @staticmethod
    def get_data_from_context(
            context: ConstantContext) -> Tuple["Command", ...]:
        return context.commands
