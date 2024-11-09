from os import getenv
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent
MODE = getenv('MODE_DEV', 'RELEASE')


if __name__ == '__main__':
    print(BASE_PATH)
    print(MODE)
