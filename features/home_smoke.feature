Feature: Grafana Synthetic Monitoring — Home smoke
  As a viewer of the public Grafana Synthetic Monitoring demo
  I want the Home dashboard shell to render reliably
  So that the app is confirmed reachable before any other test runs.

  @smoke @P0 @blocker
  Scenario: Home page loads with the expected Grafana shell
    Given I open the Synthetic Monitoring home page
    Then the page title mentions "Grafana"
    And the Grafana app shell is visible
    And no unexpected console errors are recorded
