# cidb

This directory contains CIDB data and the script to convert CIDB data
into BODS-CIDB data that follow at least BODS schema version 0.1.

BODS schema is in beta (as this commit date). So the schema may be
subject to changes and this script may need to update if so.

## CIDB data

CIDB data are the JSONL files used as source data. Each JSONL file
contains one JSON object (in CIDB source format) per line.

Files: `contractors*.jsonl`

## BODS-CIDB data

BODS-CIDB data are the JSONL files generated by the script. Each JSONL
file contains one JSON object (in BODS format) per line.

Files: `bods-contractors*.jsonl`

## Script usage

The script will convert all source data to BODS record format.

    $ python cidb_to_bods.py

The script will look for matching files (`contractors*.jsonl`) in the
specified directory (`data`) and process each file accordingly.

New files with `bods-` prefix will be created if new source data has
been added. Any existing generated files with `bods-` prefix will be
overwritten with new data.

## Script requirements

Python 2.7+ or Python 3.4+
