"""BDD step definitions for the Checks page. Each step delegates to ChecksPage."""

from __future__ import annotations

from pytest_bdd import given, parsers, then, when

from pages import ChecksPage


@given("I open the Checks list page")
def _open_checks(checks_page: ChecksPage) -> None:
    checks_page.open()
    checks_page.expect_loaded()


@given("I note the current card count")
def _note_card_count(checks_page: ChecksPage, search_state: dict[str, object]) -> None:
    search_state["initial_count"] = checks_page.card_count()


@then("every card has a non-empty name")
def _every_card_has_name(checks_page: ChecksPage) -> None:
    checks_page.expect_every_card_has_non_empty_name()


@then("the SM sub-nav exposes Checks, Probes, Alerts (Legacy) and Config entries")
def _sm_nav_entries_visible(checks_page: ChecksPage) -> None:
    checks_page.expect_sm_nav_entries_visible()


@then("every card's Type belongs to the known enum")
def _every_card_type_is_known(checks_page: ChecksPage) -> None:
    checks_page.expect_every_card_type_is_known()


@when(parsers.parse('I search for "{search_term}"'))
def _search_for_term(
    checks_page: ChecksPage, search_state: dict[str, object], search_term: str
) -> None:
    search_state["term"] = search_term
    checks_page.search(search_term)


@then("every visible card contains the search term")
def _cards_contain_term(
    checks_page: ChecksPage, search_state: dict[str, object]
) -> None:
    checks_page.expect_all_visible_cards_contain(str(search_state["term"]))


@then("the visible card count matches the expected number")
def _count_matches(checks_page: ChecksPage, search_state: dict[str, object]) -> None:
    count = checks_page.card_count()
    initial = int(search_state["initial_count"])
    assert 1 <= count <= initial, (
        f"Expected 1–{initial} cards after searching {search_state['term']!r}, "
        f"got {count}."
    )


@when("I clear the search")
def _clear_search(checks_page: ChecksPage) -> None:
    checks_page.clear_search()


@then("the visible card count equals the initial count")
def _count_restored(checks_page: ChecksPage, search_state: dict[str, object]) -> None:
    checks_page.expect_card_count(int(search_state["initial_count"]))
