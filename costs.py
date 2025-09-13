def lookup_df_cost(df, names, name_col, stat_col, day=None, day_col=None):
    if day is None:
        mask = df[name_col].isin(names)
    else:
        mask = (df[name_col].isin(names)) & (df[day_col] == day)
    return df.loc[mask, stat_col].sum()


def assess_fixed_costs(key, assignee_df, task_df, surprise_df):

    assignee_df["fixed cost"] = assignee_df.apply(
        lambda row: lookup_df_cost(task_df, row["fixed"], key["ts"], key["tn"]), axis=1
    )
    assignee_df["fixed surprise cost"] = assignee_df.apply(
        lambda row: lookup_df_cost(
            surprise_df,
            row["fixed surprises"],
            key["ss"],
            "mean",
            day=row[key["ad"]],
            day_col=key["sd"],
        ),
        axis=1,
    )
    assignee_df["fixed surprise variation"] = assignee_df.apply(
        lambda row: lookup_df_cost(
            surprise_df,
            row["fixed surprises"],
            key["ss"],
            "2std",
            day=row[key["ad"]],
            day_col=key["sd"],
        ),
        axis=1,
    )


def calc_fixed_deltas(df):
    """Returns candidate[1] - candidate[0]."""

    assert len(df) == 2, f"At this point, dataframe should be length 2:\n{df}"

    cost0 = df["fixed cost"].iloc[0] + df["fixed surprise cost"].iloc[0]
    cost1 = df["fixed cost"].iloc[1] + df["fixed surprise cost"].iloc[1]
    var0 = df["fixed surprise variation"].iloc[0]
    var1 = df["fixed surprise variation"].iloc[1]

    return (cost1 - cost0, var1 - var0)
