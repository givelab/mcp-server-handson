import pytest


@pytest.fixture(autouse=True)
def reset_slack_singleton():
    import handler
    handler._slack = None
    yield
    handler._slack = None
