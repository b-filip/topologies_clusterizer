#!/usr/bin/env python3

import pandas as pd
import numpy as np
from path import Path  # pip install --user path.py
import re
from pprint import pprint
import netCDF4
from collections import namedtuple
from random import randint, choice
import click  # pip install --user click
import logging
from predict import Predictor, load_test_results, load_topology_data, TestResults, TopologyData, \
                    check_all_classes_covered
from typing import Iterable, Dict


def join_dict_to_table(dict_: Dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Can be used on test_results.medians.
    
    Takes a dict (msg_len -> df(node1, node2, ping))
    
    Returns df(msg_len, node1, node2, ping) with dummy index"""
    return pd.concat(dict_, names=["msg_len", "dumb_index"], verify_integrity=True) \
        .reset_index(level=1, drop=True) \
        .reset_index()


def join_ping_data(multiple_tests_results: Iterable[TestResults]) -> pd.DataFrame:
    """Takes medians from all of them and concatenates them all.
    You get a DataFrame with columns (msg_len, node1, node2, ping)"""
    return pd.concat(
        (join_dict_to_table(test_results.medians) for test_results in multiple_tests_results),
        ignore_index=True
    )


def validate_on(topology_data: TopologyData, training_dir: Path, validation_dirs: Iterable[Path]):
    """Trains predictor on data in training_dir. Calculates mean squared error
    and does other validation stuff for data in validation_dirs"""
    training_dir_basename = training_dir.basename()
    logging.info("Training on '{training_dir_basename}'.".format(**locals()))
    training_data = load_test_results(training_dir)
    if not check_all_classes_covered(topology_data, training_data.hostnames):
        print(
            "'{training_dir_basename}' doesn't contain test data for at least one class. Skipping."
                .format(**locals())
        )
        return
    validation_data = join_ping_data(load_test_results(dir_) for dir_ in validation_dirs)
    predictor = Predictor(topology_data, training_data)
    predictions = predictor.predict_many(validation_data)
    mean_error = (predictions["ping"] - predictions["predicted_ping"]).abs().mean()
    print(
        "Trained on '{training_dir_basename}'. Calculated mean absolute error for all other directories."
            .format(**locals())
    )
    print("Mean absolute error = {mean_error}".format(**locals()))


@click.command()
@click.option(
    "--tests-results", "-t", required=True, envvar="NT2_TESTS_RESULTS",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    help="""Path to directory that contains network-tests2 results in subdirectories.
         Can be passed as NT2_TESTS_RESULTS environment variable"""
)
@click.option("--verbose", "-v", is_flag=True)
def main(tests_results, verbose):
    if verbose:
        logging.basicConfig(level=logging.INFO)
    tests_results_dirs = Path(tests_results).dirs()
    topology_data = load_topology_data()
    for directory in tests_results_dirs:
        validate_on(
            topology_data, directory,
            (dir_ for dir_ in tests_results_dirs if dir_ != directory)
        )
        



if __name__ == "__main__":
    main()
    
