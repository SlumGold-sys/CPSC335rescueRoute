"""Run and compare RescueRoute's FIFO and urgency-first greedy schedulers.

Default input paths match the team's existing tests/ JSON fixtures.
Usage: python main.py [--donations PATH --recipients PATH --volunteers PATH]
All matching takes place in a simplified simulation, not a real food-safety
or delivery system.
"""

import argparse
import sys

import validation
from fifo import run_fifo_with_metrics
from greedy import run_greedy_with_metrics
from metrics import compare_strategies, print_comparison


def load_inputs(donation_path, recipient_path, volunteer_path):
    """Load via the team's validation module and return independent snapshots.

    validation.py currently maintains module-level collections and catches
    missing/invalid JSON files. Clear them before each run to prevent old
    records from leaking into a subsequent run within the same Python process.
    """
    validation.donations_dict.clear()
    validation.recipients_dict.clear()
    validation.volunteers_list.clear()
    validation.seen_ids.clear()

    validation.load_and_validate_data(donation_path, "donation")
    validation.load_and_validate_data(recipient_path, "recipient")
    validation.load_and_validate_data(volunteer_path, "volunteer")
    return (list(validation.donations_dict.values()),
            list(validation.recipients_dict.values()),
            list(validation.volunteers_list))


def run_comparison(donations, recipients, volunteers, *, urgent_threshold=90,
                   verbose=True):
    """Run both strategies against identical, non-mutated starting data."""
    if verbose:
        print("\n=== FIFO ASSIGNMENTS ===")
    fifo_history, fifo_report = run_fifo_with_metrics(
        donations, recipients, volunteers,
        urgent_threshold=urgent_threshold, verbose=verbose,
    )
    if verbose:
        print("\n=== GREEDY ASSIGNMENTS ===")
    greedy_history, greedy_report = run_greedy_with_metrics(
        donations, recipients, volunteers,
        urgent_threshold=urgent_threshold, verbose=verbose,
    )
    comparison = compare_strategies(fifo_report, greedy_report)
    if verbose:
        print("\n=== FIFO VS GREEDY METRICS ===")
        print_comparison(comparison)
    return {"fifo_assignments": fifo_history,
            "greedy_assignments": greedy_history,
            "comparison": comparison}


def main(argv=None):
    parser = argparse.ArgumentParser(description="RescueRoute simulated food donation scheduler")
    parser.add_argument("--donations", default="tests/donations.json")
    parser.add_argument("--recipients", default="tests/recipients.json")
    parser.add_argument("--volunteers", default="tests/volunteers.json")
    parser.add_argument("--urgent-threshold", type=int, default=90,
                        help="remaining shelf life in minutes considered urgent (default: 90)")
    args = parser.parse_args(argv)
    if args.urgent_threshold < 0:
        parser.error("--urgent-threshold must be non-negative")
    donations, recipients, volunteers = load_inputs(
        args.donations, args.recipients, args.volunteers)
    print(f"Loaded {len(donations)} donations, {len(recipients)} recipients, "
          f"and {len(volunteers)} volunteers.")
    if not all((donations, recipients, volunteers)):
        print("Error: one or more validated datasets is empty; cannot run comparison.",
              file=sys.stderr)
        return 1
    run_comparison(donations, recipients, volunteers,
                   urgent_threshold=args.urgent_threshold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
