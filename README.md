# Data Synchronisation Tool
The `csp.py` Python script takes a set of directories as line seperated entries in a text file, will iterate through them and create a list of all filepaths for files that have been edited / created since the last successful run, the hashes of those files and a timestamp for successful synchronisation.

The `sftp_client.py` script starts the implementation of a custom SFTP client class using the Python Paramiko library as the base. This is incomplete, but has the base classing as a start for the implementation.

## Commands to run client-side application
Commands to run the client side application.
```bash
git clone <repo_link> 

uv venv

uv sync

uv run csp.py directories.txt # to run basic with no logging output. 

uv run csp.py directories.txt -l INFO 
# OR uv run csp.py directories.txt -l info 
# OR uv run csp.py directories.txt -logging INFO 
# OR uv run csp.py directories.txt -logging info
```

## Notes on current `csp.py` file
The current setup enables testing by loading in an increment and previous sync data to show how it changes per run. This is implemented by storing the data in json files. A first run will do an initial sync and create json files. Subsequent runs will load in the old files and generate a new file. 

In a further implementation, this data would not write artefacts to the client and it would be read from the server. The current setup allows local testing to run multiple scans and see that files are correctly picked up. The first run locally will catch all relevant files in the specified directories, with subsequent runs only picking up those that have been edited. 

The `example_output` folder shows an initial 3 runs of the tool using `uv run csp.py directories.txt`. The file `data_1.json` corresponding to an initial run, `data_2.json` where an additional file has been added and run `csp.py` again, `data_3.json` where no changes were made.

# References 
- Logging was implemented using Python logging docs - https://docs.python.org/3/library/logging.html
- JSON code adapted from - https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python/ 
- Hashing implemented with hashlib docs - https://docs.python.org/3/library/hashlib.html#file-hashing
- File loading and manipulation drawn from - https://docs.python.org/3/library/pathlib.html
- SFTP client class implementation adapted and changed from paramiko source code - https://github.com/paramiko/paramiko/blob/main/paramiko/sftp_client.py
    - Using the library we get a base implementation that we can use, and then add the custom functionality needed so that it better suits our needs. 