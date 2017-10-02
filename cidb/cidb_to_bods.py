#!/usr/bin/python

from __future__ import print_function
import os
import fnmatch
import json
import uuid
import datetime

# define global variable
OBJ_LINK = {}

def party_identifier(parse):
    # parse data for identifier in party
    party_id = ""
    party_schema = ""
    # Use HINT to overwrite default values, if any
    if parse["#has_type"] == "firm":
        party_id = uuid.uuid4().hex
        party_schema = "UUID-HEX"
        # modify global variable to save as object for later reuse
        global OBJ_LINK
        OBJ_LINK["firm"] = {}
        OBJ_LINK["firm"]["party_id"] = party_id
        OBJ_LINK["firm"]["party_schema"] = party_schema
    elif parse["#has_type"] == "person":
        if parse["#has_data"] == "yes":
            icnum = parse["idenfity_card_no"] # this is not a typo!
            party_id = "MYS-IDCARD-" + icnum # following BODS docs
            party_schema = "id-card" # using BODS codelist
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    # assign data into identifier fields
    party_identifier_data = {
        "id": party_id,
        "schema": party_schema
    }
    return party_identifier_data

def bods_party(parse):
    # parse data for each interested party
    generated_date = parse["generated_date"] # from bods_statement
    party_type = "arrangement"
    party_name = "Joint shareholding"
    null_party_type = ""
    null_party_desc = ""
    # Use HINT to overwrite default values, if any
    if parse["#has_type"] == "firm":
        if parse["#has_person"] == "yes":
            pass # use default values for existing firm
        else:
            null_party_type = "unknown"
            null_party_desc = "no beneficial owner in source"
    elif parse["#has_type"] == "person":
        if parse["#has_data"] == "yes":
            party_name = parse["name"]
            party_type = "naturalPerson"
            # check nationality and assign 2-letter country code
            if "MALAYSIA" in parse["nationality"]:
                nationality = "MY" # refer ISO 3166-1 alpha-2
            else:
                nationality = "XX" # unknown nationality if empty
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    identifier_list = []
    identifier_list.append(party_identifier(parse))
    # assign data into interested party fields
    interested_party_data = {
        "id": uuid.uuid4().hex,
        "statementDate": generated_date,
        "type": party_type,
        "name": party_name,
        "identifiers": identifier_list
    }
    # assign data to additional field for existing person
    if parse["#has_type"] == "person" and \
       parse["#has_data"] == "yes":
        interested_party_data["nationalities"] = []
        interested_party_data["nationalities"].append(nationality)
    # assign data into null party fields
    null_party_data = {
        "type": null_party_type,
        "description": null_party_desc
    }
    # overwrite data to return if null_party_type has non-empty strings
    if len(null_party_type) != 0:
        interested_party_data = null_party_data
    return interested_party_data

def entity_identifier(parse):
    # parse data for identifier in entity
    entity_id = ""
    entity_schema = ""
    # Use HINT to overwrite default values, if any
    if parse["#has_type"] == "firm":
        if parse["#has_data"] == "yes":
            # no persistent ID in CIDB, use in following order
            if len(parse["name_info"]["Nombor Pendaftaran"]) > 1:
                entity_id = parse["name_info"]["Nombor Pendaftaran"]
                entity_schema = "CIDB-registered"
            elif len(parse["name_info"]["ROB"]) > 1:
                entity_id = parse["name_info"]["ROB"]
                entity_schema = "CIDB-ROB"
            elif len(parse["name_info"]["ROC"]) > 1:
                entity_id = parse["name_info"]["ROC"]
                entity_schema = "CIDB-ROC"
            else:
                # if all above fail, use meta id that always exist
                entity_id = parse["meta"]["id"]
                entity_schema = "CIDB-META"
        else:
            pass # use default values for empty firm
    elif parse["#has_type"] == "person":
        # check content of global variable OBJ_LINK
        if len(OBJ_LINK["firm"]) != 0:
            entity_id = OBJ_LINK["firm"]["party_id"]
            entity_schema = OBJ_LINK["firm"]["party_schema"]
        else:
            # DEBUG: Must prep data by party_identifier beforehand
            raise ValueError('No data from party_identifier', parse)
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    # assign data into identifier fields
    entity_identifier_data = {
        "id": entity_id,
        "schema": entity_schema
    }
    return entity_identifier_data

def entity_address(parse):
    # parse data for address in entity
    address_type = ""
    # Use HINT to assign type of address
    if "#has_type" in parse:
        address_type = parse["#has_type"]
    else:
        # DEBUG: Ensure firm addresses have HINT in compile_entity
        raise ValueError('Unexpected HINT in parse data', parse)
    address_name = ""
    if len(parse["Alamat"]) != 0:
        address_name = address_name + parse["Alamat"]
    if len(parse["Alamat 1"]) != 0:
        address_name = address_name + ", " + parse["Alamat 1"]
    if len(parse["Alamat 2"]) != 0:
        address_name = address_name + ", " + parse["Alamat 2"]
    if len(parse["Bandar"]) != 0:
        address_name = address_name + ", " + parse["Bandar"]
    if len(parse["Negeri"]) != 0:
        address_name = address_name + ", " + parse["Negeri"]
    address_postcode = parse["Poskod"]
    # assign data into address fields
    entity_address_data = {
        "type": address_type,
        "address": address_name,
        "postCode": address_postcode,
        "country": "MY"
    }
    return entity_address_data

def bods_entity(parse):
    # parse data for each entity
    generated_date = parse["generated_date"] # from bods_statement
    entity_type = "arrangement"
    entity_name = "Joint shareholding"
    entity_date = "" # no founding date in source
    identifier_list = []
    identifier_list.append(entity_identifier(parse))
    address_list = []
    # Use HINT to overwrite default values, if any
    if parse["#has_type"] == "firm":
        if parse["#has_data"] == "yes":
            entity_type = "registeredEntity"
            entity_name = parse["name"]
            address_list.append(entity_address(parse["addr"]))
            address_list.append(entity_address(parse["addr_ssm"]))
        else:
            entity_type = "unknownEntity"
            entity_name = ""
    elif parse["#has_type"] == "person":
        if parse["#has_data"] == "yes":
            pass # use default values for existing person
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    # assign data into entity fields
    entity_data = {
        "id": uuid.uuid4().hex,
        "statementDate": generated_date,
        "type": entity_type,
        "name": entity_name,
        "identifiers": identifier_list,
        "foundingDate": entity_date,
        "jurisdiction": "MY"
    }
    # assign data to additional field for firm regardless
    if parse["#has_type"] == "firm":
        entity_data["addresses"] = []
        for address in address_list:
            entity_data["addresses"].append(address)
    return entity_data

def bods_interest(parse):
    # parse data for each interest
    interest_type = "shareholding"
    interest_level = "direct"
    share_value = 100
    # Use HINT to overwrite default values, if any
    if parse["#has_type"] == "firm":
        if parse["#has_person"] == "yes":
            pass # use default values for existing firm with director
    elif parse["#has_type"] == "person":
        if parse["#has_data"] == "yes" and \
           len(parse["shares"]) != 0:
            share_value = parse["shares"]
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    # assign data into interest fields
    interest_data = {
        "type": interest_type,
        "interestLevel": interest_level,
        "share": {
            "exact": float(share_value)
        }
    }
    return interest_data

def bods_statement(parse):
    # parse data for each statement
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    parse["generated_date"] = now # save for later reuse
    interested_party = {}
    interested_party = bods_party(parse)
    entity = {}
    entity = bods_entity(parse)
    interest_list = []
    # use HINT to determine if interests should remain empty
    if parse["#has_type"] == "firm":
        if parse["#has_person"] == "yes":
            interest_list.append(bods_interest(parse))
    elif parse["#has_type"] == "person":
        if parse["#has_data"] == "yes":
            interest_list.append(bods_interest(parse))
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected HINT in parse data', parse)
    # assign data into statement fields
    statement_data = {
        "id": uuid.uuid4().hex,
        "statementDate": now,
        "entity": entity,
        "interestedParty": interested_party,
        "interests": interest_list
    }
    return statement_data

def check_person(parse):
    # check if "directors" field exist
    result = None # assume not found first
    for field in parse:
        if "directors" in field:
            result = "yes" # overwrite result if found
    return result

def compile_person(parse):
    data = {}
    result = check_person(parse)
    # generate statement from directors details
    statement_list = []
    if isinstance(result, type(None)) or \
       len(parse["directors"]) == 0:
        pass # no statement for empty director
    elif len(parse["directors"]) >= 1:
        for data in parse["directors"]:
            data["#has_type"] = "person" # HINT: One-off use
            data["#has_data"] = "yes" # HINT: One-off use
            statement = bods_statement(data)
            statement_list.append(statement)
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected content in parse data', parse)
    return statement_list

def compile_entity(parse):
    data = {}
    # check if "name" field contain valid string; assuming if valid,
    # other fields would have some details if not all
    if len(parse["name"]) == 0:
        data["#has_type"] = "firm" # HINT: One-off use
        data["#has_data"] = "no" # HINT: One-off use
    elif len(parse["name"]) != 0:
        data["#has_type"] = "firm" # HINT: One-off use
        data["#has_data"] = "yes" # HINT: One-off use
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected content in parse data', parse)
    # gather firm details and alternative naming for parse data
    data["meta"] = parse["meta"] # fallback identifier for entity
    data["name"] = parse["name"]
    data["name_info"] = parse["Profil"]
    data["addr"] = parse["Alamat Surat Menyurat"]
    data["addr"]["#has_type"] = "residence" # HINT: One-off use
    data["addr_ssm"] = parse["Alamat Berdaftar seperti Didalam Sijil SSM"]
    data["addr_ssm"]["#has_type"] = "registered" # HINT: One-off use
    # check if director details are available and insert HINT
    result = check_person(parse)
    if isinstance(result, type(None)) or \
       len(parse["directors"]) == 0:
        data["#has_person"] = "no" # HINT: One-off use
    elif len(parse["directors"]) >= 1:
        data["#has_person"] = "yes" # HINT: One-off use
    else:
        # DEBUG: This should not happen
        raise ValueError('Unexpected content in parse data', parse)
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
    # DEBUG: BODS list should contain at least one statement
    if len(bods_list) < 1:
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
