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
from optparse import OptionParser


def csv_read(filename):
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


def csv_save(filename, data):
    f = open(filename, 'w')
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for row in data:
        row2 = []
        for x in row:
            row2.append(x)
        writer.writerow(row2)

    f.close()


def csv_save_all(output_dir, data):
    for k, v in list(data.items()):
        filename = os.sep.join([output_dir, k + '.csv'])
        if os.path.isfile(filename):
            os.rename(filename, filename + '~')

        csv_save(filename, v)


def get_root_name(filename):
    filename = os.path.basename(filename)
    return os.path.splitext(filename)[0]


def get_table_name(filename):
    table_name = get_root_name(filename)
    return re.compile('^(\d)|[!-\.]').sub(r'_\1', table_name)


def sqlite_create_table(cursor, table_name, header, column_types):
    sql = 'CREATE TABLE IF NOT EXISTS `{}` ( '.format(table_name)
    for i, v in enumerate(header):
        if i == len(header) - 1:
            sql += '"{}" {} )'.format(v.strip(), column_types[i])
            break
        sql += '"{}" {}, '.format(v.strip(), column_types[i])

    cursor.execute(sql)


def transpose_matrix(m):
    new_matrix = [[None for x in m] for y in m[0]]
    for i, row in enumerate(m):
        for j, elem in enumerate(row):
            new_matrix[j][i] = elem
    return new_matrix


def is_float(s):
    try:
        float(s)
        return True
    except:
        return False


def guess_row_type(row):
    isFloat = True
    for item in row:
        if not is_float(item):
            isFloat = False
    if isFloat:
        return 'NUMERIC'
    else:
        return 'TEXT'


def guess_column_types(data):
    transposed = transpose_matrix(data)
    column_types = []
    for row in transposed:
        column_types.append(guess_row_type(row))
    return column_types


def sqlite_insert_into_table(cursor, table_name, header, data):
    # Data, in SQLite, by default it only allows 500. So, we cannot add too much
    # Just a special note. `sqliteman` cannot see the column with the name with dot. But `sqlitebrowser` can open.
    sql = 'INSERT INTO `{}` VALUES ('.format(table_name)
    for j, row in enumerate(data):
        for i, v in enumerate(row):
            if i == len(header) - 1:
                sql += '"{}" ) '.format(v.replace('"', '""').strip())

                if (j + 1) % 500 == 0 and j < len(data) - 1:  # need to close then repeat
                    cursor.execute(sql)
                    sql = 'INSERT INTO `{}` VALUES ('.format(table_name)

                elif j < len(data) - 1:
                    sql += ', ('

                break
            sql += '"{}", '.format(v.replace('"', '""').strip())
    cursor.execute(sql)


def sqlite_save(input_file, output_file, header, data):
    conn = sqlite3.connect(output_file)
    c = conn.cursor()
    table_name = get_table_name(input_file)
    column_types = guess_column_types(data)

    sqlite_create_table(c, table_name, header, column_types)
    sqlite_insert_into_table(c, table_name, header, data)
    conn.commit()
    c.close()
    conn.close()


def sqlite_read(filename):
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
    data = sqlite_read(sqliteFile)
    os.makedirs(output_dir, exist_ok=True)
    csv_save_all(output_dir, data)
    print('Convert sqlite to CSV done')


def convert_csv_to_sqlite(input_file, output_file):
    header, data = csv_read(input_file)
    sqlite_save(input_file, output_file, header, data)


def main(argv=None):
    parser = OptionParser(usage='usage: %prog [options] input_file output_file')
    parser.add_option('-R', '--reverse', action='store_true', dest='reverse', help='SQLite to CSV. Usage: csv2sqlite -R input_file output_folder', default=False)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('incorrect number of arguments')

    input_file = args[0]
    output_file = args[1]
    if options.reverse:
        convert_sqlite_to_csv(input_file, output_file)
    else:
        convert_csv_to_sqlite(input_file, output_file)


main(sys.argv)
