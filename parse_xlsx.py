#!/usr/bin/env python3

import re
from openpyxl import load_workbook  # pip install --user openpyxl
from itertools import chain
import pickle


# path to "cable journal" excel file
# it's a MS Excel spreadsheet with a list of node connections
# in Lomonosov 2 cluster
# I am not allowed to share it.
SPREADSHEET_FILENAME = r'wire_journal_48_53.xlsx'

# regex for parsing rack number and other numbers from cells
# with switch names in the spreadsheet
switch_regex = re.compile(
    r"""
    КГК\.       # literally match what is written here
    (?P<rack>\d+)\.        # rack number is one or more digits, followed by dot
    (?P<second_number>\d+)\.            # then goes another non-negative integer followed by dot
    (?P<last_number>\d+)            # and another integer of the same form
    """,
    re.VERBOSE
)


def get_column_name(column):
    """Takes column as tuple as argument and returns
    its name as string"""
    return column[0].column


def extract_columns(worksheet, column_names):
    """
    parameters:
        worksheet -- worksheet
        column_names -- list of strings, for example
            ['A', 'C', 'E']
    returns:
        list of columns, where every column is represented
        as a tuple"""
    all_columns = worksheet.columns
    extracted_columns = [col for col in all_columns
                         if get_column_name(col) in column_names]
    assert len(extracted_columns) == len(column_names)
    return extracted_columns


def columns_to_tuples(columns):
    """parameters:
        columns -- columns as a tuple/list of tuples
    returns:
        list of lists/tuples, each one represents a row"""
    return [[cell.value for cell in row] for row in zip(*columns)]


def parse_switch_pairs(workbook):
    """Parse openpyxl workbook and extract a list of
    pairs of switches. Pair (A, B) means that swithes A
    and B are connected.
    Returns list of pairs of strings."""
    return list(chain(*[columns_to_tuples(extract_columns(worksheet, ['C', 'K']))
                        for worksheet in workbook]))


# Lomonosov2's racks are grouped into pairs
# Switches in the same rack or pair of racks are connected with copper wires
# Switches in different pairs of racks are connected with optic cable
RACK_PAIRS = ((48, 49), (50, 51), (52, 53))


def get_rack(switch_name):
    """Determines rack number from switch name"""
    return int(switch_regex.match(switch_name).group('rack'))


def determine_material_between_switches(rack1, rack2):
    """Switches have different material between them.
    See comment about RACK_PAIRS.
    
    This function determines cable material between two switches
    by using their rack numbers and returns it as string"""
    racks = (rack1, rack2)
    if any(
            all(rack in rack_pair for rack in racks)
            for rack_pair in RACK_PAIRS):
        # they are in the same pair of racks
        return 'copper'
    return 'optic'


def get_cable_material_from_row(row):
    rack1 = row.loc["switch1_rack"]
    rack2 = row.loc["switch2_rack"]
    return determine_material_between_switches(rack1, rack2)


def get_second_number(switch_name):
    return switch_regex.match(switch_name).groups()[1]


def get_third_number(switch_name):
    return switch_regex.match(switch_name).groups()[2]


def parse_xslx():
    workbook = load_workbook(SPREADSHEET_FILENAME, data_only=True)
    switch_pairs = parse_switch_pairs(workbook)
    with open("switch_pairs.pkl", mode="wb") as f:
        pickle.dump(switch_pairs, f)


def test_everything():
    assert switch_regex.match("КГК.63.2.4").groups() == ("63", "2", "4")
    assert get_rack('КГК.48.0.1') == 48


if __name__ == "__main__":
    test_everything()
    parse_xslx()
