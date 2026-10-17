# RescueRoute

## 1. Project Overview / Purpose

RescueRoute is a Python application designed to simulate the coordination of time-sensitive surplus-food donations with compatible recipient organizations and volunteer drivers.

It is designed to handle each case using two different approaches:

- FIFO
- Greedy urgency-first

The purpose is to determine how different handling methods affect the number of successful donations, rescued food, and urgent donation cases.

Restaurants, campus events, grocery stores, and other organizations may have surplus food that must be picked up before it expires.

Recipients, such as shelters and food pantries, may have different conditions when deciding whether to accept donations, including:

- Available capacity
- Location
- Accepted food types
- Operating hours

Volunteers may also differ in:

- Location
- Vehicle capacity
- Availability
- Maximum pickups

RescueRoute checks these constraints before assigning a donation.

---

## 2. How to Run

**In process**


## 3. Project Structure / Architecture

main.py
validation.py
matching.py
fifo.py
greedy.py
metrics.py
test_rescueroute.py

data/
tests/
### File Responsibilities

**main.py**  
Runs the program and connects the different components.

**validation.py**  
Loads and validates donation, recipient, and volunteer data.

**matching.py**  
Determines whether a donation can be matched with a recipient and volunteer.

**fifo.py**  
Processes donations in arrival order.

**greedy.py**  
Processes donations using the urgency-first priority rule.

**metrics.py**  
Calculates performance statistics and compares FIFO and Greedy.

**test_rescueroute.py** 
Tests program based on varying constraints and values
## 4. Input Data Model

The program loads data from JSON files.

### Donation Fields

- `donation_id`
- `donor_name`
- `food_type`
- `quantity`
- `expiry`
- `pickup_area`
- `ready_time`

### Recipient Fields

- `recipient_id`
- `organization_name`
- `accepted_food_types`
- `capacity`
- `area/location`
- `closing_time`

### Volunteer Fields

- `volunteer_id`
- `vehicle_capacity`
- `area_location`
- `availability`
- `maximum_pickups`

---

## 5. Validation and Matching Rules

Before evaluating donations, all input records are validated for:

- Duplicate IDs
- Missing IDs
- Invalid quantities
- Invalid capacities
- Invalid expiration values
- Invalid ready times
- Missing food types
- Missing locations

Invalid records are skipped and a warning is displayed.

Input records are also checked for matching, since a donation can only be assigned if a compatible recipient and volunteer are available.

The matching process checks:

- Whether the recipient accepts the food type
- Whether the recipient has sufficient remaining capacity
- Whether the volunteer has sufficient vehicle capacity
- Whether the volunteer is available
- Whether the volunteer has exceeded the maximum pickup limit
- Whether location requirements are satisfied
- Whether time requirements are satisfied

If there are no valid combinations, the donation is marked as unassigned and an explanation is provided.

---

## 6. FIFO Explanation

The FIFO baseline processes donations in their original arrival order.

For each donation:

1. Donations are examined in the order they arrive.
2. The program searches for a compatible recipient.
3. The program searches for a compatible volunteer.
4. The first feasible combination is assigned.
5. If no feasible assignment exists, the donation is marked as unassigned.

FIFO does not prioritize urgency. It preserves the original arrival order.

---

## 7. Exact Greedy Rule

The Greedy strategy prioritizes urgent donations.

Our Greedy priority rule is:

1. Donations with the shortest remaining shelf life (expiry) are processed first.
2. If donations have the same expiry, the donation with the larger quantity is processed first.
3. If both expiry and quantity are equal, the donation with the earlier ready time is processed first.
4. If all previous rules are equal, the donations are processed in their original order.


## 8. Data Structures Used

This program uses several data structures.

### Dictionaries

Used for fast lookup of donations and recipients by ID.

### Sets

Used for detecting duplicate IDs and checking accepted food-type membership.

### Lists

Used for volunteers, assignment history, and processing order.

### Sorted List

Used by the Greedy scheduling function to sort donations according to the priority rules.



## 9. Complexity Analysis

- D = number of donations
- R = number of recipients
- V = number of volunteers
Every donation has complexity O(R*V) because of matching work done between Recipient and Volunteer in matching function
- FIFO = O(DRV)
FIFO matches Recipient and Volunteer for every Donation
- Greedy = O(D log D + D^2 + DRV)
Greedy has to first sort which causes O(D log D), then it also has to match like FIFO - O(DRV),
then it scans the orderd donation list to output an explanation for each donation wwhich add O(D^2)



## 10. Metrics

**In process**

---

## 11. Testing and Edge Cases

**In process**

What was tested exactly?

--

## 12. Fairness / Starvation Discussion

**In process**

-

## 13. Limitations

**In process**

-

## 14. Team Contributions

### Team Member 1
-

### Team Member 2
-

### Team Member 3
-