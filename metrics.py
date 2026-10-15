"""Explainable, comparable metrics for RescueRoute FIFO and greedy outcomes.

Pass structured assignment records with donation_id, recipient_id,
volunteer_id, status ('assigned', 'unassigned', or 'deferred'), and reason.
Quantities are counted only once per donation. Invalid input records should
be rejected by validation before calling these functions.
"""


def _records(items):
    return list(items.values()) if isinstance(items, dict) else list(items)


def _field(item, *names, default=None):
    for name in names:
        if name in item:
            return item[name]
    return default


def calculate_metrics(donations, recipients, volunteers, assignments, urgent_threshold=90):
    """Return metrics for one strategy, using original (unmodified) input data.

    Urgent = donation shelf life <= ``urgent_threshold`` minutes.
    Recipient utilization = assigned units / sum(initial recipient capacity).
    Volunteer utilization = assigned units / sum(initial vehicle capacity).
    This treats vehicle capacity as a cumulative simulation budget, consistent
    with the current FIFO prototype. Unassigned/deferred donations remain at risk.
    """
    donations = _records(donations)
    recipients = _records(recipients)
    volunteers = _records(volunteers)
    assignments = _records(assignments)
    donation_by_id = {d["donation_id"]: d for d in donations}
    recipient_by_id = {r["recipient_id"]: r for r in recipients}
    volunteer_by_id = {v["volunteer_id"]: v for v in volunteers}
    assigned_ids = set()
    recipient_used = {rid: 0 for rid in recipient_by_id}
    volunteer_used = {vid: 0 for vid in volunteer_by_id}
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise TypeError("Metrics require structured assignment dictionaries, not text messages.")
        if str(assignment.get("status", "")).lower() != "assigned":
            continue
        did = assignment.get("donation_id")
        rid = assignment.get("recipient_id")
        vid = assignment.get("volunteer_id")
        if did not in donation_by_id or rid not in recipient_by_id or vid not in volunteer_by_id:
            raise ValueError(f"Assigned record refers to an unknown ID: {assignment}")
        if did in assigned_ids:
            raise ValueError(f"Donation {did} appears assigned more than once")
        assigned_ids.add(did)
        quantity = donation_by_id[did]["quantity"]
        recipient_used[rid] += quantity
        volunteer_used[vid] += quantity

    total_qty = sum(d["quantity"] for d in donations)
    rescued = sum(donation_by_id[did]["quantity"] for did in assigned_ids)
    urgent_ids = {d["donation_id"] for d in donations if d["expiry"] <= urgent_threshold}
    urgent_assigned = len(urgent_ids & assigned_ids)
    recipient_capacity = sum(r["capacity"] for r in recipients)
    volunteer_capacity = sum(_field(v, "vehicle_capacity", "vehicle capacity", default=0) for v in volunteers)

    def ratio(num, denom):
        return round(100 * num / denom, 2) if denom else 0.0

    return {
        "donations_received": len(donations),
        "donations_assigned": len(assigned_ids),
        "donations_unassigned": len(donations) - len(assigned_ids),
        "food_quantity_rescued": rescued,
        "food_quantity_at_risk": total_qty - rescued,
        "urgent_donations_received": len(urgent_ids),
        "urgent_donations_assigned": urgent_assigned,
        "urgent_rescue_rate": ratio(urgent_assigned, len(urgent_ids)),
        "recipient_capacity_utilization": ratio(rescued, recipient_capacity),
        "volunteer_capacity_utilization": ratio(rescued, volunteer_capacity),
        "recipient_utilization_by_id": {
            rid: ratio(recipient_used[rid], item["capacity"])
            for rid, item in recipient_by_id.items()
        },
        "volunteer_utilization_by_id": {
            vid: ratio(volunteer_used[vid], _field(item, "vehicle_capacity", "vehicle capacity", default=0))
            for vid, item in volunteer_by_id.items()
        },
    }


def compare_strategies(fifo_metrics, greedy_metrics):
    """Return both metrics plus greedy-minus-FIFO numeric differences."""
    keys = ["donations_assigned", "donations_unassigned", "food_quantity_rescued",
            "food_quantity_at_risk", "urgent_rescue_rate",
            "recipient_capacity_utilization", "volunteer_capacity_utilization"]
    differences = {key: round(greedy_metrics[key] - fifo_metrics[key], 2) for key in keys}
    rescued_delta = differences["food_quantity_rescued"]
    urgent_delta = differences["urgent_rescue_rate"]
    explanation = (
        f"Compared with FIFO, greedy rescued {abs(rescued_delta)} "
        f"{'more' if rescued_delta > 0 else 'fewer' if rescued_delta < 0 else 'additional'} units "
        f"and changed the urgent rescue rate by {urgent_delta:+.2f} percentage points. "
        "Differences can arise because earlier-scheduled donations reserve finite "
        "recipient and volunteer capacity, potentially blocking later ones. "
        "These totals alone do not identify which specific priority decision caused a change; "
        "consult the assignment explanations for that detail."
    )
    return {"fifo": fifo_metrics, "greedy": greedy_metrics,
            "greedy_minus_fifo": differences, "explanation": explanation}


def print_comparison(comparison):
    """Display a small human-readable comparison table."""
    print(f"{'Metric':34} {'FIFO':>12} {'Greedy':>12} {'Difference':>12}")
    print("-" * 74)
    for key, difference in comparison["greedy_minus_fifo"].items():
        print(f"{key:34} {comparison['fifo'][key]:>12} "
              f"{comparison['greedy'][key]:>12} {difference:>+12}")
    print(comparison["explanation"])
