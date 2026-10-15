"""Urgency-first greedy scheduler for RescueRoute (simulated data only).

Priority: shortest remaining shelf life (expiry) first; then larger quantity;
then earlier ready_time; then original input order. All time values are
simulated minutes, and complete donations cannot be split.

Run this scheduler independently of FIFO using the ORIGINAL input data.
It never modifies donations, recipients, or volunteers.
"""

from matching import find_feasible_matches
from metrics import calculate_metrics


def _as_list(records):
    """Accept ID-keyed dictionaries or lists without modifying them."""
    return list(records.values()) if isinstance(records, dict) else list(records)


def _priority(donation, original_position):
    return (donation["expiry"], -donation["quantity"],
            donation["ready_time"], original_position)


def run_greedy(donations, recipients, volunteers, *, verbose=False):
    """Return one explainable assignment/unassigned record for each donation.

    Expected input: validated RescueRoute records. ``expiry`` represents
    remaining shelf life in minutes, starting at ``ready_time``.
    Vehicle capacity is a cumulative budget throughout this one simulation,
    rather than reset between deliveries (consistent with matching/metrics).
    """
    donation_list = _as_list(donations)
    recipient_list = _as_list(recipients)
    volunteer_list = _as_list(volunteers)

    # Remaining budgets are local to this strategy; originals stay unchanged.
    recipient_remaining = {r["recipient_id"]: r["capacity"] for r in recipient_list}
    volunteer_remaining = {v["volunteer_id"]: v["vehicle_capacity"] for v in volunteer_list}
    volunteer_pickups = {v["volunteer_id"]: 0 for v in volunteer_list}

    # Input order is interpreted as FIFO arrival order. We retain it for
    # readable fairness explanations when greedy jumps over earlier entries.
    ordered = sorted(enumerate(donation_list), key=lambda pair: _priority(pair[1], pair[0]))
    history = []
    for position, donation in ordered:
        did = donation["donation_id"]
        shelf_life = donation["expiry"]
        qty = donation["quantity"]
        # Earlier FIFO donations that greedy handles AFTER this donation.
        bypassed = [d["donation_id"] for original, d in ordered
                    if original < position and _priority(d, original) > _priority(donation, position)]
        priority_note = (f" Priority: {shelf_life} minutes remaining, {qty} units; "
                         "greedy orders by least shelf life, then greatest quantity, "
                         "then earliest ready time.")
        if bypassed:
            priority_note += (f" This donation was considered ahead of earlier-arriving "
                              f"donation(s) {', '.join(map(str, bypassed))}; those donations "
                              "were deferred in processing order, not automatically rejected.")
        matches, failures = find_feasible_matches(
            donation, recipient_list, volunteer_list,
            recipient_remaining=recipient_remaining,
            volunteer_remaining=volunteer_remaining,
            volunteer_pickups=volunteer_pickups,
        )
        if matches:
            match = matches[0]  # Deterministic first feasible recipient + volunteer
            rid, vid = match["recipient_id"], match["volunteer_id"]
            recipient_remaining[rid] -= qty
            volunteer_remaining[vid] -= qty
            volunteer_pickups[vid] += 1
            recipient_name = next(r.get("organization_name", rid)
                                  for r in recipient_list if r["recipient_id"] == rid)
            reason = (f"Assigned donation {did} to {recipient_name} ({rid}) with volunteer "
                      f"{vid}. {match['reason']}" + priority_note)
            record = {"donation_id": did, "recipient_id": rid, "volunteer_id": vid,
                      "scheduled_time": match["scheduled_time"], "status": "assigned",
                      "reason": reason}
        else:
            failures_text = "; ".join(failures) if failures else "No feasible match."
            record = {"donation_id": did, "recipient_id": None, "volunteer_id": None,
                      "scheduled_time": None, "status": "unassigned",
                      "reason": f"Unassigned donation {did}: {failures_text}." + priority_note}
        history.append(record)
        if verbose:
            print(record["reason"])
    return history


def run_greedy_with_metrics(donations, recipients, volunteers, *, urgent_threshold=90,
                            verbose=False):
    """Run greedy and calculate metrics against the untouched initial inputs."""
    history = run_greedy(donations, recipients, volunteers, verbose=verbose)
    report = calculate_metrics(donations, recipients, volunteers, history,
                               urgent_threshold=urgent_threshold)
    return history, report


# Optional naming alias for callers who prefer a descriptive function name.
run_greedy_urgency_first = run_greedy
