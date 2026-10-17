import json

donations_dict = {}
recipients_dict = {}
volunteers_list = []
seen_ids = set()


def _get_field(record, *keys):
    """Return the first matching key's value (supports space and underscore keys)."""
    for key in keys:
        if key in record:
            return record[key]
    return None


def load_and_validate_data(file_path, entity_type):
    global donations_dict, recipients_dict, volunteers_list, seen_ids
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        for record in data:
            # 1. Extract ID based on entity type
            if entity_type == "donation":
                record_id = record.get("donation_id")
            elif entity_type == "recipient":
                record_id = record.get("recipient_id")
            elif entity_type == "volunteer":
                record_id = record.get("volunteer_id")
            else:
                continue

            if not record_id or not isinstance(record_id, str):
                print(f"Warning: Missing or invalid ID in {file_path}. Skipping.")
                continue

            # 2. Duplicate ID Check
            if record_id in seen_ids:
                print(f"Warning: Duplicate ID {record_id} found in {file_path}. Skipping this record.")
                continue
            seen_ids.add(record_id)

            # 3. Validate and Normalize Donations
            if entity_type == "donation":
                qty = _get_field(record, "quantity")
                expiry = _get_field(record, "expiry", "remaining_shelf_life")
                ready = _get_field(record, "ready_time", "ready time")
                food_type = _get_field(record, "food_type", "food type")
                pickup_area = _get_field(record, "pickup_area", "pickup area")
                donor_name = _get_field(record, "donor_name", "donor name")

                if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
                    print(f"Warning: Invalid quantity for {record_id}. Skipping.")
                    continue
                if not isinstance(expiry, (int, float)) or isinstance(expiry, bool):
                    print(f"Warning: Invalid expiry time for {record_id}. Skipping.")
                    continue
                if not isinstance(ready, (int, float)) or isinstance(ready, bool) or ready < 0:
                    print(f"Warning: Invalid ready time for {record_id}. Skipping.")
                    continue
                if not food_type or not pickup_area:
                    print(f"Warning: Missing food type or pickup area for {record_id}. Skipping.")
                    continue

                # Standardize keys for fifo.py, greedy.py, and matching.py
                record["donor_name"] = donor_name
                record["food_type"] = food_type
                record["pickup_area"] = pickup_area
                record["ready_time"] = ready
                donations_dict[record_id] = record

            # 4. Validate and Normalize Recipients
            elif entity_type == "recipient":
                cap = _get_field(record, "capacity")
                closing = _get_field(record, "closing_time", "closing time")
                org_name = _get_field(record, "organization_name", "organization name")
                area = _get_field(record, "area_location", "area/location", "area")
                accepted = _get_field(record, "accepted_food_types", "accepted food types")

                if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
                    print(f"Warning: Invalid capacity for {record_id}. Skipping.")
                    continue
                if not isinstance(closing, (int, float)) or isinstance(closing, bool) or closing < 0:
                    print(f"Warning: Invalid closing time for {record_id}. Skipping.")
                    continue
                if not accepted or not area:
                    print(f"Warning: Missing accepted food types or area for {record_id}. Skipping.")
                    continue

                accepted_set = set(accepted)
                record["accepted food types"] = accepted_set
                record["accepted_food_types"] = accepted_set
                record["organization_name"] = org_name or record_id
                record["closing_time"] = closing
                record["area_location"] = area
                recipients_dict[record_id] = record

            # 5. Validate and Normalize Volunteers
            elif entity_type == "volunteer":
                v_cap = _get_field(record, "vehicle_capacity", "vehicle capacity")
                avail = _get_field(record, "availability", "available")
                max_pickups = _get_field(record, "maximum_pickups", "max_pickups", "maximum pickups")
                area = _get_field(record, "area_location", "area/location", "area")

                if not isinstance(v_cap, int) or isinstance(v_cap, bool) or v_cap <= 0:
                    print(f"Warning: Invalid vehicle capacity for {record_id}. Skipping.")
                    continue
                if not isinstance(max_pickups, int) or isinstance(max_pickups, bool) or max_pickups <= 0:
                    print(f"Warning: Invalid maximum pickups for {record_id}. Skipping.")
                    continue
                if avail is None or (isinstance(avail, (int, float)) and not isinstance(avail, bool) and avail < 0):
                    print(f"Warning: Invalid availability for {record_id}. Skipping.")
                    continue

                # Convert single integer availability (e.g., 1200) into [0, 1200] window for matching.py
                if isinstance(avail, (int, float)) and not isinstance(avail, bool):
                    record["availability"] = [0, avail]

                record["vehicle_capacity"] = v_cap
                record["maximum_pickups"] = max_pickups
                record["max_pickups"] = max_pickups
                record["area_location"] = area
                volunteers_list.append(record)

    except FileNotFoundError:
        print(f"File {file_path} not found. Starting with empty data.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Starting with empty data.")
