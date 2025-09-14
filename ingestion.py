import json

import numpy as np
import pandas

# Agreed-upon required keys, along with their shortname for easier access
KEYS = {
    "a": "assignees",
    "at": "assignee team",
    "ad": "assignee day",
    "ss": "surprise sources",
    "sd": "surprise day",
    "ts": "task sources",
    "tn": "task number",
    "ktt": "known task team",
    "sp": "surprise profile",
    "sdt": "surprise distribution team",
    "sdist": "surprise distribution data",
}


def parse_keyfile(keyfile):
    """
    Take in a keyfile which maps the known required data to specific columns
    in the incoming data. This allows the user of whatever software is
    filling out the spreadsheet data to see tasking columns that are more
    understandable without using job-specific columns in the code.
    """

    # Gather keyfile data
    data = json.load(open(keyfile, "r"))

    # Check for quality
    assert isinstance(data, dict), f"Keyfile {keyfile} should store a json dict"
    for key in KEYS.values():
        assert key in data, f"Required key {key} not found"
    assert len(data) == len(
        KEYS
    ), f"Key mismatch between\n{sorted(data.keys())}\n{sorted(KEYS.values())}"

    # Sort the keyfile by the shortnames
    return {key: data[value] for key, value in KEYS.items()}


def parse_spreadsheets(file, keyfile):

    key = parse_keyfile(keyfile)

    # Read the full spreadsheet, then split it into chunks using shortnames
    df = pandas.read_csv(file)
    assignees = df[[key["a"], key["at"], key["ad"]]].dropna()
    surprises = df[[key["ss"], key["sd"]]].dropna()
    tasks = df[[key["ts"], key["tn"], key["ktt"], key["sp"]]].dropna()
    distributions = df[[key["sdt"], key["sdist"]]].dropna()

    # Filter the distribution information into the surprises
    unpack_dist(key, surprises, distributions, tasks)

    # Filter the surprise team information into the surprise sources
    surprises = unpack_surprise_team(key, surprises, tasks)

    # Remap the assignee days, since tasks generated on Friday will be handled
    # on Saturday and so on
    remap_days(key, assignees)

    return key, assignees, surprises, tasks


def unpack_dist(key, surprise_df, dist_df, task_df) -> None:
    """
    Label each surprise with the appropriate distribution, modifying the
    suprises dataframe in place.
    """

    distributions = {
        row[key["sdt"]]: parse_dist_dataset(row[key["sdist"]])
        for _, row in dist_df.iterrows()
    }

    # Make a temporary working dataframe
    df = surprise_df.merge(task_df, left_on=key["ss"], right_on=key["ts"], how="left")

    # Map the team of each surprise tasker to that team's profile
    surprise_df["mean"] = df[key["sp"]].map(
        lambda team: float(np.round(distributions[team].mean(), 1))
    )
    surprise_df["2std"] = df[key["sp"]].map(
        lambda team: float(np.round(2 * distributions[team].std(), 1))
    )


def parse_dist_dataset(dist_str) -> np.ndarray:
    """
    Two options. If numbers are given with
        X|Y|Z
    then X is assumed to have 2 instances (20% representation, low end), Y is
    assumed to have 6 instances (60% representation, bulk), and Z is assumed
    to have 2 instances (20% representation, high end). This is just a simple
    and understandable way to roughly bound a distribution.

    If the numbers are given with
        u,v,w,x,y,z
    then assume that these are measured data points.

    Returns a numpy array of data that can provide .mean() and .std() info.
    """
    if "|" in dist_str:
        X = dist_str.split("|")
        assert len(X) == 3, f"{dist_str} was expected to be X|Y|Z"
        return np.array([int(X[0])] * 2 + [int(X[1])] * 6 + [int(X[2])] * 2)
    else:
        return np.array([int(x) for x in dist_str.split(",")])


def unpack_surprise_team(key, surprise_df, task_df) -> pandas.DataFrame:

    # Label the surprise_df with the team each surprise source is assigned to
    return surprise_df.merge(
        task_df[[key["ts"], key["ktt"]]],
        left_on=key["ss"],
        right_on=key["ts"],
        how="left",
    ).drop(columns=[key["ts"]])


def remap_days(key, assignees):
    """
    Remap the assignee days to the day the tasks are generated, since tasks
    generated on Friday will be handled on Saturday and so on
    """
    assignees[key["ad"]] = assignees[key["ad"]].map(
        {"Saturday": "Friday", "Sunday": "Saturday"}
    )
