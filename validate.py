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


def validate_per_msg_len(predictions: pd.DataFrame, write_to: Path) -> None:
    mean_rel_err_per_len = predictions.groupby("msg_len")["relative_error"].mean() \
        .rename("mean relative error")
    max_rel_err_per_len = predictions.groupby("msg_len")["relative_error"].max() \
        .rename("max relative error")
    pd.concat([mean_rel_err_per_len, max_rel_err_per_len], axis=1).to_csv(write_to)
    print("Wrote to '{0}'".format(write_to))


def validate_on(
    topology_data: TopologyData, training_dir: Path, validation_dirs: Iterable[Path],
    output_dir: Path
) -> None:
    """Trains predictor on data in training_dir. Calculates mean squared error
    and does other validation stuff for data in validation_dirs"""
    logging.info("Training on '{0}'.".format(training_dir.basename()))
    training_data = load_test_results(training_dir)
    if not check_all_classes_covered(topology_data, training_data.hostnames):
        print(
            "'{0}' doesn't contain test data for at least one class. Skipping."
                .format(training_dir.basename())
        )
        return
    validation_data = join_ping_data(load_test_results(dir_) for dir_ in validation_dirs)
    predictor = Predictor(topology_data, training_data)
    predictions = predictor.predict_many(validation_data)
    predictions["abs_error"] = (predictions["ping"] - predictions["predicted_ping"]).abs()
    predictions["relative_error"] = (predictions["abs_error"] / predictions["ping"]).fillna(0)
    #assert 0 not in predictions["ping"]
    print("Trained on '{0}'. Validated on all other directories.".format(training_dir.basename()))
    print("mean (absolute error / ping) = {0}".format(predictions["relative_error"].mean(skipna=False)))
    print("max (absolute error / ping) = {0}".format(predictions["relative_error"].max(skipna=False)))
    validate_per_msg_len(predictions, output_dir.joinpath(training_dir.basename() + ".csv"))


@click.command()
@click.option(
    "--tests-results", "-t", required=True, envvar="NT2_TESTS_RESULTS",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    help="""Path to directory that contains network-tests2 results in subdirectories.
         Can be passed as NT2_TESTS_RESULTS environment variable"""
)
@click.option(
    "--output-dir", "-o", required=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=False, writable=True, readable=False),
    help="The program will write csv files to this dir"
)
@click.option("--verbose", "-v", is_flag=True)
def main(tests_results, output_dir, verbose):
    output_dir = Path(output_dir)
    if verbose:
        logging.basicConfig(level=logging.INFO)
    tests_results_dirs = Path(tests_results).dirs()
    topology_data = load_topology_data()
    for directory in tests_results_dirs:
        validate_on(
            topology_data, directory,
            (dir_ for dir_ in tests_results_dirs if dir_ != directory),
            output_dir
        )
        



if __name__ == "__main__":
    main()
    
