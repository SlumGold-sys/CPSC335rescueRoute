#fifo.py

def find_first_feasible_match(donation, recipients_dict, volunteers_list):
    
    for recipient_id, recipient in recipients_dict.items():
        
        # Skip incompatible recipients
        if donation["food type"] not in recipient["accepted food types"]:
            continue
            
        if recipient["capacity"] < donation["quantity"]:
            continue
            
        for volunteer in volunteers_list:
            if volunteer["vehicle capacity"] < donation["quantity"]:
                continue

            # Deduct capacities instantly inside the nested loop
            recipient["capacity"] -= donation["quantity"]
            volunteer["vehicle capacity"] -= donation["quantity"]

            return {"recipient_id": recipient_id, "volunteer_id": volunteer["volunteer_id"]}
            
    return None


def run_fifo_baseline(donations_dict, recipients_dict, volunteers_list):
  
    assignment_history = []
    
    for donation in donations_dict.values():
        # Pass the dictionaries down into the matcher
        match = find_first_feasible_match(donation, recipients_dict, volunteers_list)
        
        if match:
          
            msg = f"Match found for donation {donation['donation_id']}: Recipient {match['recipient_id']}, Volunteer {match['volunteer_id']}"
            print(msg)
            assignment_history.append(msg)
          
        else:
          
            msg = f"No feasible match found for donation {donation['donation_id']}."
            print(msg)
            assignment_history.append(msg)

    return assignment_history
