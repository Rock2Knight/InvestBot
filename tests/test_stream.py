import os
import sys
from dotenv import load_dotenv

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'app/')

from app import stream_client
from config import program_config
TOKEN = os.getenv('TINKOFF_TOKEN')

if __name__ == '__main__':
    programConfig = program_config.ProgramConfiguration("../settings.ini")
    stream_client.setup_stream(programConfig)