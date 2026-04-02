import pytest

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-e2e", default=False):
        skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)

def pytest_addoption(parser):
    parser.addoption("--run-e2e", action="store_true", default=False, help="run e2e tests")
