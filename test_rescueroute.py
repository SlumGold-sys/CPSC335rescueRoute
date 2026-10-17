import json

from matching import check_match
from fifo import run_fifo_baseline
from greedy import run_greedy

from validation import (
    load_and_validate_data,
    donations_dict,
    seen_ids
)

def test_normal_compatible_match():

    donation = {
        "donation_id": "D1",
        "food_type": "produce",
        "quantity": 10,
        "expiry": 60,
        "pickup_area": "Downtown",
        "ready_time": 500
    }
    recipient = {
        "recipient_id": "R1",
        "accepted_food_types": {"produce"},
        "capacity": 20,
        "area_location": "Downtown",
        "closing_time": 1000
    }

    volunteer = {
        "volunteer_id": "V1",
        "vehicle_capacity": 20,
        "area_location": "Downtown",
        "availability": [0, 1000],
        "maximum_pickups": 2
    }

    result, reason = check_match(donation, recipient, volunteer)

    assert result == True


def test_duplicate_donation_id(tmp_path):

    data = [
        {
            "donation_id": "D1",
            "donor_name": "Store A",
            "food_type": "produce",
            "quantity": 10,
            "expiry": 60,
            "pickup_area": "Downtown",
            "ready_time": 500
        },
        {
            "donation_id": "D1",
            "donor_name": "Store B",
            "food_type": "produce",
            "quantity": 20,
            "expiry": 90,
            "pickup_area": "Downtown",
            "ready_time": 500
        }
    ]

    file_path = tmp_path / "donations.json"

    with open(file_path, "w") as file:
        json.dump(data, file)

    donations_dict.clear()
    seen_ids.clear()

    load_and_validate_data(file_path, "donation")

    assert len(donations_dict) == 1


def test_expired_donation():

    donation = {
        "donation_id": "D2",
        "food_type": "produce",
        "quantity": 10,
        "expiry": 0,
        "pickup_area": "Downtown",
        "ready_time": 500
    }
    recipient = {
        "recipient_id": "R1",
        "accepted_food_types": {"produce"},
        "capacity": 20,
        "area_location": "Downtown",
        "closing_time": 1000
    }
    volunteer = {
        "volunteer_id": "V1",
        "vehicle_capacity": 20,
        "area_location": "Downtown",
        "availability": [0, 1000],
        "maximum_pickups": 2
    }

    result, reason = check_match(donation, recipient, volunteer)

    assert result == False


def test_no_compatible_food_type():

    donation = {
        "donation_id": "D3",
        "food_type": "dairy",
        "quantity": 10,
        "expiry": 60,
        "pickup_area": "Downtown",
        "ready_time": 500
    }
    recipient = {
        "recipient_id": "R1",
        "accepted_food_types": {"produce"},
        "capacity": 20,
        "area_location": "Downtown",
        "closing_time": 1000
    }

    volunteer = {
        "volunteer_id": "V1",
        "vehicle_capacity": 20,
        "area_location": "Downtown",
        "availability": [0, 1000],
        "maximum_pickups": 2
    }

    result, reason = check_match(donation, recipient, volunteer)

    assert result == False


def test_insufficient_recipient_capacity():

    donation = {
        "donation_id": "D4",
        "food_type": "produce",
        "quantity": 50,
        "expiry": 60,
        "pickup_area": "Downtown",
        "ready_time": 500
    }

    recipient = {
        "recipient_id": "R1",
        "accepted_food_types": {"produce"},
        "capacity": 20,
        "area_location": "Downtown",
        "closing_time": 1000
    }

    volunteer = {
        "volunteer_id": "V1",
        "vehicle_capacity": 100,
        "area_location": "Downtown",
        "availability": [0, 1000],
        "maximum_pickups": 2
    }

    result, reason = check_match(donation, recipient, volunteer)

    assert result == False


def test_no_available_volunteer_capacity():

    donation = {
        "donation_id": "D5",
        "food_type": "produce",
        "quantity": 30,
        "expiry": 60,
        "pickup_area": "Downtown",
        "ready_time": 500
    }
    recipient = {
        "recipient_id": "R1",
        "accepted_food_types": {"produce"},
        "capacity": 100,
        "area_location": "Downtown",
        "closing_time": 1000
    }

    volunteer = {
        "volunteer_id": "V1",
        "vehicle_capacity": 10,
        "area_location": "Downtown",
        "availability": [0, 1000],
        "maximum_pickups": 2
    }

    result, reason = check_match(donation, recipient, volunteer)

    assert result == False


def test_two_donations_compete_for_capacity():

    donations = [
        {
            "donation_id": "D1",
            "food_type": "produce",
            "quantity": 30,
            "expiry": 100,
            "pickup_area": "Downtown",
            "ready_time": 500
        },
        {
            "donation_id": "D2",
            "food_type": "produce",
            "quantity": 30,
            "expiry": 50,
            "pickup_area": "Downtown",
            "ready_time": 500
        }
    ]

    recipients = [
        {
            "recipient_id": "R1",
            "organization_name": "Shelter",
            "accepted_food_types": {"produce"},
            "capacity": 30,
            "area_location": "Downtown",
            "closing_time": 1000
        }
    ]
    volunteers = [
        {
            "volunteer_id": "V1",
            "vehicle_capacity": 100,
            "area_location": "Downtown",
            "availability": [0, 1000],
            "maximum_pickups": 3
        }
    ]

    history = run_fifo_baseline(donations, recipients, volunteers)

    assert history[0]["status"] == "assigned"
    assert history[1]["status"] == "unassigned"


def test_empty_input():

    donations = []
    recipients = []
    volunteers = []

    history = run_fifo_baseline(donations, recipients, volunteers)

    assert history == []

def test_fifo_and_greedy_different_results():

    donations = [
        {
            "donation_id": "D1",
            "food_type": "produce",
            "quantity": 30,
            "expiry": 120,
            "pickup_area": "Downtown",
            "ready_time": 500
        },
        {
            "donation_id": "D2",
            "food_type": "produce",
            "quantity": 30,
            "expiry": 30,
            "pickup_area": "Downtown",
            "ready_time": 500
        }
    ]

    recipients = [
        {
            "recipient_id": "R1",
            "organization_name": "Shelter",
            "accepted_food_types": {"produce"},
            "capacity": 30,
            "area_location": "Downtown",
            "closing_time": 1000
        }
    ]

    volunteers = [
        {
            "volunteer_id": "V1",
            "vehicle_capacity": 100,
            "area_location": "Downtown",
            "availability": [0, 1000],
            "maximum_pickups": 3
        }
    ]

    fifo_history = run_fifo_baseline(
        donations,
        recipients,
        volunteers
    )

    greedy_history = run_greedy(
        donations,
        recipients,
        volunteers
    )

    assert fifo_history[0]["donation_id"] == "D1"
    assert fifo_history[0]["status"] == "assigned"

    assert greedy_history[0]["donation_id"] == "D2"
    assert greedy_history[0]["status"] == "assigned"


def test_fairness_starvation_deferral():

    donations = [
        {
            "donation_id": "D1",
            "food_type": "produce",
            "quantity": 10,
            "expiry": 150,
            "pickup_area": "Downtown",
            "ready_time": 400
        },
        {
            "donation_id": "D2",
            "food_type": "produce",
            "quantity": 10,
            "expiry": 30,
            "pickup_area": "Downtown",
            "ready_time": 500
        }
    ]

    recipients = [
        {
            "recipient_id": "R1",
            "organization_name": "Shelter",
            "accepted_food_types": {"produce"},
            "capacity": 30,
            "area_location": "Downtown",
            "closing_time": 1000
        }
    ]
    volunteers = [
        {
            "volunteer_id": "V1",
            "vehicle_capacity": 30,
            "area_location": "Downtown",
            "availability": [0, 1000],
            "maximum_pickups": 3
        }
    ]

    history = run_greedy(
        donations,
        recipients,
        volunteers
    )

    assert history[0]["donation_id"] == "D2"
    assert history[1]["donation_id"] == "D1"