import os
import utils


def main():

    for source in os.listdir('source'):
        if 'html' in source:
            print(f'Analyzing {source}')
            filename = source.split('.', 1)[0]
            df = utils.loadDF(filename)
            output = utils.apply(df)
            with open('output.txt', 'w') as f:
                f.write(output)
            return
    print('No source found! Make sure in source folder there is a .html file.')


if __name__ == '__main__':
    main()
