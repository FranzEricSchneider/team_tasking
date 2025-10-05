from itertools import combinations
from typing import List, Tuple

import numpy as np


def assign_fixed(key, assignee_df, task_df) -> None:
    """
    Checks for the team of each assignee and the team of each tasker, and
    assigns taskers on team A to the assignee on team A. Note that some
    teams will be unrepresented in assignees, and those unclaimed tasks
    will be divvied up later.

    Modifies the assignee DF in place.
    """

    # Make a mapping from team: [task source 1, task source 2, ...]
    mapping = task_df.groupby(key["ktt"])[key["ts"]].apply(list).to_dict()

    # Apply that map to the assignees
    assignee_df["fixed"] = assignee_df[key["at"]].map(mapping)


def assign_fixed_surprises(key, assignee_df, surprise_df):
    """
    Checks for the team of each assignee and the team of each surprise tasker,
    and assigns taskers on team A to the assignee on team A. Note that some
    teams will be unrepresented in assignees, and those unclaimed tasks
    will be divvied up later.

    Modifies the assignee DF in place.
    """

    # Make a mapping from (day, team): [surprise source 1, surprise source 2, ...]
    mapping = (
        surprise_df.groupby([key["sd"], key["ktt"]])[key["ss"]].apply(list).to_dict()
    )
    # Apply that map to the assignees
    assignee_df["fixed surprises"] = assignee_df.apply(
        lambda row: mapping[(row[key["ad"]], row[key["at"]])], axis=1
    )

    # Then duplicate that for the surprise sources
    mapping = (
        surprise_df.groupby([key["sd"], key["ktt"]])["source"].apply(list).to_dict()
    )
    # Apply that map to the assignees
    assignee_df["fixed surprise sources"] = assignee_df.apply(
        lambda row: mapping[(row[key["ad"]], row[key["at"]])], axis=1
    )


def unassigned_tasks(
    key, day, assignee_df, task_df, surprise_df
) -> Tuple[List, np.ndarray, np.ndarray]:

    fixed = set(name for sublist in assignee_df["fixed"] for name in sublist)
    surprises = set(
        name for sublist in assignee_df["fixed surprises"] for name in sublist
    )

    # Make a temporary dataframe that is just the free tasks
    free_task_df = task_df[~task_df[key["ts"]].isin(fixed)]
    free_surprise_df = surprise_df[
        (~surprise_df[key["ss"]].isin(surprises)) & (surprise_df[key["sd"]] == day)
    ]

    # Build up a list of unassigned names and tasks
    names = free_task_df[key["ts"]].tolist()
    tasks = np.array(free_task_df[key["tn"]], dtype=float)
    variation = np.zeros_like(tasks)

    # Add in the surprise names, adding to existing names if relevant or appending
    for _, row in free_surprise_df.iterrows():
        if row[key["ss"]] in names:
            index = names.index(row[key["ss"]])
            tasks[index] += row["mean"]
            variation[index] += row["2std"]
        else:
            names.append(row[key["ss"]])
            tasks = np.hstack([tasks, [row["mean"]]])
            variation = np.hstack([variation, [row["2std"]]])

    # Weed out zero taskers
    mask = tasks == 0
    if mask.sum() > 0:
        names = [names[i] for i in np.where(~mask)[0]]
        tasks = tasks[~mask]
        variation = variation[~mask]

    return names, tasks, variation


def find_best_matches(deltas, names, tasks, variation, N):
    """
    Try all combos of unassigned tasks to try and achieve the given delta. The
    delta was calculated with x1-x0, so here we will do x0-x1 and attempt to
    get it equal.
    """

    # Try to balance delta0 primarily, with a slight weight given to delta1
    # (arbitrarily 0.1 for now)
    delta0, delta1 = deltas
    d1_weight = 0.1

    def cost(ind0, ind1):
        t0 = np.sum([tasks[i] for i in ind0])
        t1 = np.sum([tasks[i] for i in ind1])
        v0 = np.sum([variation[i] for i in ind0])
        v1 = np.sum([variation[i] for i in ind1])
        return float(
            np.abs((t0 - t1) - delta0) + d1_weight * np.abs((v0 - v1) - delta1)
        )

    combos = []
    costs = []
    for grouping in all_two_group_splits(range(len(names))):
        combos.append(grouping)
        costs.append(cost(*grouping))

    # Sort by cost
    sorted_pairs = sorted(zip(costs, combos), key=lambda x: x[0])
    costs, combos = map(list, zip(*sorted_pairs))

    return combos[:N]


def all_two_group_splits(indices) -> Tuple[List, List]:
    """
    Generate all ways to split indices into 2 groups (order doesn't matter),
    including empty groups.
    """
    n = len(indices)
    for r in range(n + 1):
        for group1 in map(list, combinations(indices, r)):
            group2 = [x for x in indices if x not in group1]
            yield (group1, group2)
