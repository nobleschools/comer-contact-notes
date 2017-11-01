"""
comer_contact_notes/src/upload_contact_notes.py

Define upload_contact_notes function, which:
    - creates Noble Contact Notes where existing at Comer, but not Noble
    - saves report of new (Noble) Contact Note Safe IDs to send back to Comer

"""

import csv
from datetime import date
from itertools import chain
from os import path

from salesforce_fields import contact_note as contact_note_fields
from salesforce_fields import contact as contact_fields
from salesforce_utils import (
    get_salesforce_connection,
    make_salesforce_datestr,
    salesforce_gen,
)
from salesforce_utils.constants import CAMPUS_SF_IDS
from salesforce_utils.constants import COMER

from noble_logging_utils.papertrail_logger import (
    get_logger,
    SF_LOG_LIVE,
    SF_LOG_SANDBOX,
)

COMER_ACCOUNT_ID = CAMPUS_SF_IDS[COMER]

# using data from below headers for Contact Note objects
NOBLE_CONTACT_SF_ID = "Noble SF ID Contact"
NOBLE_CONTACT_NOTE_SF_ID = "Noble SF ID Contact Note"
COMMENTS = "Comments"
COMM_STATUS = "Communication Status"
DATE_OF_CONTACT = "Date of Contact"
DISCUSSION_CATEGORY = "Discussion Category"
INITIATED_BY_ALUM = "Initiated by alum"
MODE = "Mode of Communication"
SUBJECT = "Subject"

COMER_CONTACT_NOTE_SF_ID = "Contact Note: ID"

SOURCE_DATESTR_FORMAT = "%m/%d/%y"
OUTFILE_DATESTR_FORMAT = "%Y%m%d"

# simple_salesforce.Salesfoce.bulk operation result keys
SUCCESS = "success" # bool
ERRORS = "errors"   # list
ID_RESULT = "id"    # str safe id
CREATED = "created" # bool


def upload_contact_notes(infile_path, output_dir, sandbox=False):
    """
    ...

    :pararm infile_path: str path to the input file
    :param output_dir: str path to the directory in which output file is saved
    :param sandbox: (optional) bool whether or not to use the sandbox
        Salesforce instance
    :return: path to output csv file
    :rtype: str
    """
    sandbox = True # XXX for dev
    global sf_connection
    sf_connection = get_salesforce_connection(sandbox=sandbox)
    job_name = __file__.split(path.sep)[-1]
    hostname = SF_LOG_SANDBOX if sandbox else SF_LOG_LIVE
    global logger
    logger = get_logger(job_name, hostname=hostname)

    for_bulk_create = []

    with open(infile_path, "r") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            # standard with exported Salesforce reports, expecting a blank row
            # after the data before footer metadata rows
            if _is_blank_row(row):
                break

            # likely means it's a GCYC alum
            if not row[NOBLE_CONTACT_SF_ID]:
                continue

            if not row[NOBLE_CONTACT_NOTE_SF_ID]:
                for_bulk_create.append(row)

    created_results = _create_contact_notes(for_bulk_create)
    _save_created_report(created_results, output_dir, for_bulk_create)

    return "output_filename.csv" #??


def _save_created_report(results_list, output_dir, args_dicts):
    """Save a csv report of newly-created Contact Notes to send to Comer.

    Save only new (to Noble) Contact Notes, skipping any that were passed on
    (eg. possible duplicate found).

    :param results_list: list of result dicts
    :param output_dir: str path to directory where to save report file
    :param args_dicts: iterable of original args_dicts, to pull college SF ID
    :return: None
    """
    today_datestr = date.today().strftime(OUTFILE_DATESTR_FORMAT)
    filename = f"New_Noble_Contact_Notes_{today_datestr}.csv"
    file_path = path.join(output_dir, filename)

    report_headers = (
        NOBLE_CONTACT_NOTE_SF_ID,
        COMER_CONTACT_NOTE_SF_ID,
    )

    if results_list:
        headers = report_headers
        with open(file_path, "w") as fhand:
            writer = csv.DictWriter(
                fhand, fieldnames=headers, extrasaction="ignore"
            )
            writer.writeheader()
            for result, args_dict in zip(results_list, args_dicts):
                if result[SUCCESS] == True:
                    # mapping back from Salesforce to source headers for Comer
                    result[NOBLE_CONTACT_NOTE_SF_ID] = result[ID_RESULT]
                    writer.writerow(result)
    else:
        with open(file_path, "w") as fhand:
            writer = csv.Writer(fhand)
            writer.writerow("No new Noble Contact Note objects saved.")

    logger.info(f"Saved new Noble Contact Notes report to {file_path}")


def _create_contact_notes(data_dicts):
    """Create new Contact Notes after converting row to Salesforce-ready data
    dicts, and add Comer's 'Contact Note: ID' to the results.

    First checks for existing Notes with the same Contact (alum), Date of
    Contact, and Subject, and skip if one is found.

    The returned results format should otherwise mimic the format returned by
    ``simple-salesforce.Salesforce.bulk`` operations; ie. the following keys:
        - 'id'
        - 'success'
        - 'errors'
        - 'created'
        - COMER_CONTACT_NOTE_SF_ID

    :param data_dicts: iterable of dictionaries to create
    :return: list of results dicts
    :rtype: list
    """
    results = []
    for contact_note_dict in data_dicts:
        comer_id = contact_note_dict[COMER_CONTACT_NOTE_SF_ID]
        salesforce_ready = _prep_row_for_salesforce(contact_note_dict)
        result = get_or_create_note(salesforce_ready)
        # not added by non-bulk `create` call
        if result[SUCCESS]:
            result[CREATED] = True
        else:
            result[CREATED] = False
        result[COMER_CONTACT_NOTE_SF_ID] = comer_id
        results.append(result)

    _log_results(results, CREATE, data_dicts)
    return results


def get_or_create_note(contact_note_dict):
    """Look for an existing Contact Note with the same Contact, Subject, and
    Date of Contact fields. Return that if exists, otherwise create.

    :param contact_note_dict: dictionary of Contact Note details, with keys
        already mapped to Salesforce API fieldnames and dates API-ready
    :return: results dict (keys 'id', 'success', 'errors')
    :rtype: dict
    """
    alum_sf_id = contact_note_dict[contact_note_fields.CONTACT]
    subject = contact_note_dict[contact_note_fields.SUBJECT]
    date_of_contact = contact_note_dict[contact_note_fields.DATE_OF_CONTACT]
    contact_note_query = (
        f"SELECT {contact_note_fields.ID} "
        f"FROM {contact_note_fields.API_NAME} "
        f"WHERE {contact_note_fields.CONTACT} = '{alum_sf_id}' "
        f"AND {contact_note_fields.SUBJECT} = '{subject}' "
        f"AND {contact_note_fields.DATE_OF_CONTACT} = {date_of_contact} "
    )

    results = sf_connection.query(contact_note_query)
    if results["totalSize"]:
        # doesn't matter if more than one, needs manual intervention regardless
        existing_sf_id = results["records"][0]["Id"]
        logger.error(
            f"Conflicting Contact Note {existing_sf_id} found for "
            f"{contact_note_dict}. Skipping creation"
        )
        return {
            ID_RESULT: existing_sf_id,
            SUCCESS: False,
            ERRORS: [f"Found conflicting Contact Note {existing_sf_id}",],
        }

    return sf_connection.Contact_Note__c.create(contact_note_dict)


def _log_results(results_list, action, original_data):
    """Log results from Contact Note create action.

    Log results from create_contact_notes. Input results_list structured as
    if it were a ``simple_salesforce.Salesforce.bulk`` call for compatability
    with bulk updates and deletes. Expects the following keys in
    results_list dicts:
        - success
        - id
        - created
        - errors

    :param results_list: list of result dicts, mimicking
        ``simple_salesfoce.Salesforce.bulk`` result
    :param action: str action taken ('create', 'update', 'delete')
    :param original_data: list of original data dicts from the input file
    :rtype: None
    """
    logger.info(f"Logging results of bulk Contact Note {action} operation..")
    attempted = success_count = fail_count = 0
    for result, args_dict in zip(results_list, original_data):
        attempted += 1
        if not result[SUCCESS]:
            fail_count += 1
            log_payload = {
                "action": action,
                ID_RESULT: result[ID_RESULT],
                ERRORS: result[ERRORS],
                "arguments": args_dict,
            }
            logger.error(f"Failed Contact Note {action}: {log_payload}")
        else:
            success_count += 1
            logger.info(f"Successful Contact Note {action}: {result['id']}")

    logger.info(
        f"Contact Note {action}: {attempted} attempted, "
        f"{success_count} succeeded, {fail_count} failed."
    )


def _prep_row_for_salesforce(row_dict):
    """Change keys in row_dict to Salesforce API field names, and convert
    data where necessary.

    Changes keys in the row_dict to Salesforce API fieldnames, filtering out
    irrelevant keys (ie. those outside of the FIELD_CONVERSIONS lookup).
    After converting the keys, also checks for datetime fields and converts
    their values to Salesforce API-ready datestrings.

    :param row: dict row of Contact Note data
    :return: new dict ready for Salesforce bulk action
    :rtype: dict
    """
    # maps input headers to Salesforce field API names
    FIELD_CONVERSIONS = {
        NOBLE_CONTACT_SF_ID: contact_note_fields.CONTACT,
        COMMENTS: contact_note_fields.COMMENTS,
        COMM_STATUS: contact_note_fields.COMMUNICATION_STATUS,
        DATE_OF_CONTACT: contact_note_fields.DATE_OF_CONTACT,
        DISCUSSION_CATEGORY: contact_note_fields.DISCUSSION_CATEGORY,
        INITIATED_BY_ALUM: contact_note_fields.INITIATED_BY_ALUM,
        MODE: contact_note_fields.MODE_OF_COMMUNICATION,
        SUBJECT: contact_note_fields.SUBJECT,
    }

    new_dict = dict()
    for source_header, api_name in FIELD_CONVERSIONS.items():
        datum = row_dict.get(source_header, None)
        if datum:
            new_dict[api_name] = datum

    date_fields = (
        contact_note_fields.DATE_OF_CONTACT,
    )
    for date_field in date_fields:
        source_datestr = new_dict.get(date_field, None)
        if source_datestr:
            salesforce_datestr = make_salesforce_datestr(
                source_datestr, SOURCE_DATESTR_FORMAT
            )
            new_dict[date_field] = salesforce_datestr

    return new_dict


def _is_blank_row(row_dict):
    """Checks if row is blank, signaling end of data in spreadsheet.

    Reports from Salesforce are generated with footer rows at the end,
    separated from the actual report data by one blank row.
    """
    return all(v == "" for v in row_dict.values())


if __name__ == "__main__":
    pass