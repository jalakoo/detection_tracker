# import argparse

import file_manager
import alwaysai
import os

from dotenv import load_dotenv
load_dotenv(verbose=True)


def main():
    # server_token = os.getenv("SERVER_TOKEN")
    # print("app.py: main: token: {}".format(server_token))
    config = file_manager.load_json('alwaysai.app.json')['config']
    alwaysai.start_detection_and_tracking_from_config(config)


if __name__ == "__main__":
    main()
