"""Automated test suite for the RescueRoute surplus food matching planner.

Covers all 10 required testing scenarios from Section 8 of the project brief:
1. Normal matching case with compatible donor, recipient, and volunteer.
2. Duplicate donation ID detection.
3. Expired or nearly expired donation handling.
4. No compatible recipient food type.
5. Insufficient recipient capacity.
6. No available volunteer with enough vehicle capacity.
7. Two donations competing for the same capacity.
8. Empty input files or empty lists.
9. A case where FIFO and greedy strategies produce different results.
10. Fairness / starvation discussion case (deferred donation explanation).
"""

import json
import os
import tempfile
import unittest

import fifo
import greedy
import main
import matching
import validation


class TestRescueRoute(unittest.TestCase):

    def setUp(self):
        """Prepare clean baseline sample entities before each test."""
        self.sample_recipient = {
            "recipient_id": "R-201",
            "organization_name": "Downtown Shelter",
            "accepted_food_types": {"prepared meals", "produce", "dairy"},
            "capacity": 500,
            "area_location": "Downtown",
            "closing_time": 1200,
        }
        self.north_recipient = {
            "recipient_id": "R-202",
            "organization_name": "North Campus Pantry",
            "accepted_food_types": {"produce", "bakery"},
            "capacity": 50,
            "area_location": "North Campus",
            "closing_time": 1020,
        }
        self.sample_volunteer = {
            "volunteer_id": "V-301",
            "vehicle_capacity": 300,
            "area_location": "Downtown",
            "availability": [0, 1200],
            "maximum_pickups": 3,
        }
        self.north_volunteer = {
            "volunteer_id": "V-302",
            "vehicle_capacity": 50,
            "area_location": "North Campus",
            "availability": [0, 1000],
            "maximum_pickups": 3,
        }

    # 1. Normal matching case with compatible donor, recipient, and volunteer
    def test_1_normal_matching_case(self):
        donation = {
            "donation_id": "D-1001",
            "donor_name": "Campus Catering",
            "food_type": "prepared meals",
            "quantity": 40,
            "expiry": 120,
            "pickup_area": "Downtown",
            "ready_time": 480,
        }
        ok, reason = matching.check_match(
            donation, self.sample_recipient, self.sample_volunteer
        )
        self.assertTrue(ok)
        self.assertIn("Donation D-1001 can be picked up at minute 480", reason)

    # 2. Duplicate donation ID
    def test_2_duplicate_donation_id(self):
        duplicate_records = [
            {
                "donation_id": "D-1002",
                "donor name": "Fresh Mart",
                "food type": "produce",
                "quantity": 25,
                "expiry": 100,
                "pickup area": "North Campus",
                "ready time": 500,
            },
            {
                "donation_id": "D-1002",
                "donor name": "Duplicate Mart",
                "food type": "produce",
                "quantity": 20,
                "expiry": 90,
                "pickup area": "North Campus",
                "ready time": 500,
            },
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(duplicate_records, temp_file)
            temp_path = temp_file.name

        try:
            validation.donations_dict.clear()
            validation.seen_ids.clear()
            validation.load_and_validate_data(temp_path, "donation")
            self.assertEqual(len(validation.donations_dict), 1)
            self.assertEqual(
                validation.donations_dict["D-1002"]["donor name"], "Fresh Mart"
            )
        finally:
            os.remove(temp_path)

    # 3. Expired or nearly expired donation
    def test_3_expired_donation(self):
        expired_donation = {
            "donation_id": "D-1004",
            "donor_name": "Expired Eats",
            "food_type": "dairy",
            "quantity": 30,
            "expiry": -10,
            "pickup_area": "Downtown",
            "ready_time": 480,
        }
        ok, reason = matching.check_match(
            expired_donation, self.sample_recipient, self.sample_volunteer
        )
        self.assertFalse(ok)
        self.assertIn("expired", reason.lower())

    # 4. No compatible recipient food type
    def test_4_no_compatible_recipient_food_type(self):
        incompatible_donation = {
            "donation_id": "D-1005",
            "donor_name": "Seafood Co",
            "food_type": "raw oysters",
            "quantity": 15,
            "expiry": 100,
            "pickup_area": "Downtown",
            "ready_time": 540,
        }
        matches, reasons = matching.find_feasible_matches(
            incompatible_donation,
            [self.sample_recipient, self.north_recipient],
            [self.sample_volunteer, self.north_volunteer],
        )
        self.assertEqual(matches, [])
        self.assertTrue(any("does not accept raw oysters" in r for r in reasons))

    # 5. Insufficient recipient capacity
    def test_5_insufficient_recipient_capacity(self):
        oversized_donation = {
            "donation_id": "D-1006",
            "donor_name": "Massive Farm",
            "food_type": "produce",
            "quantity": 5000,
            "expiry": 200,
            "pickup_area": "North Campus",
            "ready_time": 600,
        }
        ok, reason = matching.check_match(
            oversized_donation, self.north_recipient, self.north_volunteer
        )
        self.assertFalse(ok)
        self.assertIn("Recipient does not have enough remaining capacity", reason)

    # 6. No available volunteer with enough vehicle capacity
    def test_6_insufficient_volunteer_vehicle_capacity(self):
        heavy_donation = {
            "donation_id": "D-1007",
            "donor_name": "Big Bakery",
            "food_type": "prepared meals",
            "quantity": 400,
            "expiry": 150,
            "pickup_area": "Downtown",
            "ready_time": 600,
        }
        ok, reason = matching.check_match(
            heavy_donation, self.sample_recipient, self.sample_volunteer
        )
        self.assertFalse(ok)
        self.assertIn(
            "Volunteer does not have enough remaining vehicle capacity", reason
        )

    # 7. Two donations competing for the same capacity
    def test_7_two_donations_competing_for_same_capacity(self):
        competing_donations = [
            {
                "donation_id": "D-1008",
                "donor_name": "Local Farm",
                "food_type": "produce",
                "quantity": 40,
                "expiry": 60,
                "pickup_area": "North Campus",
                "ready_time": 540,
            },
            {
                "donation_id": "D-1009",
                "donor_name": "Campus Bakery",
                "food_type": "bakery",
                "quantity": 30,
                "expiry": 45,
                "pickup_area": "North Campus",
                "ready_time": 540,
            },
        ]
        # North recipient has 50 capacity; 40 + 30 = 70 exceeds capacity
        history = fifo.run_fifo_baseline(
            competing_donations, [self.north_recipient], [self.north_volunteer]
        )
        self.assertEqual(history[0]["donation_id"], "D-1008")
        self.assertEqual(history[0]["status"], "assigned")
        self.assertEqual(history[1]["donation_id"], "D-1009")
        self.assertEqual(history[1]["status"], "unassigned")
        self.assertIn(
            "Recipient does not have enough remaining capacity",
            history[1]["reason"],
        )

    # 8. Empty input files or empty lists
    def test_8_empty_inputs(self):
        fifo_result = fifo.run_fifo_baseline([], [], [])
        greedy_result = greedy.run_greedy([], [], [])
        self.assertEqual(fifo_result, [])
        self.assertEqual(greedy_result, [])

        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as temp_file:
            json.dump([], temp_file)
            temp_path = temp_file.name

        try:
            validation.donations_dict.clear()
            validation.seen_ids.clear()
            validation.load_and_validate_data(temp_path, "donation")
            self.assertEqual(len(validation.donations_dict), 0)
        finally:
            os.remove(temp_path)

    # 9. A case where FIFO and greedy strategies produce different results
    def test_9_fifo_and_greedy_produce_different_results(self):
        donations = [
            {
                "donation_id": "D-1002",
                "donor_name": "Fresh Mart",
                "food_type": "produce",
                "quantity": 25,
                "expiry": 100,
                "pickup_area": "North Campus",
                "ready_time": 500,
            },
            {
                "donation_id": "D-1009",
                "donor_name": "Campus Bakery",
                "food_type": "bakery",
                "quantity": 30,
                "expiry": 45,
                "pickup_area": "North Campus",
                "ready_time": 540,
            },
        ]
        result = main.run_comparison(
            donations,
            [self.north_recipient],
            [self.north_volunteer],
            urgent_threshold=90,
            verbose=False,
        )
        comparison = result["comparison"]
        # FIFO assigns D-1002 (25 units, non-urgent); Greedy assigns D-1009 (30 units, urgent)
        self.assertEqual(comparison["fifo"]["food_quantity_rescued"], 25)
        self.assertEqual(comparison["greedy"]["food_quantity_rescued"], 30)
        self.assertEqual(
            comparison["greedy_minus_fifo"]["food_quantity_rescued"], 5
        )
        self.assertGreater(
            comparison["greedy_minus_fifo"]["urgent_rescue_rate"], 0
        )

    # 10. Fairness or starvation discussion case: explain which donation is deferred and why
    def test_10_fairness_and_starvation_deferral_explanation(self):
        donations = [
            {
                "donation_id": "D-1002",
                "donor_name": "Fresh Mart",
                "food_type": "produce",
                "quantity": 25,
                "expiry": 100,
                "pickup_area": "North Campus",
                "ready_time": 500,
            },
            {
                "donation_id": "D-1009",
                "donor_name": "Campus Bakery",
                "food_type": "bakery",
                "quantity": 30,
                "expiry": 45,
                "pickup_area": "North Campus",
                "ready_time": 540,
            },
        ]
        greedy_history = greedy.run_greedy(
            donations, [self.north_recipient], [self.north_volunteer]
        )
        # D-1009 is processed first due to shorter shelf life (45 < 100)
        self.assertEqual(greedy_history[0]["donation_id"], "D-1009")
        self.assertEqual(greedy_history[0]["status"], "assigned")
        self.assertIn(
            "considered ahead of earlier-arriving donation(s) D-1002",
            greedy_history[0]["reason"],
        )
        # D-1002 was deferred and starved of remaining capacity at R-202 (only 20 left < 25 needed)
        self.assertEqual(greedy_history[1]["donation_id"], "D-1002")
        self.assertEqual(greedy_history[1]["status"], "unassigned")
        self.assertIn(
            "Recipient does not have enough remaining capacity",
            greedy_history[1]["reason"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)