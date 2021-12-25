import os
import utils
import json
from pick import pick
import pyperclip


def get_source(settings):
    settings_source = settings.get('source', None)
    if settings_source:
        print(f"Using settings\' source: {settings_source}")
        return settings_source
    else:
        files = [f for f in os.listdir('source') if os.path.isfile(os.path.join('source', f))]
        if len(files) == 0:
            print('No source found! Make sure in source folder there is a .html file.')
        elif len(files) == 1:
            return files[0]
        else:
            title = 'Please pick a file:'
            files.extend(['', 'EXIT'])
            option, _ = pick(files, title)
            while option == '':
                option, _ = pick(files, title)
            if option != 'EXIT':
                return option


def get_template(settings):
    settings_template = settings.get('template', None)
    if settings_template:
        print(f"Using settings\' template: {settings_template}")
        return settings_template
    else:
        files = [f for f in os.listdir('templates') if os.path.isfile(os.path.join('templates', f))]
        if len(files) == 0:
            print('No templates found! Make sure in templates folder there is a valid .json file.')
        elif len(files) == 1:
            return files[0]
        else:
            title = 'Please choose a template:'
            files.extend(['', 'EXIT'])
            option, _ = pick(files, title)
            while option == '':
                option, _ = pick(files, title)
            if option != 'EXIT':
                return option


def main():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    except Exception as e:
        settings = {}

    source = get_source(settings)
    template=get_template(settings)
    if source and template:
        print(f'Analyzing {source}')
        df = utils.loadDF(source)
        output_text = utils.apply(df, template=template)
        pyperclip.copy(output_text)
        print('Copyied to clipboard.')
    else:
        print()
        print('FAILURE')
        print('If you are seeing this the process failed. Check the above messages please.')
    input('Type enter to close this window...')


if __name__ == '__main__':
    main()
