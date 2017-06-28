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
import sqlite3
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


def sqliteSave(filename, header, data):
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    filename = os.path.splitext(filename)[0]
    filename = filename.replace('.', '_').replace('-', '_')
    if re.compile('^\d').match(filename):
        filename = '_' + filename

    sql = 'create table if not exists `%s` ( ' % filename
    for i, v in enumerate(header):
        if i == len(header) - 1:
            sql += '"%s" text )' % v.strip()
            break
        sql += '"%s" text, ' % v.strip()

    c.execute(sql)

    # Data, in SQLite, by default it only allows 500. So, we cannot add too
    # much
    sql = 'insert into `%s` values (' % filename
    for j, row in enumerate(data):

        for i, v in enumerate(row):
            if i == len(header) - 1:
                sql += '"%s" ) ' % v.replace('"', '""').strip()

                if (j + 1) % 500 == 0 and j < len(data) - 1:  # need to close then repeat
                    c.execute(sql)
                    sql = 'insert into `%s` values (' % filename

                elif j < len(data) - 1:
                    sql += ', ('

                break
            sql += '"%s", ' % v.replace('"', '""').strip()

    c.execute(sql)
    conn.commit()
    c.close()
    conn.close()


def sqliteRead(filename):
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    # Get the tables
    tables = {}
    for row in c.execute("select name from sqlite_master where type='table'"):
        tables[row[0]] = []

    for k, v in list(tables.items()):
        for row in c.execute("select * from `%s`" % k):
            tables[k].append(row)
        headers = []
        for h in c.description:
            headers.append(h[0])
        tables[k].insert(0, headers)

    c.close()
    conn.close()
    print(tables)

    return tables


def convert_sqlite_to_csv(sqliteFile, output_dir):
    data = sqliteRead(sqliteFile)
    os.makedirs(output_dir, exist_ok=True)
    csvSaveAll(output_dir, data)
    print('Convert sqlite to CSV done')


def main(argv=None):
    if argv is None:
        print("Usage: %s csv_file_(in) sqlite_file_(out)" % argv[0])
        print("OR")
        print("SQLite to CSV: %s -R sqlite_file csv_dir")
        return

    if argv[1] != '-R':
        csvFile = argv[1]
        sqliteFile = argv[2]
        # Open the CSV
        header, data = csvRead(csvFile)

        # Save to SQLite3
        sqliteSave(sqliteFile, header, data)
    else:
        sqliteFile = argv[2]
        output_dir = argv[3]
        convert_sqlite_to_csv(sqliteFile, output_dir)


main(sys.argv)
