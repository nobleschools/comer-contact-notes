import csv
import re

noble_regex = re.compile(r"'id': '(\w+)'")
comer_regex = re.compile(r"'Contact Note: ID', '(\w+)'")


with open("dupe_notes.txt", "r") as fhand:
    with open("additional_noble_ids.csv", "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Noble ID", "Comer ID"])

        for line in fhand.readlines():
            noble_id = noble_regex.search(line).groups()[0]
            comer_id = comer_regex.search(line).groups()[0]
            writer.writerow([noble_id, comer_id])

