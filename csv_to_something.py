#!/bin/env python

"""Module provides function to convert CSV, JSON and SQLite"""

import sys
import csv
import sqlite3
import os.path
import re
from argparse import ArgumentParser
import json


PROGNAME = 'csv_to_something'


######################
# CSV
######################


def csv_read(filename):
    with open(filename, 'r', encoding="utf-8") as f:
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
    with open(filename, 'w', encoding="utf-8") as f:
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
    return re.compile(r'^(\d)|[!-\.]').sub(r'_\1', table_name)


def column_type_to_affinity(column_type):
    if column_type == 'float':
        return 'NUMERIC'
    if column_type == 'boolean':
        return 'INTEGER'
    return 'TEXT'


def sqlite_create_table(cursor, table_name, header, column_types):
    sql = f'CREATE TABLE IF NOT EXISTS `{table_name}` ( '
    for i, v in enumerate(header):
        if i == len(header) - 1:
            sql += f'"{v.strip()}" {column_type_to_affinity(column_types[i])} )'
            break
        sql += f'"{v.strip()}" {column_type_to_affinity(column_types[i])}, '

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
    # pylint: disable=broad-exception-caught
    except Exception:
        return False
    # pylint: enable=broad-exception-caught


def is_integer(s):
    try:
        int(s)
        return True
    # pylint: disable=broad-exception-caught
    except Exception:
        return False
    # pylint: enable=broad-exception-caught


def sqlite_guess_row_type(row):
    is_it_float = True
    is_it_boolean = True
    for item in row:
        if not is_float(item):
            is_it_float = False
        if not is_boolean(item):
            is_it_boolean = False
    if is_it_float:
        return 'float'
    if is_it_boolean:
        return 'boolean'
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
    sql = f'INSERT INTO `{table_name}` VALUES ('
    for j, row in enumerate(data):
        for i, v in enumerate(row):
            value = sqlite_convert_string_to_value(
                v.replace('"', '""').strip(), column_types[i])

            if i == len(header) - 1:
                sql += f'"{value}" ) '

                if (j + 1) % 500 == 0 and j < len(data) - 1:  # need to close then repeat
                    cursor.execute(sql)
                    sql = f'INSERT INTO `{table_name}` VALUES ('

                elif j < len(data) - 1:
                    sql += ', ('

                break
            sql += f'"{value}", '
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

    for k, _v in list(tables.items()):
        for row in c.execute(f"select * from `{k}`"):
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
    is_it_float = True
    is_it_boolean = True
    is_it_integer = True
    for item in row:
        if not is_float(item):
            is_it_float = False
        if not is_integer(item):
            is_it_integer = False
        if not is_boolean(item):
            is_it_boolean = False
    if is_it_float and not is_it_integer:
        return 'float'
    if is_it_integer:
        return 'integer'
    if is_it_boolean:
        return 'boolean'
    return 'string'


def json_convert_string_to_value(s, datatype):
    if datatype == 'boolean':
        return re.search(r'^([1yt]|true|yes)$', s.lower().strip())
    if datatype == 'float':
        return float(s)
    if datatype == 'integer':
        return int(s)
    return str(s)


def json_guess_column_types(data):
    transposed = transpose_matrix(data)
    column_types = []
    for row in transposed:
        column_types.append(json_guess_row_type(row))
    return column_types


def convert_to_list(header, data, column_types):
    array = []
    for row in data:
        d = {}
        for i, elem in enumerate(row):
            d[header[i]] = json_convert_string_to_value(elem, column_types[i])
        array.append(d)
    return array


def json_save(output_file, header, data):
    column_types = json_guess_column_types(data)
    array = convert_to_list(header, data, column_types)
    with open(output_file, 'w', encoding="utf-8") as f:
        json.dump(array, f, indent="  ")
        f.write('\n')


def get_all_keys(dicts):
    keys = []
    for row in dicts:
        keys += list(row.keys())
    return list(set(keys))


def unify_dicts(dicts):
    keys = get_all_keys(dicts)
    for i, d in enumerate(dicts):
        for k in keys:
            if k not in d:
                dicts[i][k] = None


def convert_dicts_to_list(dicts):
    unify_dicts(dicts)
    if len(dicts) == 0:
        return []
    header = list(dicts[0].keys())
    row = [header]
    for d in dicts:
        line = []
        for k in header:
            line.append(d[k])
        row.append(line)
    return row


##################
# Main
##################


def convert_sqlite_to_csv(sqlite_file, output_dir):
    data = sqlite_read(sqlite_file)
    os.makedirs(output_dir, exist_ok=True)
    csv_save_all(output_dir, data)


def convert_csv_to_sqlite(input_file, output_file):
    header, data = csv_read(input_file)
    sqlite_save(input_file, output_file, header, data)


def convert_csv_to_json(input_file, output_file):
    header, data = csv_read(input_file)
    json_save(output_file, header, data)


def convert_json_to_csv(input_file, output_file):
    with open(input_file, 'r', encoding="utf-8") as f:
        dicts = json.load(f)
        array = convert_dicts_to_list(dicts)
        csv_save(output_file, array)


def main(argv):
    parser = ArgumentParser(
        prog="PROG",
        usage='%(prog)s [options] input_file output_file. Default option is CSV to SQLite.')
    parser.add_argument('--c2s',
                        action='store_true',
                        dest='csv_to_sqlite',
                        help=f'CSV to SQLite [default]. Usage: {PROGNAME} --c2s input_file output_file',
                        default=False)
    parser.add_argument('--s2c',
                        action='store_true',
                        dest='sqlite_to_csv',
                        help=f'SQLite to CSV. Usage: {PROGNAME} --s2c input_file output_folder',
                        default=False)
    parser.add_argument('--c2j',
                        action='store_true',
                        dest='csv_to_json',
                        help=f'CSV to JSON. Usage: {PROGNAME} --c2j input_file output_file',
                        default=False)
    parser.add_argument('--j2c',
                        action='store_true',
                        dest='json_to_csv',
                        help=f'JSON to CSV. Usage: {PROGNAME} --j2c input_file output_file',
                        default=False)
    parser.add_argument("input_file")
    parser.add_argument("output_file")

    if len(argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    if args.sqlite_to_csv:
        convert_sqlite_to_csv(input_file, output_file)
    elif args.csv_to_json:
        convert_csv_to_json(input_file, output_file)
    elif args.json_to_csv:
        convert_json_to_csv(input_file, output_file)
    else:
        convert_csv_to_sqlite(input_file, output_file)


if __name__ == "__main__":
    main(sys.argv)
