# import argparse

import file_manager
import alwaysai

def main():
    config = file_manager.load_json('alwaysai.app.json')['config']
    alwaysai.start_camera_detection_and_tracking_from_config(config)

if __name__ == "__main__":
    main()
