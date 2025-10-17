import sys
import os
import time
from pyramid.paster import (get_appsettings, setup_logging, )

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def delete_file_if_older(file_path, days_old):
    """
    Deletes a file if it exists and its creation time is older than the specified number of days.

    Args:
        file_path (str): The full path to the file.
        days_old (int): The number of days after which a file is considered old enough to be deleted.
    """
    if os.path.exists(file_path):
        creation_time_timestamp = os.path.getctime(file_path)
        current_time_timestamp = time.time()

        # Calculate the age of the file in seconds
        file_age_seconds = current_time_timestamp - creation_time_timestamp

        # Convert the desired age in days to seconds
        threshold_seconds = days_old * 24 * 60 * 60

        if file_age_seconds > threshold_seconds:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path} (created {days_old} days ago or more)")
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")
        else:
            print(f"File {file_path} exists but is not older than {days_old} days.")
    else:
        print(f"File not found: {file_path}")

def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    captcha_files = settings.get('captcha_files', '/tmp/captcha')
    all_entries = os.listdir(captcha_files)

    # Filter for only files
    files_only = [f for f in all_entries if os.path.isfile(
        os.path.join(captcha_files, f))]

    print(f"Files in '{captcha_files}':")
    for file_name in files_only:
        delete_file_if_older(os.path.join(captcha_files, file_name), 1)

