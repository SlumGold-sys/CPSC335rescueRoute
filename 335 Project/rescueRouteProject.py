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
            seen_ids.add(record_id)

            if entity_type == "donation" and (not isinstance(record.get("quantity"), int) or record.get("quantity") <= 0):
                print(f"Warning: Invalid quantity for {record_id}. Skipping this record.")
                continue
            if entity_type == "recipient" and (not isinstance(record.get("capacity"), int) or record.get("capacity") < 0):
                print(f"Warning: Invalid capacity for {record_id}. Skipping this record.")
                continue

            if entity_type == "donation":
                donations_dict[record_id] = record
            
            elif entity_type == "recipient":
                record["accepted food types"] = set(record.get("accepted food types", []))
                recipients_dict[record_id] = record

            elif entity_type == "volunteer":
                volunteers_list.append(record)

    except FileNotFoundError:
        print(f"File {file_path} not found. Starting with empty data.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Starting with empty data.")


def main():
    load_and_validate_data('donations.json', 'donation')
    load_and_validate_data('recipients.json', 'recipient')
    load_and_validate_data('volunteers.json', 'volunteer')

    print("Donations:", donations_dict)
    print("Recipients:", recipients_dict)
    print("Volunteers:", volunteers_list)   

    return 0
