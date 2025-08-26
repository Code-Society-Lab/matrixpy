class MatrixError(Exception):
    pass


class CommandError(MatrixError):
    pass


class CommandNotFoundError(CommandError):
    def __init__(self, cmd):
        super().__init__(f"Command with name '{cmd}' not found")


class AlreadyRegisteredError(CommandError):
    def __init__(self, cmd):
        super().__init__(f"Command '{cmd}' is already registered")


class MissingArgumentError(CommandError):
    def __init__(self, param):
        super().__init__(f"Missing required argument: '{param.name}'")


class CheckError(CommandError):
    def __init__(self, cmd, check):
        super().__init__(f"'{check.__name__}' has failed for '{cmd.name}'!")


class ConfigError(MatrixError):
    def __init__(self, error):
        super().__init__(f"Missing required configuration: '{error}'")


class CooldownError(CheckError):
    def __init__(self, cmd, check):
        super().__init__(cmd, check)
