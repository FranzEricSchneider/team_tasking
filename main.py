#!/usr/bin/env python3

import argparse
from pathlib import Path

from assignation import (
    assign_fixed,
    assign_fixed_surprises,
    find_best_matches,
    unassigned_tasks,
)
from costs import assess_fixed_costs, calc_fixed_deltas
from ingestion import parse_spreadsheets


def main(spreadsheet, keyfile):

    key, assignees, surprises, tasks = parse_spreadsheets(
        file=spreadsheet,
        keyfile=keyfile,
    )

    # Assign tasks to team members who must take their team's tasks
    assign_fixed(key, assignees, tasks)

    # Assign surprise tasks that necessarily go to a team member
    assign_fixed_surprises(key, assignees, surprises)

    # Assess costs at this point
    assess_fixed_costs(key, assignees, tasks, surprises)

    for df in [key, assignees, surprises, tasks]:
        print("=" * 80)
        print(df)

    # Split by day
    for day, subdf in assignees.groupby(key["ad"]):

        # When divvying up tasks, what are we trying to cancel out?
        deltas = calc_fixed_deltas(subdf)

        # Figure out which names and tasks are up for grabs
        unassigned = unassigned_tasks(key, day, subdf, tasks, surprises)

        # Try random variations to find the best match, sorted
        best_matches = find_best_matches(deltas, *unassigned, N=5)

        print(f"{day} →")
        for indices in best_matches[0]:
            print(f"\tMatched with: {[unassigned[0][i] for i in indices]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="TODO",
    )
    parser.add_argument("--data", type=Path)
    parser.add_argument("--key", type=Path)
    args = parser.parse_args()

    main(
        spreadsheet=args.data,
        keyfile=args.key,
    )
