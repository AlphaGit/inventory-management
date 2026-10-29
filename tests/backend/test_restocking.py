"""
Tests for restocking API endpoints.
"""
import json
from datetime import datetime, timedelta

import pytest

from main import allocate_budget


def place_order(client, budget, lines):
    """Submit a restocking order with (sku, quantity) pairs."""
    return client.post(
        "/api/restocking/orders",
        json={"budget": budget, "lines": [{"sku": s, "quantity": q} for s, q in lines]},
    )


class TestRestockRecommendations:
    """Test suite for the restocking recommendation endpoint."""

    def test_get_recommendations_default_budget(self, client):
        """Test that omitting the budget uses the default of half the max."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        for field in ["budget", "max_budget", "default_budget", "lines", "total", "remaining", "unpriced"]:
            assert field in data
        assert data["budget"] == data["default_budget"]
        assert data["default_budget"] == data["max_budget"] // 2 // 500 * 500

    def test_recommendation_line_structure(self, client):
        """Test that recommendation lines have proper structure."""
        data = client.get("/api/restocking/recommendations").json()
        assert len(data["lines"]) > 0

        for line in data["lines"]:
            for field in ["sku", "name", "trend", "on_hand", "need", "unit_cost",
                          "lead_time_days", "recommended_qty", "line_total"]:
                assert field in line
            assert isinstance(line["recommended_qty"], int)
            assert 0 <= line["recommended_qty"] <= line["need"]
            assert line["unit_cost"] is not None

    def test_max_budget_covers_full_need(self, client):
        """Test that max_budget is the full-need cost rounded up to the next 1,000."""
        data = client.get("/api/restocking/recommendations").json()
        full_cost = sum(l["unit_cost"] * l["need"] for l in data["lines"])

        assert data["max_budget"] % 1000 == 0
        assert full_cost <= data["max_budget"] < full_cost + 1000

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget gives zero quantities."""
        data = client.get("/api/restocking/recommendations?budget=0").json()

        assert data["total"] == 0
        assert all(l["recommended_qty"] == 0 for l in data["lines"])

    def test_max_budget_recommends_full_need(self, client):
        """Test that the max budget funds every line's full need."""
        max_budget = client.get("/api/restocking/recommendations").json()["max_budget"]
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()

        for line in data["lines"]:
            assert line["recommended_qty"] == line["need"]

    def test_recommendation_totals_calculation(self, client):
        """Test that total and remaining match the lines and stay within budget."""
        data = client.get("/api/restocking/recommendations?budget=20000").json()

        line_sum = sum(l["line_total"] for l in data["lines"])
        assert abs(data["total"] - line_sum) < 0.01
        assert data["total"] <= 20000
        assert abs(data["remaining"] - (20000 - data["total"])) < 0.01

        for line in data["lines"]:
            assert abs(line["line_total"] - line["recommended_qty"] * line["unit_cost"]) < 0.01

    def test_recommendation_priority_order(self, client):
        """Test that lines are ranked by trend, then by growth descending."""
        lines = client.get("/api/restocking/recommendations").json()["lines"]
        rank = {"increasing": 0, "stable": 1, "decreasing": 2}

        keys = [(rank[l["trend"]], -l["growth_pct"]) for l in lines]
        assert keys == sorted(keys)

    def test_partial_budget_funds_highest_priority_first(self, client):
        """Test that a short budget funds the top line fully and later lines less."""
        data = client.get("/api/restocking/recommendations?budget=15000").json()
        lines = data["lines"]

        assert lines[0]["sku"] == "WDG-001"
        assert lines[0]["recommended_qty"] == lines[0]["need"]
        assert any(0 < l["recommended_qty"] < l["need"] for l in lines)
        assert lines[-1]["trend"] == "decreasing"
        assert lines[-1]["recommended_qty"] == 0

    def test_need_subtracts_on_hand_stock(self, client):
        """Test that need is forecast minus on-hand, never below zero."""
        lines = client.get("/api/restocking/recommendations").json()["lines"]
        psu = next(l for l in lines if l["sku"] == "PSU-501")

        # 420 on hand in San Francisco covers the 252 forecast
        assert psu["on_hand"] == 420
        assert psu["need"] == 0

        for line in lines:
            assert line["need"] == max(0, line["forecasted_demand"] - line["on_hand"])

    def test_unpriced_items_excluded(self, client):
        """Test that items without a unit cost are listed separately."""
        data = client.get("/api/restocking/recommendations").json()

        unpriced_skus = {u["sku"] for u in data["unpriced"]}
        assert unpriced_skus == {"SNR-420", "CTL-330"}
        assert all(u["unit_cost"] is None for u in data["unpriced"])
        assert not unpriced_skus & {l["sku"] for l in data["lines"]}

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 422."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422


class TestAllocateBudget:
    """Test suite for the greedy allocation helper."""

    def test_leftover_flows_to_cheaper_items(self):
        """Test that budget left after a partial line still funds cheaper lines below it."""
        lines = [
            {"sku": "A", "need": 10, "unit_cost": 100.0},
            {"sku": "B", "need": 10, "unit_cost": 30.0},
        ]
        result = allocate_budget(lines, 250)

        # A gets 2 units ($200); the $50 left buys 1 unit of B
        assert [l["recommended_qty"] for l in result] == [2, 1]

    def test_cent_precision(self):
        """Test that prices with cents do not lose a unit to float rounding."""
        lines = [{"sku": "A", "need": 10, "unit_cost": 24.99}]
        result = allocate_budget(lines, 74.97)

        assert result[0]["recommended_qty"] == 3
        assert result[0]["line_total"] == 74.97


class TestRestockOrders:
    """Test suite for restocking order endpoints."""

    def test_get_restock_orders_empty(self, client):
        """Test that there are no submitted orders initially."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client, restock_store):
        """Test submitting a valid restocking order."""
        response = place_order(client, 10000, [("WDG-001", 100), ("MTR-304", 2)])
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert len(order["items"]) == 2
        assert abs(order["total_cost"] - (100 * 24.99 + 2 * 445.0)) < 0.01

        # Order is persisted to the (temp) file
        saved = json.loads(restock_store.read_text())
        assert saved[0]["order_number"] == "RST-0001"

    def test_restock_order_lead_time_calculation(self, client):
        """Test that lead time is the slowest line and sets expected delivery."""
        order = place_order(client, 10000, [("FLT-405", 10), ("MTR-304", 1)]).json()

        # FLT-405 = 5 days, MTR-304 = 21 days
        assert order["lead_time_days"] == 21
        submitted = datetime.fromisoformat(order["submitted_at"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=21)

    def test_restock_order_ignores_client_unit_cost(self, client):
        """Test that the server prices lines from its own data."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "lines": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01}]},
        )
        assert response.status_code == 201

        item = response.json()["items"][0]
        assert item["unit_cost"] == 24.99
        assert abs(item["line_total"] - 249.9) < 0.01

    def test_restock_order_drops_zero_quantity_lines(self, client):
        """Test that zero-quantity lines are left out of the order."""
        order = place_order(client, 1000, [("WDG-001", 10), ("GSK-203", 0)]).json()
        assert [i["sku"] for i in order["items"]] == ["WDG-001"]

    def test_restock_order_over_budget(self, client):
        """Test that an order above the budget returns 422."""
        response = place_order(client, 100, [("MTR-304", 1)])
        assert response.status_code == 422
        assert "budget" in response.json()["detail"].lower()

    @pytest.mark.parametrize("lines", [
        [("NOPE-999", 1)],
        [("SNR-420", 1)],
        [("WDG-001", 1), ("WDG-001", 2)],
        [("WDG-001", 0)],
        [],
    ], ids=["unknown-sku", "unpriced-sku", "duplicate-sku", "all-zero", "empty"])
    def test_restock_order_invalid_lines(self, client, restock_store, lines):
        """Test that invalid line sets return 422 and write nothing."""
        response = place_order(client, 100000, lines)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert not restock_store.exists()

    def test_restock_order_negative_quantity(self, client):
        """Test that a negative quantity returns 422."""
        response = place_order(client, 1000, [("WDG-001", -1)])
        assert response.status_code == 422

    def test_restock_orders_newest_first(self, client):
        """Test that order numbers increment and the list is newest first."""
        place_order(client, 1000, [("WDG-001", 1)])
        place_order(client, 1000, [("GSK-203", 1)])

        data = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]

    def test_restock_orders_excluded_from_customer_orders(self, client):
        """Test that submitted restock orders do not change customer order data."""
        before = client.get("/api/dashboard/summary").json()
        place_order(client, 1000, [("WDG-001", 1)])
        after = client.get("/api/dashboard/summary").json()

        assert before == after
