from typing import Any

from lexer.lexer_classes import BaseConstantMetadata, ConstantContext


class CommandsConstantMetadata(BaseConstantMetadata):

    @staticmethod
    def get_data_from_context(context: ConstantContext) -> Any:
        return context.commands
