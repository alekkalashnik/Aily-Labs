"""Home page of the Grafana Synthetic Monitoring plugin."""

from __future__ import annotations

import allure
from playwright.sync_api import expect

from .base_page import BasePage


class HomePage(BasePage):
    URL = "/a/grafana-synthetic-monitoring-app/home"

    @allure.step("Home page landmarks are visible")
    def expect_loaded(self) -> None:
        expect(self._synthetics_breadcrumb).to_be_visible()
