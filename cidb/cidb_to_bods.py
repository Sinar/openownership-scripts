#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

def bods_statement(parse):
    # parse data for each statement
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    entity = {}
    # TODO: entity for "firm" or "director"
    interested_party = {}
    # TODO: interested_party for "firm" or "director"
    interest_list = []
    # TODO: interest_list.append() for "firm" or "director"
    # assign data into statement fields
    statement_data = {
        "#comment": parse["#comment"], # DEBUG: Temp use
        "id": uuid.uuid4().hex,
        "statementDate": now,
        "entity": entity,
        "interestedParty": interested_party,
        "interests": interest_list
    }
    return statement_data

def compile_person(parse):
    data = {}
    # check if "directors" field exist
    result = None # assume not found first
    for field in parse:
        if "directors" in field:
            result = "yes" # overwrite result if found
    # generate statement from directors details
    statement_list = []
    if isinstance(result, type(None)) or \
       len(parse["directors"]) == 0:
        data["#comment"] = "No director details" # DEBUG: Temp use
        statement = bods_statement(data)
        statement_list.append(statement)
#        print('DEBUG: result no: {}'.format(data))
    elif len(parse["directors"]) >= 1:
        for data in parse["directors"]:
            data["#comment"] = "Director details here" # DEBUG: Temp use
            statement = bods_statement(data)
            statement_list.append(statement)
#        print('DEBUG: result yes: {}'.format(data))
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected content in parse data', parse)
    return statement_list

def compile_entity(parse):
    data = {}
    data["#comment"] = "Firm details here" # DEBUG: Temp use
    # generate statement from firm details
    statement_list = []
    statement = bods_statement(data)
    statement_list.append(statement)
    return statement_list

def bods_package(parse):
    # parse data for package metadata
    bods_id = uuid.uuid4().hex + '-meta-' + parse["meta"]["id"]
    bods_list = []
    # generate statements from "firm" details
    statement_list = compile_entity(parse)
    for statement in statement_list:
        bods_list.append(statement)
    # generate statements from "director" details
    statement_list = compile_person(parse)
    for statement in statement_list:
        bods_list.append(statement)
    # assign data into package fields
    package_data = {
        "statementGroups": [
            {
                "id": bods_id,
                "beneficialOwnershipStatements": bods_list
            }
        ]
    }
    # DEBUG: BODS list should contain at least two statements
    if len(bods_list) < 2:
        raise ValueError('Unexpected number of statements',
                         len(bods_list))
    return package_data

def cidb_to_bods(path, parse_ls):
    for fname in parse_ls:
        # retrieve JSONL file in CIDB format
        fpath = path + '/' + fname
        print('Read from {}'.format(fpath))
        cidb_file = open(fpath, 'r')
        # prepare JSONL file in BODS format
        bods_fname = 'bods-' + fname
        bods_fpath = path + '/' + bods_fname
        print('Write to {}'.format(bods_fpath))
        bods_file = open(bods_fpath, 'w')
        # convert each line from CIDB to BODS format
        for line in cidb_file:
            data = json.loads(line)
            bods_data = bods_package(data)
            dump_data = json.dumps(bods_data)
            bods_file.write(dump_data + '\n')
        bods_file.close()
        cidb_file.close()

def main():
    path = './data' # location of files
    blob = 'contractors*.jsonl' # name of files to match
    name_ls = []
    for name in os.listdir(path):
        if fnmatch.fnmatch(name, blob):
            name_ls.append(name)
    name_ls.sort()
    if len(name_ls) == 0:
        print('File not found: {0}/{1}'.format(path, blob))
    else:
        cidb_to_bods(path, name_ls)
    print('Finish')

if __name__ == '__main__':
    main()
