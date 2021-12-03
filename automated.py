import os
import utils
import json

def sources(settings):
    settings_source=settings.get('source', None)
    if settings_source:
        print(f"Using settings\' source: {settings_source}")
        yield settings_source
        return
    else:
        print('Iterating source/ files')
        for file in os.listdir('source'):
            if os.path.isfile(os.path.join('source', file)) and 'html' in file:
                yield file
        print('No source found! Make sure in source folder there is a .html file.')

def get_template(settings):
    settings_template=settings.get('template', None)
    if settings_template:
        print(f"Using settings\' template: {settings_template}")
        return settings_template
    else:
        for file in os.listdir('templates'):
            if os.path.isfile(os.path.join('templates', file)) and 'json' in file:
                template = file.rsplit('.', 1)[0]
                print(f'Using the first json available in templates/ as template: {template}')
                return template
        print('No templates available.')
        input('Type enter to exit.')
        raise ValueError

def main():
    with open('settings.json', 'r') as f:
        settings = json.load(f)
    
    for source in sources(settings):
        print(f'Analyzing {source}')
        filename = source.split('.', 1)[0]
        df = utils.loadDF(filename)
        _ = utils.apply(df, template=get_template(settings))
        input('Type enter to close this window')
        return
    print()
    print('FAILURE')
    print('If you are seeing this the process failed. Check the above messages please.')


if __name__ == '__main__':
    main()
