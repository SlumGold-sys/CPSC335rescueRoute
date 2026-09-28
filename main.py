from validation import (
    load_and_validate_data,
    donations_dict,
    recipients_dict,
    volunteers_list
)

def main():
    load_and_validate_data('tests/donations.json', 'donation')
    load_and_validate_data('tests/recipients.json', 'recipient')
    load_and_validate_data('tests/volunteers.json', 'volunteer')

    print("Donations:", donations_dict)
    print("Recipients:", recipients_dict)
    print("Volunteers:", volunteers_list)   

    return 0



# 