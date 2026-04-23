Feature: Grafana Synthetic Monitoring — Checks search filter
  As a viewer of the Synthetic Monitoring app
  I want the search box to narrow the card grid self-consistently
  So that I trust filters and can recover the original view by clearing them.

  @P0 @filter @idempotence @critical
  Scenario: Search narrows cards and clearing restores the count
    Given I open the Checks list page
    And I note the current card count
    When I search for "sm-check"
    Then every visible card contains the search term
    And the visible card count matches the expected number
    When I clear the search
    Then the visible card count equals the initial count
