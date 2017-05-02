def pytest_addoption(parser):
    parser.addoption(
        "--run-integration-tests",
        action="store_true",
        help="Run integration tests as well as unit tests"
    )
