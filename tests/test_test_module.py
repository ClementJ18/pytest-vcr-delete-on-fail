import pytest


def test_it_should_handle_automatically_more_than_one_test_file(
    pytester, add_test_file
):
    """It should handle automatically more than one test file"""
    # language=python  # IDE language injection
    t_0_source = """
    def test_first():
        assert True
    """
    t_0 = add_test_file(t_0_source, connect_debugger=False)

    # language=python  # IDE language injection
    t_1_source = """
    def test_second():
        assert False
    """
    t_1 = add_test_file(t_1_source, connect_debugger=False)

    # language=python  # IDE language injection
    t_2_source = """
    def test_third():
        assert True
    """
    t_2 = add_test_file(t_2_source, connect_debugger=False, name="test_custom")

    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=2)

    # Check in the test stdout that the correct filename are present
    for test_name in [
        "test_it_should_handle_automatically_more_than_one_test_file.py",
        "test_it_should_handle_automatically_more_than_one_test_file_1.py",
        "test_custom.py",
    ]:
        assert (
            len(list(filter(lambda line: test_name in line, result.stdout.lines))) > 0
        )


class TestARemoteDebuggerInjecter:
    """Test: A remote debugger injecter..."""

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, pytester, add_test_file):
        """TestARemoteDebuggerInjecter setup"""
        # language=python  # IDE language injection
        t_0_source = """
        def test_first():
            assert True
        """
        add_test_file(t_0_source, connect_debugger=True, name="test_file")

    def test_should_result_in_a_module(self, pytester):
        """A remote debugger injecter should result in a module."""
        out = pytester.run("ls", "__init__.py").stdout.lines
        assert out[0] == "__init__.py"

    def test_should_inject_the_debugger_in_the_test_file(self, pytester):
        """A remote debugger injecter should inject the debugger in the test file."""
        test_file_lines = pytester.run("cat", "test_file.py").stdout.lines
        assert (
            test_file_lines[0]
            == "from .debugger import connect_debugger; connect_debugger()"
        )

    def test_should_make_available_the_debug_module(self, pytester):
        """A remote debugger injecter should make available the debug module."""
        out = pytester.run("cat", "debugger.py").stdout.lines
        assert "connect_debugger" in out[3]


@pytest.mark.vcr
def test_it_should_allow_to_make_assertions_about_cassettes(
    pytester, add_test_file, get_test_cassettes, default_conftest
):
    """It should allow to make assertions about cassettes"""
    # language=python  # IDE language injection
    t_0_source = """
import pytest
import requests
    
@pytest.mark.vcr
def test_first():
    assert requests.get("https://github.com").status_code == 200
"""
    t_0 = add_test_file(t_0_source, connect_debugger=False)

    # language=python  # IDE language injection
    t_1_source = """
import requests
    
def test_second():
    assert requests.get("https://github.com").status_code == 200
"""
    t_1 = add_test_file(t_1_source, connect_debugger=False)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)

    t_0_cassettes_names = map(lambda x: x.name, get_test_cassettes(t_0))
    assert "test_first.yaml" in t_0_cassettes_names
    assert "test_second.yaml" not in t_0_cassettes_names

    t_1_cassettes = get_test_cassettes(t_1)
    assert not t_1_cassettes


def test_it_should_handle_assertions_about_nested_modules_cassettes(
    pytester, add_test_file, get_test_cassettes, default_conftest
):
    """It should handle assertions about nested modules cassettes."""
    # language=python  # IDE language injection
    t_0_source = """
import pytest
import requests
    
@pytest.mark.vcr
def test_first():
    assert requests.get("https://github.com").status_code == 200
"""
    pytester.mkpydir("test_nested")

    t_0 = add_test_file(
        t_0_source, connect_debugger=False, name="test_nested/test_nested_module"
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)

    t_0_cassettes_names = map(lambda x: x.name, get_test_cassettes(t_0))
    assert "test_first.yaml" in t_0_cassettes_names
