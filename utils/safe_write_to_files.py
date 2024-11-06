import json
import shutil
import os

def create_backup(file_path):
    """
    Create an incrementally numbered backup of the specified file.

    Args:
        file_path (str): The path to the original file.

    Returns:
        str: Path to the created backup file, or None if backup fails.
    """
    # Extract directory, filename, and extension
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    file_name, file_ext = os.path.splitext(base_name)

    # Find the next available backup name
    i = 1
    while True:
        backup_name = f"bk{i}_{file_name}{file_ext}"
        backup_path = os.path.join(dir_name, backup_name)
        if not os.path.exists(backup_path):
            break
        i += 1

    # Copy the file to the new backup path
    try:
        shutil.copy(file_path, backup_path)
        return backup_path
    except IOError:
        return None

def safe_write_to_file(file_path, data):
    """
    Write data to a specified JSON file.

    Args:
        file_path (str): The path to the file to write to.
        data (dict): The data to write to the file.

    Returns:
        bool: True if write was successful, False otherwise.
    """
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        return True
    except IOError:
        return False
