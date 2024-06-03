import os

def setup(config):
    config.add_section('defaults')

    directory = os.environ.get('HOMEPATH')
    config.set('defaults', 'directory', directory)
    config.set('defaults', 'a', '0.09949062')
    config.set('defaults', 'k', '0.23745731')

    with open('defaults.ini', 'w') as config_file:
        config.write(config_file)
    return