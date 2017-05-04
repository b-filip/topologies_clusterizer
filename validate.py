#!/usr/bin/env python3

import pandas as pd
import numpy as np
from path import Path  # pip install --user path.py
import re
from IPython.display import display
from pprint import pprint
import netCDF4
from IPython.core.debugger import Pdb
from collections import namedtuple
from random import randint, choice
import click  # pip install --user click


@click.command()
@click.option(
    "--tests-results", "-t", required=True, envvar="NT2_TESTS_RESULTS",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    help="Path to directory that contains network-tests2 results in subdirectories."
         "Can be passed as NT2_TESTS_RESULTS environment variable"
)
def main(tests_results):
    tests_results_dirs = Path(tests_results).dirs()
    for directory in tests_results_dirs:
        print("Training on '{0}'.".format(directory.basename()))


if __name__ == "__main__":
    main()
    
