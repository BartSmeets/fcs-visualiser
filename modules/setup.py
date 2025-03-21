from datetime import datetime
import toml
import os

def setup():
    today = datetime.now()
    toStore = {
        'directory': os.environ.get('HOMEPATH'),
        'calibration': {
            'a': 0.09949062,
            'k': 0.23745731
            },
        'logbook': {
            today.isoformat(): {
                'a': 0.09949062,
                'k': 0.23745731
                }
            }
        }

    with open('defaults.toml', "w") as toml_file:
        toml.dump(toStore, toml_file)
    return