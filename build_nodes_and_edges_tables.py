#!/usr/bin/env python3

import pickle
import pandas as pd
from itertools import chain


def build_switches_table(switch_pairs):
    switches = pd.DataFrame({
        "name": sorted(list(frozenset(chain(*switch_pairs))))
    })
    switches["rack_number"] = switches["name"].apply(get_rack)
    switches["second_number"] = switches["name"].apply(get_second_number)
    switches["third_number"] = switches["name"].apply(get_third_number)


def main():
    with open("switch_pairs.pkl", "rb") as f:
        switch_pairs = pickle.load(f)

