"""Checks list page of the Grafana Synthetic Monitoring plugin.

The UI renders each check as a card (data-testid="check-card") rather
than a table row.

We derive structured fields (like Check Type) by extracting the card text
and matching against known enums via pipe-split token matching. All action
methods are wrapped with `allure.step` for detailed reporting.
"""

from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, expect

from .base_page import BasePage

KNOWN_CHECK_TYPES: frozenset[str] = frozenset(
    {
        "HTTP",
        "PING",
        "DNS",
        "TCP",
        "TRACEROUTE",
        "MULTIHTTP",
        "SCRIPTED",
        "BROWSER",
    }
)


class ChecksPage(BasePage):
    URL = "/a/grafana-synthetic-monitoring-app/checks"

    _NAV_MENU_ITEM_TESTID: str = "data-testid Nav menu item"
    _SM_NAV_ENTRIES: tuple[str, ...] = ("Checks", "Probes", "Alerts (Legacy)", "Config")

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    @property
    def _checks_breadcrumb(self) -> Locator:
        return self._page.get_by_test_id("data-testid Checks breadcrumb")

    @property
    def _cards(self) -> Locator:
        return self._page.get_by_test_id("check-card")

    @property
    def _search_input(self) -> Locator:
        return self._page.get_by_test_id("check-search-input")

    # ------------------------------------------------------------------
    # Readiness
    # ------------------------------------------------------------------

    @allure.step("Checks page is loaded (breadcrumb + at least one card)")
    def expect_loaded(self) -> None:
        expect(self._checks_breadcrumb).to_be_visible()
        expect(self._cards.first).to_be_visible()

    # ------------------------------------------------------------------
    # Data snapshots (atomic, single round-trip)
    # ------------------------------------------------------------------

    def _snapshot_card_names(self) -> list[str]:
        return [t.strip() for t in self._cards.locator("h3").all_inner_texts()]

    @allure.step("Count visible cards")
    def card_count(self) -> int:
        # The SM plugin renders all cards atomically from one API response,
        # so waiting for the first card guarantees the full list is present.
        expect(self._cards.first).to_be_visible()
        return self._cards.count()

    def _snapshot_card_types(self) -> list[str | None]:
        types: list[str | None] = []
        for text in self._cards.all_inner_texts():
            tokens = [t.strip().upper() for t in text.replace("\n", "|").split("|")]
            types.append(next((t for t in tokens if t in KNOWN_CHECK_TYPES), None))
        return types

    # ------------------------------------------------------------------
    # Structural invariants (data-validation §3.1)
    # ------------------------------------------------------------------

    @allure.step("Every card has a non-empty name")
    def expect_every_card_has_non_empty_name(self) -> None:
        names = self._snapshot_card_names()
        assert names, "Expected at least one check card on the demo."
        for i, name in enumerate(names):
            assert name, f"Card {i} has an empty name."

    @allure.step("Every card's Type belongs to the known enum")
    def expect_every_card_type_is_known(self) -> None:
        types = self._snapshot_card_types()
        assert types, "Expected at least one check card on the demo."
        allure.attach(
            "\n".join(t if t is not None else "(unresolved)" for t in types),
            name="card_types.txt",
            attachment_type=allure.attachment_type.TEXT,
        )
        for i, type_ in enumerate(types):
            assert type_ is not None, (
                f"Card {i}: could not determine Check Type from card text."
            )

    # ------------------------------------------------------------------
    # Search actions + filter-consistency invariants (§3.2, §3.7)
    # ------------------------------------------------------------------

    @allure.step("Search {term} in the Checks filter box")
    def search(self, term: str) -> None:
        self._search_input.fill(term)

    @allure.step("Clear the search box")
    def clear_search(self) -> None:
        self._search_input.fill("")

    @allure.step("The Checks grid has {count} visible card(s)")
    def expect_card_count(self, count: int) -> None:
        expect(self._cards).to_have_count(count)

    @allure.step("Every visible card contains {term} somewhere in its text")
    def expect_all_visible_cards_contain(self, term: str) -> None:
        expect(self._cards.first).to_be_visible()
        expect(
            self._cards.filter(has_not_text=re.compile(term, re.IGNORECASE))
        ).to_have_count(0)

    # ------------------------------------------------------------------
    # Navigation invariants (§3.5)
    # ------------------------------------------------------------------

    @allure.step("SM sub-nav exposes Checks, Probes, Alerts (Legacy), Config entries")
    def expect_sm_nav_entries_visible(self) -> None:
        for entry in self._SM_NAV_ENTRIES:
            expect(
                self._page.get_by_test_id(self._NAV_MENU_ITEM_TESTID)
                .filter(has_text=re.compile(rf"^\s*{re.escape(entry)}\s*$"))
                .first
            ).to_be_visible()
