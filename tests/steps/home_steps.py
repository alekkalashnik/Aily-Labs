"""BDD step definitions for the Home page. Each step delegates to HomePage."""

from __future__ import annotations

from pytest_bdd import given, parsers, then

from pages import HomePage


@given("I open the Synthetic Monitoring home page")
def _open_home(home_page: HomePage) -> None:
    home_page.open()
    home_page.expect_loaded()


@then(parsers.parse('the page title mentions "{title}"'))
def _title_mentions(home_page: HomePage, title: str) -> None:
    home_page.expect_title_mentions(title)


@then("the Grafana app shell is visible")
def _shell_visible(home_page: HomePage) -> None:
    home_page.expect_app_shell_visible()


@then("no unexpected console errors are recorded")
def _no_console_errors(home_page: HomePage, console_errors: list[str]) -> None:
    home_page.expect_no_console_errors(console_errors)
