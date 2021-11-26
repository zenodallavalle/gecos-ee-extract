from bs4 import BeautifulSoup
from decimal import Decimal
import json
import os
import pandas as pd
import pyperclip
import re

EEE_RUN_MODE = os.environ.get('EEE_RUN_MODE', 'production')

with open('dictionary.json', 'rb') as f:
    dictionary = json.load(f)
with open('duplicated.json', 'rb') as f:
    duplicated = json.load(f)


def parseId(x):
    if x:
        id = x.attrs['id'].replace('§', '-')
        return duplicated.get(id, id)


def parseName(x):
    if x:
        try:
            return x.attrs['title']
        except KeyError:
            return x.text.strip()


def parseValue(x):
    if x:
        try:
            dry_text = x.text.replace('*', '').strip()
            return Decimal(dry_text)
        except Exception as e:
            return dry_text


def gen_column_name(columns):
    column_names = []
    for i, col in enumerate(columns):
        if i == 0:
            column_names.append(0)
        elif i == 1:
            column_names.append(1)
        else:
            column_names.append(col.text.strip())
    return column_names


def transform_rows(row):
    row_values = []
    for i, x in enumerate(row):
        if i == 0:
            row_values.append(parseId(x))
            row_values.append(parseName(x))
        elif i == 1:
            splitted = x.text.rsplit('[', 1)
            if len(splitted) == 2:
                if splitted[0].strip() != '':
                    row_values.append(splitted[0].strip())
                else:
                    row_values.append(parseName(x))
                row_values.append(splitted[1].replace(']', '').strip())
            else:
                row_values.append(parseName(x))
                row_values.append('')
        else:
            row_values.append(parseValue(x))
    return row_values


def loadDF(file):
    folder = 'sample' if EEE_RUN_MODE == 'development' else 'source'
    with open(f'{folder}/{file}.html', 'rb') as f:
        bs = BeautifulSoup(f.read(), 'lxml')
        table = bs.find('table', {'id': 'tabRisultati'})
        trs = table.find_all('tr')
        df = pd.DataFrame([tr.find_all(re.compile('^t[dh]$')) for tr in trs])
        df.columns = gen_column_name(df.loc[0])
        df.drop([0], inplace=True)
        left_df = df[[0, 1]].apply(
            transform_rows, result_type='expand', axis=1)
        left_df.columns = ['id', 'name', 'name2', 'unit']
        right_df = df[df.columns[2:]].applymap(parseValue)
        df = left_df.join(right_df)
    return df


def compile_value(df, id):
    def get_instructions(id):
        instructions = dictionary.get(id, None)
        if not instructions:
            print(
                f'Skipping exam with id {id} as was not found in dictionary.')
        return instructions

    def transform(value, unit, instructions):
        transformer = instructions.get('transformer', None)
        transformed_unit = instructions.get('transformedUnit', None)
        transformed_float_precision = instructions.get(
            'transformedFloatPrecision', None)
        if transformer or transformed_unit:
            if transformer is None and transformed_unit is None:
                print(
                    f'Analyzing id {id}, missing transformer or transformedUnit, make sure dictionary has them both')
            else:
                if transformed_float_precision is None:
                    print(
                        f'Analyzing id {id}, transformedFloatPrecision was not specified, using default = 2')
                    transformed_float_precision = 2
                command = transformer.replace('x', str(value))
                try:
                    new_value = Decimal(round(eval(
                        command)*(10**transformed_float_precision)))/(10**transformed_float_precision)
                    return new_value, transformed_unit
                except Exception as e:
                    print(f'Analyzing {id} exception during transformation.')
                    print(f'Executed command was: "{command}"')
                    print(e)
        return value, unit

    def retrieve_value(df, id, unit=None, mode='left'):
        def first_decimal(serie):
            for x in serie:
                if isinstance(x, Decimal):
                    return x

        results_df = df[df['id'] == id]
        for serie in results_df.itertuples():
            try:
                _unit = serie.unit or ''
            except KeyError:
                _unit = ''
            _unit = _unit.encode('utf-8').replace(b'\xc2\xb5',
                                                  'u'.encode('utf-8')).decode('utf-8').lower().strip()
            if unit:
                if _unit == unit.lower().strip():
                    return first_decimal(serie)
            else:
                return first_decimal(serie)

    instructions = get_instructions(id)
    if instructions is None:
        return
    displayed_name = instructions.get('displayedName', instructions['name'])
    expected_unit = instructions.get('unit', None)
    if expected_unit is None:
        print(
            f'Skipping {displayed_name} [{id}] as its unit was not defined in dictionary.')
        return
    try:
        value = retrieve_value(df, id, unit=expected_unit)
        # apply transformer if available
        value, unit = transform(value, expected_unit, instructions)
        if value is None:
            raise KeyError
        spaced_unit = f' {unit}' if unit else ''
        compiled = '{}: {}{}'.format(displayed_name, value, spaced_unit)
        return compiled
    except KeyError:
        print(f'Skipping {displayed_name} as its value was not found.')
        pass


def apply(df, template='default'):
    output_lines = []
    with open(f'templates/{template}.json', 'rb') as f:
        lines = json.load(f)
        for line in lines:
            output_chunks = []
            for chunk in line:
                # Everything after # is considered a comment
                chunk = chunk.split('#')[0]
                if '$' in chunk:
                    # this is a free text chunk, delete $ and go on
                    output_chunks.append(chunk.replace('$', ''))
                else:
                    # this is a real chunk
                    id = chunk
                    compiled_value = compile_value(df, id)
                    if compiled_value is not None:
                        output_chunks.append(compiled_value)

            if len(output_chunks) > 0:
                output_lines.append('{}.'.format(', '.join(output_chunks)))
    output = os.linesep.join([f'- {l}' for l in output_lines])
    pyperclip.copy(output)
    print('Copyed to clipboard!')
    input('Type enter to close this window')
    return output
