def print_full(key, day, assignee_df, unassigned, grouping):
    assert (
        len(assignee_df) == 2
    ), f"At this point, dataframe should be length 2:\n{assignee_df}"

    # Map the day from when tasks were generated to when they'll be done
    day = {"Friday": "Saturday", "Saturday": "Sunday"}[day]

    # Lay out the groundwork
    work0 = assignee_df.iloc[0]
    work1 = assignee_df.iloc[1]
    print(f"========OVERVIEW FOR {day.upper()}========\n")
    for worker, name in [(work0, "Worker 0"), (work1, "Worker 1")]:
        fc = worker["fixed cost"]
        fsc = worker["fixed surprise cost"]
        fsv = worker["fixed surprise variation"]
        print(f"{name}: {worker[key['a']]:<12}[Team: {worker[key['at']]}]")
        print(f"\tFor sure covering [{fc} tasks]: {worker['fixed']}")
        print(
            f"\tFor sure covering {key['ss'].lower()}s [{fsc} expected tasks]: {worker['fixed surprises']}"
        )
        print(f"\tTotal so far: {fc + fsc:.1f} tasks, variation ±{fsv:.1f}")

    # Lay out the problem
    names, tasks, variation = unassigned
    print("\nThese need covering:")
    for name, task, vary in sorted(zip(names, tasks, variation)):
        suffix = "" if vary == 0 else f"±{vary:.1f}"
        print(f"\t{name}: {task} tasks {suffix}")

    # Explain the split
    print(f"\nSUGGESTED SPLIT FOR {day.upper()}\n")
    for i, worker in enumerate([work0, work1]):
        fc = worker["fixed cost"]
        fsc = worker["fixed surprise cost"]
        fsv = worker["fixed surprise variation"]
        dc = sum([tasks[j] for j in grouping[i]])
        dv = sum([variation[j] for j in grouping[i]])
        print(f"{worker[key['a']]} takes {', '.join([names[j] for j in grouping[i]])}")
        print(f"\tThis results in a total of {fc + fsc + dc:.1f} tasks ±{fsv + dv:.1f}")


def print_simple(key, assignee_df, unassigned, grouping):
    assert (
        len(assignee_df) == 2
    ), f"At this point, dataframe should be length 2:\n{assignee_df}"

    # Lay out only the split
    work0 = assignee_df.iloc[0]
    work1 = assignee_df.iloc[1]
    names, tasks, variation = unassigned

    for i, worker in enumerate([work0, work1]):
        fc = worker["fixed cost"]
        fsc = worker["fixed surprise cost"]
        fsv = worker["fixed surprise variation"]
        dc = sum([tasks[j] for j in grouping[i]])
        dv = sum([variation[j] for j in grouping[i]])
        print(
            f"\t{worker[key['a']]} takes {', '.join([names[j] for j in grouping[i]])} = "
            f"{fc + fsc + dc:.1f} tasks ±{fsv + dv:.1f}"
        )
    print("")
