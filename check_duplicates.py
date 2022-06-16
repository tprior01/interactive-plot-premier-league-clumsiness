import csv
import os
path = "/Users/tom/Documents/Personal/Errors/"
directories =  ['minutes/','redcards/','errors/','pensconceded/']
duplicates_in_file = {}
for directory in directories:
    dir = path + directory
    for entry in os.scandir(dir):
        if ".csv" in entry.name:
            entries = []
            with open(dir + entry.name, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] not in entries:
                        entries.append(row[0])
                    else:
                        duplicates_in_file[entry.name] = row[0]

    for key, val in duplicates_in_file.items():
        print(key, val)