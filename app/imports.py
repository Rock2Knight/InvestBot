import sys
import os
from dotenv import load_dotenv
import logging
import asyncio
import math
import multiprocessing as mp
import csv
import time
from datetime import datetime, timedelta, timezone

load_dotenv()
main_path = os.getenv('MAIN_PATH')
TOKEN = os.getenv('TINKOFF_TOKEN')
sys.path.append(main_path)
sys.path.append(main_path+'app/')

from config import program_config
from utils_funcs import utils_funcs