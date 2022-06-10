import textwrap
from pathlib import Path
from typing import List, Optional
from pytest import Pytester
from _pytest.fixtures import SubRequest

import pytest

# DEPRECATED OLD MODULE
from tests.conftest_deprecated import *


pytest_plugins = "pytester"


def connect_to_debugger(tester: Pytester, enabled: bool = True) -> str:
    """Allows to connect to an Idea/PyCharm remote debugger from the in-string-tests code.

    In the virtualenv install the debugger client (with a compatible version): `pip install pydevd-pycharm`
    The 'Python Debug Server' must be configured (hostname: localhost, port: 12345) and
    running (Run->Debug->Your 'Python Debug Server' instance) before launching tests.

    :param tester: the Pytester instance
    :param enabled: whether to actually connect to the debugger
    :return: the string to add to the source code that connects the test to the debugger
    """

    debugger_host = "localhost"
    debugger_port = "12345"

    if enabled:
        tester.run("touch", "__init__.py")  # make sure this is treated as a package

        debugger_module = f"""
        from functools import partial
        import pydevd_pycharm

        connect_debugger = partial(pydevd_pycharm.settrace, '{debugger_host}',
                                   port={debugger_port}, stdoutToServer=True, stderrToServer=True)
        """

        _ = tester.makepyfile(debugger=debugger_module)
        return """from .debugger import connect_debugger; connect_debugger()"""
    else:
        return ""


def _get_next_test_file_index(request: SubRequest) -> int:
    """Hackish way to count pytester temp files in the same test.
    The actual value is stored in request.node.user_properties.

    :param request: The current test SubRequest
    :return: The next index
    """
    key = "pytester_test_file_index"
    index = 0

    new_props = []
    for prop in request.node.user_properties:
        if prop[0] == key:
            index = prop[1] + 1
            new_props.append((prop[0], index))
        else:
            new_props.append(prop)

    if index == 0:
        new_props.append((key, index))

    request.node.user_properties = new_props

    return index


@pytest.fixture
def add_test_file(pytester, request):
    """A wrapper of pytester.makepyfile that can inject a pycharm remote debugger and allows for multiple test temp
    file without specifying directly custom file names."""

    def _add_test_file(
        source: str,
        name: Optional[str] = None,
        connect_debugger: bool = False,
    ) -> Path:
        """A wrapper of pytester.makepyfile that can inject a pycharm remote debugger and allows for multiple test
        temp file without specifying directly custom file names.

        :param source: the source code of the file
        :param name: a custom name; should begin with test_ if it's to be collected by pytest
        :param connect_debugger: whether to start the debugger
        :return: the path of the temp file
        """
        debugger_str = ""
        if connect_debugger:
            debugger_str = connect_to_debugger(pytester) + "\n\n"
        test_str = f"""{debugger_str}{textwrap.dedent(source)}"""

        index = _get_next_test_file_index(request)
        if name is None:
            name = f"{request.node.name}"
            if index > 0:
                name += f"_{index}"

        return pytester.makepyfile(**{name: test_str})

    return _add_test_file


@pytest.fixture
def get_test_cassettes(pytester):
    """Return a list of PosixPath of cassettes associated with the test file passed as the argument."""

    def _assert_test_cassettes_empty(test_file: Path) -> List[Path]:
        """Return a list of PosixPath of cassettes associated with the test file passed as the argument.

        :param test_file: the chosen test file
        :return: a list of the PosixPath of the cassettes associated with the file
        """
        test_cassettes_path = Path(
            str(test_file).replace(test_file.name, f"cassettes/{test_file.stem}")
        )
        return list(test_cassettes_path.glob("*"))

    return _assert_test_cassettes_empty


@pytest.fixture
def default_conftest(pytester):
    """Provide a conftest.py with the default confit for pytest-recording that will allow to record cassettes."""
    # language=python  # IDE language injection
    source = """
import pytest
    
@pytest.fixture(scope="module")
def vcr_config():
    return {"record_mode": ["once"]}
"""
    return pytester.makepyfile(conftest=source)


@pytest.fixture
def is_file(pytester):
    """Check if a file exists in the pytester temporary folder."""

    def _is_file(name: str) -> bool:
        """Check if a file exists in the pytester temporary folder.

        :param name: the file name
        :return: True if the file exists, False otherwise
        """
        return (pytester.path / name).exists()

    return _is_file
