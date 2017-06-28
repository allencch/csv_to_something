#!/bin/env python
import sys
import csv
import sqlite3
import os.path
import re
from optparse import OptionParser
import json


PROGNAME = 'csv_to_something'


######################
# CSV
######################


def csv_read(filename):
    f = open(filename, 'r')

    reader = csv.reader(f, delimiter=',', quotechar='"')
    header = None
    data = []
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


##################
# SQlite
##################


def get_root_name(filename):
    filename = os.path.basename(filename)
    return os.path.splitext(filename)[0]


def get_table_name(filename):
    table_name = get_root_name(filename)
    return re.compile('^(\d)|[!-\.]').sub(r'_\1', table_name)


def column_type_to_affinity(column_type):
    if column_type == 'float':
        return 'NUMERIC'
    elif column_type == 'boolean':
        return 'INTEGER'
    else:
        return 'TEXT'


def sqlite_create_table(cursor, table_name, header, column_types):
    sql = 'CREATE TABLE IF NOT EXISTS `{}` ( '.format(table_name)
    for i, v in enumerate(header):
        if i == len(header) - 1:
            sql += '"{}" {} )'.format(v.strip(), column_type_to_affinity(column_types[i]))
            break
        sql += '"{}" {}, '.format(v.strip(), column_type_to_affinity(column_types[i]))

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


def is_integer(s):
    try:
        int(s)
        return True
    except:
        return False


def sqlite_guess_row_type(row):
    isFloat = True
    isBoolean = True
    for item in row:
        if not is_float(item):
            isFloat = False
        if not is_boolean(item):
            isBoolean = False
    if isFloat:
        return 'float'
    elif isBoolean:
        return 'boolean'
    else:
        return 'string'


def sqlite_guess_column_types(data):
    transposed = transpose_matrix(data)
    column_types = []
    for row in transposed:
        column_types.append(sqlite_guess_row_type(row))
    return column_types


def sqlite_convert_string_to_value(s, datatype):
    if datatype == 'boolean':
        return 1 if re.search(r'^([1yt]|true|yes)$', s.lower().strip()) else 0
    return s


def sqlite_insert_into_table(cursor, table_name, header, data, column_types):
    # Data, in SQLite, by default it only allows 500. So, we cannot add too much
    # Just a special note. `sqliteman` cannot see the column with the name with dot. But `sqlitebrowser` can open.
    sql = 'INSERT INTO `{}` VALUES ('.format(table_name)
    for j, row in enumerate(data):
        for i, v in enumerate(row):
            value = sqlite_convert_string_to_value(v.replace('"', '""').strip(), column_types[i])

            if i == len(header) - 1:
                sql += '"{}" ) '.format(value)

                if (j + 1) % 500 == 0 and j < len(data) - 1:  # need to close then repeat
                    cursor.execute(sql)
                    sql = 'INSERT INTO `{}` VALUES ('.format(table_name)

                elif j < len(data) - 1:
                    sql += ', ('

                break
            sql += '"{}", '.format(value)
    cursor.execute(sql)


def sqlite_save(input_file, output_file, header, data):
    conn = sqlite3.connect(output_file)
    c = conn.cursor()
    table_name = get_table_name(input_file)
    column_types = sqlite_guess_column_types(data)

    sqlite_create_table(c, table_name, header, column_types)
    sqlite_insert_into_table(c, table_name, header, data, column_types)
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
    return tables


##################
# JSON
##################

def is_boolean(s):
    return re.search(r'^([01yntf]|true|false|yes|no)$', s.lower().strip())


def json_guess_row_type(row):
    isFloat = True
    isBoolean = True
    isInteger = True
    for item in row:
        if not is_float(item):
            isFloat = False
        if not is_integer(item):
            isInteger = False
        if not is_boolean(item):
            isBoolean = False
    if isFloat and not isInteger:
        return 'float'
    elif isInteger:
        return 'integer'
    elif isBoolean:
        return 'boolean'
    else:
        return 'string'


def json_convert_string_to_value(s, datatype):
    if datatype == 'boolean':
        return True if re.search(r'^([1yt]|true|yes)$', s.lower().strip()) else False
    elif datatype == 'float':
        return float(s)
    elif datatype == 'integer':
        return int(s)
    else:
        return str(s)


def json_guess_column_types(data):
    transposed = transpose_matrix(data)
    column_types = []
    for row in transposed:
        column_types.append(json_guess_row_type(row))
    return column_types


def convert_to_list(header, data, column_types):
    l = []
    for row in data:
        d = {}
        for i, elem in enumerate(row):
            d[header[i]] = json_convert_string_to_value(elem, column_types[i])
        l.append(d)
    return l


def json_save(output_file, header, data):
    column_types = json_guess_column_types(data)
    l = convert_to_list(header, data, column_types)
    with open(output_file, 'w') as f:
        json.dump(l, f, indent="  ")
        f.write('\n')


def convert_dicts_to_list(dicts):
    if len(dicts) == 0:
        return []
    header = list(dicts[0].keys())
    l = [header]
    for d in dicts:
        l.append(list(d.values()))
    return l


##################
# Main
##################


def convert_sqlite_to_csv(sqliteFile, output_dir):
    data = sqlite_read(sqliteFile)
    os.makedirs(output_dir, exist_ok=True)
    csv_save_all(output_dir, data)


def convert_csv_to_sqlite(input_file, output_file):
    header, data = csv_read(input_file)
    sqlite_save(input_file, output_file, header, data)


def convert_csv_to_json(input_file, output_file):
    header, data = csv_read(input_file)
    json_save(output_file, header, data)


def convert_json_to_csv(input_file, output_file):
    with open(input_file, 'r') as f:
        dicts = json.load(f)
        l = convert_dicts_to_list(dicts)
        csv_save(output_file, l)


def main(argv=None):
    parser = OptionParser(usage='usage: %prog [options] input_file output_file. Default option is CSV to SQLite.')
    parser.add_option('--c2s',
                      action='store_true',
                      dest='csv_to_sqlite',
                      help='CSV to SQLite [default]. Usage: {} --c2s input_file output_file'.format(PROGNAME),
                      default=False)
    parser.add_option('--s2c',
                      action='store_true',
                      dest='sqlite_to_csv',
                      help='SQLite to CSV. Usage: {} --s2c input_file output_folder'.format(PROGNAME),
                      default=False)
    parser.add_option('--c2j',
                      action='store_true',
                      dest='csv_to_json',
                      help='CSV to JSON. Usage: {} --c2j input_file output_file'.format(PROGNAME),
                      default=False)
    parser.add_option('--j2c',
                      action='store_true',
                      dest='json_to_csv',
                      help='JSON to CSV. Usage: {} --j2c input_file output_file'.format(PROGNAME),
                      default=False)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('incorrect number of arguments')

    input_file = args[0]
    output_file = args[1]
    if options.sqlite_to_csv:
        convert_sqlite_to_csv(input_file, output_file)
    elif options.csv_to_json:
        convert_csv_to_json(input_file, output_file)
    elif options.json_to_csv:
        convert_json_to_csv(input_file, output_file)
    else:
        convert_csv_to_sqlite(input_file, output_file)


main(sys.argv)
