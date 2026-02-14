import configparser
import os

# Configuration Loading
config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.ini")
config.read(config_path)

# General Settings
FETCH_INTERVAL = config.getint('General', 'FETCH_INTERVAL', fallback=10)
MIL_PREFIX_LIST = [prefix.strip() for prefix in config.get('General', 'MIL_PREFIX_LIST', fallback='7CF').split(',')]
TAR1090_URL = config.get('General', 'TAR1090_URL', fallback='http://localhost/data/aircraft.json')
BLINK_MILITARY = config.getboolean('General', 'BLINK_MILITARY', fallback=True)

# Audio Settings
ATC_STREAM_URL = config.get('Audio', 'ATC_STREAM_URL', fallback='')
ATC_AUTO_START = config.getboolean('Audio', 'AUTO_START', fallback=False)

# Location Settings
LAT = config.getfloat('Location', 'LAT', fallback=0.0)
LON = config.getfloat('Location', 'LON', fallback=0.0)
AREA_NAME = config.get('Location', 'AREA_NAME', fallback='UNKNOWN')
RADIUS_NM = config.getint('Location', 'RADIUS_NM', fallback=60)
# ADDED: This line allows the app to read your facing direction
RADAR_ROTATION = config.getint('Location', 'RADAR_ROTATION', fallback=0)

# Display Settings
SCREEN_WIDTH = config.getint('Display', 'SCREEN_WIDTH', fallback=960)
SCREEN_HEIGHT = config.getint('Display', 'SCREEN_HEIGHT', fallback=640)
FPS = config.getint('Display', 'FPS', fallback=6)
MAX_TABLE_ROWS = config.getint('Display', 'MAX_TABLE_ROWS', fallback=10)
FONT_PATH = config.get('Display', 'FONT_PATH', fallback='fonts/TerminusTTF-4.49.3.ttf')
BACKGROUND_PATH = config.get('Display', 'BACKGROUND_PATH', fallback=None)
TRAIL_MIN_LENGTH = config.getint('Display', 'TRAIL_MIN_LENGTH', fallback=8)
TRAIL_MAX_LENGTH = config.getint('Display', 'TRAIL_MAX_LENGTH', fallback=25)
TRAIL_MAX_SPEED = config.getint('Display', 'TRAIL_MAX_SPEED', fallback=500)
HEADER_FONT_SIZE = config.getint('Display', 'HEADER_FONT_SIZE', fallback=32)
RADAR_FONT_SIZE = config.getint('Display', 'RADAR_FONT_SIZE', fallback=28)
TABLE_FONT_SIZE = config.getint('Display', 'TABLE_FONT_SIZE', fallback=28)
INSTRUCTION_FONT_SIZE = config.getint('Display', 'INSTRUCTION_FONT_SIZE', fallback=28)

# Colours
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BRIGHT_GREEN = (50, 255, 50)
DIM_GREEN = (0, 180, 0)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
AMBER = (255, 191, 0)
