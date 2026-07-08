from matrix._error_handler import resolve_error_handler


class BaseCustomError(Exception):
    pass


class SubCustomError(BaseCustomError):
    pass


def test_resolve_error_handler_with_exact_type_match__expect_handler_returned():
    def handler(error):
        pass

    handlers = {ValueError: handler}

    assert resolve_error_handler(handlers, ValueError("boom")) is handler


def test_resolve_error_handler_with_exception_subclass__expect_base_handler_returned():
    def handler(error):
        pass

    handlers = {BaseCustomError: handler}

    assert resolve_error_handler(handlers, SubCustomError("boom")) is handler


def test_resolve_error_handler_with_grandparent_exception_class__expect_handler_returned():
    class GrandparentError(Exception):
        pass

    class ParentError(GrandparentError):
        pass

    class ChildError(ParentError):
        pass

    def handler(error):
        pass

    handlers = {GrandparentError: handler}

    assert resolve_error_handler(handlers, ChildError("boom")) is handler


def test_resolve_error_handler_with_no_matching_handler__expect_none_returned():
    def handler(error):
        pass

    handlers = {ValueError: handler}

    assert resolve_error_handler(handlers, TypeError("boom")) is None


def test_resolve_error_handler_with_empty_handlers__expect_none_returned():
    assert resolve_error_handler({}, ValueError("boom")) is None


def test_resolve_error_handler_with_specific_and_base_registered__expect_specific_handler_returned():
    def base_handler(error):
        pass

    def specific_handler(error):
        pass

    handlers = {BaseCustomError: base_handler, SubCustomError: specific_handler}

    assert resolve_error_handler(handlers, SubCustomError("boom")) is specific_handler
