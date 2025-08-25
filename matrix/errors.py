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
        if cmd is None:
            cmd_name = "global check"
        else:
            cmd_name = cmd.name

        super().__init__(f"'{check.__name__}' has failed for '{cmd_name}'!")


class ConfigError(MatrixError):
    def __init__(self, error):
        super().__init__(f"Missing required configuration: '{error}'")
