from metaso.exceptions import (
    MetasoError, AuthError, BackendError, NetworkError,
    RateLimitError, ServerError, NotFoundError, ValidationError,
)

def test_all_exceptions_inherit_from_metaso_error():
    for exc_cls in [AuthError, BackendError, NetworkError, RateLimitError, ServerError, NotFoundError, ValidationError]:
        assert issubclass(exc_cls, MetasoError)

def test_exception_message():
    err = AuthError("token expired")
    assert str(err) == "token expired"
    assert isinstance(err, MetasoError)

def test_backend_error_with_operation():
    err = BackendError("OfficialBackend does not support create_topic")
    assert "create_topic" in str(err)
