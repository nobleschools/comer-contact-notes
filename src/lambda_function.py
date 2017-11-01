"""
comer_contact_notes/src/lambda_function.py

Lambda wrapper for upload_contact_notes. Creates Contact Notes at Noble where
necessary, and sends reference of their (Noble) Safe IDs to Comer.
"""

def lambda_handler(event, context):
    """"""
    pass
    infile, outfile, sandbox = get_me_args(context)
    noble_safe_ids_file = upload_contact_notes(infile, outfile, sandbox)
    push_to_s3(noble_safe_ids_file, bucket_name)


if __name__ == "__main__":
    pass #?
