"""
comer_contact_notes/cli.py

CLI for upload_contact_notes.py, creating Contact Notes at Noble from Comer.
"""

import argparse

from src import upload_contact_notes


def push_contact_notes(infile_path, output_dir=".", sandbox=False):
    """
    Upload Comer Contact Notes data, and print path to file containing
    details on newly created Contact Notes.
    """
    new_noble_contact_notes = upload_contact_notes(
        infile_path, output_dir, sandbox
    )
    print(f"Details on new Contact Notes saved to {new_noble_contact_notes}")


def parse_args():
    """
    * input_file: the Comer Contact Notes file, as csv
    *  --sandbox: if given, try running on Salesforce sandbox
    """
    parser = argparse.ArgumentParser(description=\
        "Run the Comer Contact Notes upload from the passed csv"
    )
    parser.add_argument(
        "input_file",
        type=argparse.FileType("r"),
        help="Contact Notes csv file",
    )
    parser.add_argument(
        "--sandbox", "-s",
        action="store_true",
        default=False,
        help="If passed, uses the sandbox Salesforce instance. Defaults to live",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    push_contact_notes(args.input_file.name, sandbox=args.sandbox)
