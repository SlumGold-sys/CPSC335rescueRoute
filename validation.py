import json

donations_dict = {}

recipients_dict = {}

volunteers_list = []

seen_ids = set()

def load_and_validate_data(file_path, entity_type):
    global donations_dict, recipients_dict, volunteers_list, seen_ids
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        for record in data:

            if entity_type == "donation":
                record_id = record.get("donation_id")
            elif entity_type == "recipient":
                record_id = record.get("recipient_id")
            elif entity_type == "volunteer":
                record_id = record.get("volunteer_id")
            else:
                continue

            if record_id in seen_ids:   
                print(f"Warning: Duplicate ID {record_id} found in {file_path}. Skipping this record.")
                continue
# 
            if entity_type == "donation" and (not isinstance(record.get("donation_id"), str) or not record.get("donation_id").strip() ):
                            print(f"Warning: Invalid donation ID for {record_id}. Skipping this record.")
                            continue
            if entity_type == "donation" and (not isinstance(record.get("donor_name"), str) or not record.get("donor_name").strip() ):
                                        print(f"Warning: Invalid Donor Name for {record_id}. Skipping this record.")
                                        continue
            if entity_type == "donation" and (not isinstance(record.get("food_type"), str) or not record.get("food_type").strip() ):
                                        print(f"Warning: Invalid Food Type for {record_id}. Skipping this record.")
                                        continue
            if entity_type == "donation" and (not isinstance(record.get("pickup_area"), str) or not record.get("pickup_area").strip() ):
                                                    print(f"Warning: Invalid Pickup Area for {record_id}. Skipping this record.")
                                                    continue
            if entity_type == "donation" and (not isinstance(record.get("ready_time"), int) or record.get("ready_time") < 0): 
                print(f"Warning: Invalid quantity for {record_id}. Skipping this record.")
                continue
            if entity_type == "donation" and (not isinstance(record.get("quantity"), int) or record.get("quantity") <= 0):
                print(f"Warning: Invalid quantity for {record_id}. Skipping this record.")
                continue
            if entity_type == "donation" and (not isinstance(record.get("expiry"), int) or record.get("expiry") <= 0):
                print(f"Warning: Donation is expired for {record_id}. Skipping this record.")
                continue
# 

            
            if entity_type == "recipient" and (not isinstance(record.get("recipient_id"), str) or not record.get("recipient_id").strip() ):
                                        print(f"Warning: Invalid recipient ID for {record_id}. Skipping this record.")
                                        continue
            if entity_type == "recipient" and (not isinstance(record.get("organization_name"), str) or not record.get("recipient_id").strip() ):
                            print(f"Warning: Invalid Organization Name for {record_id}. Skipping this record.")
                            continue
            # if entity_type == "recipient" and (not isinstance(record.get("accepted_food_types"), list? ) or not record.get("recipient_id").strip() ):
            #                             print(f"Warning: Invalid Organization Name for {record_id}. Skipping this record.")
            #                             continue
    # "accepted_food_types": [
    #   "prepared meals",
    #   "produce",
    #   "dairy"
    # ],
    
            if entity_type == "recipient" and (not isinstance(record.get("capacity"), int) or record.get("capacity") < 0):
                print(f"Warning: Invalid capacity for {record_id}. Skipping this record.")
                continue
            if entity_type == "recipient" and (not isinstance(record.get("area_location"), str) or not record.get("area_location").strip()):
                            print(f"Warning: Invalid area/location for {record_id}. Skipping this record.")
                            continue
            if entity_type == "recipient" and (not isinstance(record.get("closing_time"), int) or record.get("capacity") < 0):
                print(f"Warning: Invalid Closing Time for {record_id}. Skipping this record.")
                continue


            
            seen_ids.add(record_id)    
            
            if entity_type == "donation":
                donations_dict[record_id] = record
            
            elif entity_type == "recipient":
                record["accepted_food_types"] = set(record.get("accepted_food_types", []))
                recipients_dict[record_id] = record

            elif entity_type == "volunteer":
                volunteers_list.append(record)

    except FileNotFoundError:
        print(f"File {file_path} not found. Starting with empty data.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Starting with empty data.")