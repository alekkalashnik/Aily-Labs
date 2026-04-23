Feature: Grafana Synthetic Monitoring — Checks list structure
  As a viewer of the Synthetic Monitoring app
  I want every check card to expose a well-formed name and Type
  So that downstream data assertions have a reliable surface to read from.

  @P0 @structure @critical
  Scenario: Checks page renders cards with well-formed structure
    Given I open the Checks list page
    Then every card has a non-empty name
    And every card's Type belongs to the known enum

  @P0 @navigation
  Scenario: SM sub-navigation entries are all visible from the Checks page
    Given I open the Checks list page
    Then the SM sub-nav exposes Checks, Probes, Alerts (Legacy) and Config entries
