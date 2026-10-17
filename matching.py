"""Shared feasibility checks for RescueRoute's FIFO and greedy schedulers.

All times are simulated minutes since midnight. ``expiry`` means minutes of
remaining shelf life from ``ready_time``; no driving time is modeled. Matching
is non-mutating: schedulers reserve resources only after choosing a match.
"""


def _value(record, *names, default=None):
    """Read canonical JSON keys while tolerating early prototype spellings."""
    for name in names:
        if name in record:
            return record[name]
    return default


def _same_area(left, right):
    return isinstance(left, str) and isinstance(right, str) and left.strip().casefold() == right.strip().casefold()


def _volunteer_available(volunteer, scheduled_time):
    """Support boolean, a [start, end] window, or start/end keys.

    If availability is unspecified, no availability can be verified, so reject.
    """
    availability = _value(volunteer, "availability", "available")
    if isinstance(availability, bool):
        return availability
    if isinstance(availability, (list, tuple)) and len(availability) == 2:
        start, end = availability
        return all(isinstance(t, (int, float)) and not isinstance(t, bool) for t in (start, end)) and start <= scheduled_time <= end
    if isinstance(availability, dict):
        start = _value(availability, "start", "start_time")
        end = _value(availability, "end", "end_time")
        return isinstance(start, (int, float)) and isinstance(end, (int, float)) and start <= scheduled_time <= end
    start = _value(volunteer, "available_from", "start_time")
    end = _value(volunteer, "available_until", "end_time")
    return isinstance(start, (int, float)) and isinstance(end, (int, float)) and start <= scheduled_time <= end


def check_match(donation, recipient, volunteer, *, recipient_remaining=None,
                volunteer_remaining=None, volunteer_pickups=0, scheduled_time=None):
    """Return (is_feasible, explanation) for a specific triple.

    ``volunteer_pickups`` is the number already scheduled for this volunteer.
    The optional remaining values allow schedulers to track reserved capacity
    without changing the original data. A full donation is never split.
    """
    donation_id = _value(donation, "donation_id", default="unknown")
    food = _value(donation, "food_type", "food type")
    quantity = _value(donation, "quantity")
    ready = _value(donation, "ready_time", "ready time")
    shelf_life = _value(donation, "expiry", "remaining_shelf_life")
    when = ready if scheduled_time is None else scheduled_time
    if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity <= 0:
        return False, "Donation has an invalid quantity."
    if not isinstance(ready, (int, float)) or not isinstance(shelf_life, (int, float)) or shelf_life <= 0:
        return False, "Donation is expired or has invalid timing information."
    if not isinstance(when, (int, float)) or when < ready or when >= ready + shelf_life:
        return False, "Pickup cannot occur within the donation's remaining shelf life."

    accepted = _value(recipient, "accepted_food_types", "accepted food types", default=[])
    if food not in accepted:
        return False, f"Recipient does not accept {food}."
    if not _same_area(_value(donation, "pickup_area", "pickup area"),
                      _value(recipient, "area_location", "area/location", "area")):
        return False, "Recipient is outside the donation's pickup area (no travel model is available)."
    closing = _value(recipient, "closing_time", "closing time")
    if not isinstance(closing, (int, float)) or when > closing:
        return False, "Recipient closes before the scheduled pickup time."
    capacity = _value(recipient, "capacity") if recipient_remaining is None else recipient_remaining
    if not isinstance(capacity, (int, float)) or capacity < quantity:
        return False, "Recipient does not have enough remaining capacity."

    if not _same_area(_value(donation, "pickup_area", "pickup area"),
                      _value(volunteer, "area_location", "area/location", "area")):
        return False, "Volunteer is outside the donation's pickup area (no travel model is available)."

    if not _volunteer_available(volunteer, when):
        return False, "Volunteer is unavailable at the scheduled pickup time."
    capacity = _value(volunteer, "vehicle_capacity", "vehicle capacity") if volunteer_remaining is None else volunteer_remaining
    if not isinstance(capacity, (int, float)) or capacity < quantity:
        return False, "Volunteer does not have enough remaining vehicle capacity."
    limit = _value(volunteer, "max_pickups", "maximum_pickups", "maximum pickups")
    if not isinstance(limit, int) or isinstance(limit, bool) or volunteer_pickups >= limit:
        return False, "Volunteer has reached the maximum pickup limit (or it is missing)."

    return True, (f"Donation {donation_id} can be picked up at minute {when}: "
                  f"food type {food} is accepted, recipient and volunteer are in the pickup area, "
                  f"the recipient is open, {quantity} units fit both capacities, "
                  f"and volunteer availability and pickup limit permit the assignment. "
                  f"Remaining shelf life is {shelf_life} minutes.")


def find_feasible_matches(donation, recipients, volunteers, *, recipient_remaining=None,
                          volunteer_remaining=None, volunteer_pickups=None, scheduled_time=None):
    """Find feasible choices in input order; return (matches, rejection_reasons).

    Recipients can be an ID-keyed dict or list; volunteers can be a list or dict.
    Each match includes recipient_id, volunteer_id, scheduled_time and reason.
    """
    recipients_iter = recipients.values() if isinstance(recipients, dict) else recipients
    volunteers_iter = volunteers.values() if isinstance(volunteers, dict) else volunteers
    volunteers_iter = list(volunteers_iter)
    recipient_remaining = recipient_remaining or {}
    volunteer_remaining = volunteer_remaining or {}
    volunteer_pickups = volunteer_pickups or {}
    matches = []
    reasons = []
    when = _value(donation, "ready_time", "ready time") if scheduled_time is None else scheduled_time
    for recipient in recipients_iter:
        rid = _value(recipient, "recipient_id")
        for volunteer in volunteers_iter:
            vid = _value(volunteer, "volunteer_id")
            ok, reason = check_match(
                donation, recipient, volunteer,
                recipient_remaining=recipient_remaining.get(rid),
                volunteer_remaining=volunteer_remaining.get(vid),
                volunteer_pickups=volunteer_pickups.get(vid, 0),
                scheduled_time=when,
            )
            if ok:
                matches.append({"recipient_id": rid, "volunteer_id": vid,
                                "scheduled_time": when, "reason": reason})
            elif reason not in reasons:
                reasons.append(reason)
    if not matches and not reasons:
        reasons.append("No recipients or volunteers are available to evaluate.")
    return matches, reasons


def first_feasible_match(donation, recipients, volunteers, **kwargs):
    """Return the first feasible match or None, with no resource mutation."""
    matches, _ = find_feasible_matches(donation, recipients, volunteers, **kwargs)
    return matches[0] if matches else None
