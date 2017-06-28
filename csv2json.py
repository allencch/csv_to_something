#!/bin/env python
'''
@author	Allen Choong Chieng Hoon
@date	2014-05-06
@version	0.1

This script is to make the CSV and SQLite data interchangeable, so that we can use the SQL operation
and edit the CSV with spreadsheet application.
'''
import sys
import csv
import json
import os.path
import re


def csvRead(filename):
    f = open(filename, 'r')

    reader = csv.reader(f, delimiter=',', quotechar='"')
    header = None
    data = []

    header = None
    for i, row in enumerate(reader):
        if i == 0:
            header = row
            continue
        data.append(row)

    f.close()

    return header, data


def csvSave(filename, data):
    f = open(filename, 'w')
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for row in data:
        row2 = []
        for x in row:
            if type(x) is str:
                row2.append(x)
            else:
                row2.append(x.decode())
        writer.writerow(row2)

    f.close()


def csvSaveAll(output_dir, data):
    for k, v in list(data.items()):
        filename = os.sep.join([output_dir, k + '.csv'])
        if os.path.isfile(filename):
            os.rename(filename, filename + '~')

        csvSave(filename, v)


def convert_csv_to_json(csv_file, json_file):
    header, data = csvRead(csv_file)



def main(argv=None):
    if argv is None:
        print("Usage: %s csv_file_(in) json_file_(out)" % argv[0])
        return


    csv_file = argv[2]
    json_file = argv[3]
    convert_csv_to_json(csv_file, json_file)


main(sys.argv)
