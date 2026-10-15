"""FIFO baseline for RescueRoute's simulated donation scheduling.

Donations are considered in the order provided (the validated JSON preserves
arrival order). This module uses matching.py's shared rules, so FIFO and greedy
can be compared against independent, unchanged input datasets.
"""

from matching import find_feasible_matches
from metrics import calculate_metrics


def _as_list(records):
    """Support both ID-keyed dictionaries and record lists."""
    return list(records.values()) if isinstance(records, dict) else list(records)


def find_first_feasible_match(donation, recipients_dict, volunteers_list, *,
                              recipient_remaining=None, volunteer_remaining=None,
                              volunteer_pickups=None):
    """Compatibility wrapper for the prototype's original public function.

    Unlike the old implementation, this does NOT mutate resource capacities.
    Use run_fifo_baseline to reserve capacity across several donations.
    """
    matches, _ = find_feasible_matches(
        donation, recipients_dict, volunteers_list,
        recipient_remaining=recipient_remaining,
        volunteer_remaining=volunteer_remaining,
        volunteer_pickups=volunteer_pickups,
    )
    return matches[0] if matches else None


def run_fifo_baseline(donations_dict, recipients_dict, volunteers_list, *, verbose=False):
    """Schedule each donation in input order; return explainable decisions.

    A matching donation is fully assigned to the FIRST feasible recipient and
    volunteer. Capacities and pickup limits are reserved only in local state.
    Each donation produces exactly one structured result, successful or not.
    """
    donations = _as_list(donations_dict)
    recipients = _as_list(recipients_dict)
    volunteers = _as_list(volunteers_list)

    recipient_remaining = {r["recipient_id"]: r["capacity"] for r in recipients}
    volunteer_remaining = {v["volunteer_id"]: v["vehicle_capacity"] for v in volunteers}
    volunteer_pickups = {v["volunteer_id"]: 0 for v in volunteers}
    recipient_names = {r["recipient_id"]: r.get("organization_name", r["recipient_id"])
                       for r in recipients}

    history = []
    for donation in donations:
        did, qty = donation["donation_id"], donation["quantity"]
        matches, reasons = find_feasible_matches(
            donation, recipients, volunteers,
            recipient_remaining=recipient_remaining,
            volunteer_remaining=volunteer_remaining,
            volunteer_pickups=volunteer_pickups,
        )
        if matches:
            match = matches[0]
            rid, vid = match["recipient_id"], match["volunteer_id"]
            recipient_remaining[rid] -= qty
            volunteer_remaining[vid] -= qty
            volunteer_pickups[vid] += 1
            record = {
                "donation_id": did, "recipient_id": rid, "volunteer_id": vid,
                "scheduled_time": match["scheduled_time"], "status": "assigned",
                "reason": (f"Assigned donation {did} to {recipient_names[rid]} ({rid}) "
                           f"with volunteer {vid} under FIFO (input arrival order). "
                           f"{match['reason']}"),
            }
        else:
            record = {
                "donation_id": did, "recipient_id": None, "volunteer_id": None,
                "scheduled_time": None, "status": "unassigned",
                "reason": (f"Unassigned donation {did} under FIFO: "
                           + ("; ".join(reasons) if reasons else "No feasible match found.")),
            }
        history.append(record)
        if verbose:
            print(record["reason"])
    return history


def run_fifo_with_metrics(donations, recipients, volunteers, *, urgent_threshold=90,
                          verbose=False):
    """Return (FIFO assignment history, FIFO metrics)."""
    history = run_fifo_baseline(donations, recipients, volunteers, verbose=verbose)
    report = calculate_metrics(donations, recipients, volunteers, history,
                               urgent_threshold=urgent_threshold)
    return history, report
