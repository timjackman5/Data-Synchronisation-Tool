# Get the relevant imports needed
import pathlib
import hashlib
import json
import time
import argparse
import logging

# Set global variables that will be used 
directories = set()
last_sync = 0
increment = 0

# setup logger for logger.infoing output for debugging
logger = logging.getLogger(__name__)

def hash_file(filepath: str):
    """
    Given a filepath, returns the hash of the file

    hashlib.file_digest() function exclusive to python 3.11 and above
    https://docs.python.org/3/library/hashlib.html#file-hashing

    Params:
        filepath of the file to be hashed

    Returns:
        the hex digest hash of a file 
    """
    digest = ''
    try:
        with open(filepath, 'rb') as f:
            logger.debug(f"f: {f}")
            logger.debug(f"type(f): {type(f)}\n")
            
            digest = hashlib.file_digest(f, 'sha256')
            
    except FileNotFoundError as e:
        logger.debug(f"File not found ERROR:{e}")


    return digest.hexdigest()


def prep_file_for_transfer(filepath):
    """
    Given a filepath, return the hash and filepath.

    Params:
        filepath: filepath of file to prep for transfer 

    Returns:
        filepath and hash in dictionary

    """
    # given a file, first get the hash
    hash = hash_file(str(filepath))

    # use absolute paths
    # return {'filepath': str(filepath.resolve()), 'hash': hash}

    # uses working directory paths, 
    return {'filepath': str(filepath), 'hash': hash}


def enumerate_directory(last_sync, path):
    """
    Recursive function that is called on each specified directory
    to sync. Enables calling on sub-directories inside the specified 
    directories. 

    Params:
        last_sync: timestamp of last successful sync
        path: the path of the directory to be enumerated

    Returns: 
        files: list of files 
    """
    global directories
    files = []

    if path.iterdir() is None:
        # empty directory with no files
        pass
    else:

        for item in path.iterdir():
            logger.debug(f"subdir:{item}")

            if item.is_dir():
                logger.debug("it is a subdirectory")
                logger.debug(f"str(sub_dir): {str(item)}")
                
                # If a subdirectory we want to first check if it is already 
                # in the list of directories
                logger.debug(f"'./'+str(item): {'./'+str(item)}")
                logger.debug(f"directories: {directories}")
                logger.debug(f"if './'+str(item) in directories:: {'./'+str(item) in directories:}")
                logger.debug(f"if pathlib.Path('./'+str(item)) in directories:: {pathlib.Path('./'+str(item)) in directories:}\n")
                if pathlib.Path('./'+str(item)) in directories:
                    logger.debug("DIRECTORY ALREADY IN SET\n")
                    pass
                else:
                    files += enumerate_directory(last_sync, item)

                logger.debug(f"files: {files}")

            # if file is newer than the last synced timestamp, add to files list
            if item.is_file():
                logger.debug(f"sub_dir: {item}")
                logger.debug(item.stat())
                logger.debug(f"st_mtime: {item.stat().st_mtime}")
                logger.debug(f"last_sync: {last_sync}")
                logger.debug(f"item.stat().st_mtime > last_sync: {item.stat().st_mtime > last_sync}\n")
                
                # do a comparison on the last edited time of the file 
                if item.stat().st_mtime > last_sync:
                    logger.debug("THIS IS A NEW FILE\n ")
                    
                    # send to prep_for_sending
                    files.append(prep_file_for_transfer(item))
                    
    logger.debug(f"files per directory: {files}\n")
    
    return files 


def timestamp_comparison(last_sync, directories):
    """
    Given a set of directories, current timestamp and last 
    successful sync timestamp starts the process of 
    iterating over directories and checking per file.

    Params:
        last_sync: timestamp of last successful sync
        directories: set of directories to be iterated through 
            to build up list of files

    Returns:
        Data structure to be transferred
    """
    full_files = {}

    # iterate through the original set of directories to sync
    for directory in directories:
        path = pathlib.Path(directory)

        full_files[str(directory)] = enumerate_directory(last_sync, path)

    logger.debug(f"full_files: {full_files}\n")
    
    logger.debug(f"full_files.keys(): {full_files.keys()}\n")

    # return the fill list of files to be transferred per specified directory
    return full_files


def run_sync(directories):
    """
    Runs a synchronisation, iterating through all directories and files 
    to determine which need to be transferred, and then preparing
    them for transfer.  

    Params:
        set of directories to sync

    Returns:
        files ready for syncing
    """
    global last_sync

    time_stamp = time.time()

    # timestamp comparison to determine which files are needed for transfer
    files = timestamp_comparison(last_sync, directories)

    # after a successful sync update the last sync time
    last_sync = time_stamp

    return files


def handle_argparse():  
    """
    Function that handles argparsing, for command line calling of the program

    """
    parser = argparse.ArgumentParser(
        description='Handle cmd line arguements'
    )
    parser.add_argument("directories", type=str, help='Filepath of .txt file with directories to sync')
    parser.add_argument('-l', "-logging", type=str, help='Logging setting (INFO or leave blank)')

    args = parser.parse_args()

    return args


def load_directories(directories_path):
    """
    Given the filepath to a txt file of the directories to cover
    Load the directory paths in 

    Params:
        Path to directories text file to load

    Returns:

    """
    p = pathlib.Path(directories_path)

    with p.open() as f:
        for line in f:
            logger.debug(line.strip('\n'))
            directories.add(pathlib.Path(line.strip('\n')))


    return directories


def write_to_json(data_path, data):
    """
    Given a filepath to write final data to JSON file

    Params:
        filepath to store data in

    Returns:
        Nothing
    """
    try:
        json_data = json.dumps(data)
        with open(data_path, 'w') as j:
            j.write(json_data)

    except Exception as e:
        logger.debug(f"WRITING to JSON file failed, EXCEPTION: {e}")

    pass


def read_from_json(data_path):
    """
    Given filepath to JSON load the data
    """
    try:
        with open(data_path) as j:
            data = json.load(j)
    except Exception as e:
        logger.debug(f"Reading from JSON file failed, EXCEPTION: {e}")
        data = None

    return data 


def call_dst():
    global last_sync, increment

    logger.debug(directories)

    # handle args 
    args = handle_argparse()

    # setup logging
    # print(f"if args.l: {args.l}")
    if args.l == 'DEBUG' or args.l == 'debug':
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.debug(F"args.directories: {args.directories}")    

    # load in directories from args 
    dirs = load_directories(args.directories)

    # load in backend data from JSON file
    # first the increment to show differences in re-running the synchronise
    increment_filepath = pathlib.Path(f"increment.json")
    if increment_filepath.is_file():
        old_data = read_from_json(str(increment_filepath))
        increment = old_data['increment']
    
    json_data_filepath = pathlib.Path(f'data_{increment}.json')
    if json_data_filepath.is_file():
        old_data = read_from_json(str(json_data_filepath))
        last_sync = old_data['last_sync']
        # increment = old_data['increment']
    else:
        old_data = {}

    increment += 1

    logger.debug(f"old_data: {old_data}")
    # logger.debug(f"old_data['last_sync']: {old_data['last_sync']}")

    logger.debug(f"dirs: {dirs}")
    
    prepped_files = run_sync(dirs)

    print(f"prepped_files: {prepped_files}")

    data = {'last_sync': last_sync, 'increment': increment, 'prepped_files': prepped_files}

    # write prepped files and last_sync timestamp to a file.
    write_to_json(f"data_{increment}.json", data)
    # write increment to file 
    write_to_json(f"{str(increment_filepath)}", {"increment": increment})


def main():
    call_dst()


if __name__=="__main__":
    main()