import os
import paramiko
from paramiko.sftp_attr import SFTPAttributes
from csp import call_dst


# Implement the custom transport and ssh to ensure that the custom 
# SFTP client is instantiated from the SSH class
class CustomTransport(paramiko.Transport):
    def open_sftp_client(self):
        return CustomSFTPClient.from_transport(self)

class CustomSSHClient(paramiko.SSHClient):
    def open_sftp(self):
        return self._transport.open_sftp_client()

class CustomSFTPClient(paramiko.SFTPClient):
    """
    Custom SFTP Client class, which adds chunk_size parameter to 
    the put function to specify how many bytes are transferred at a 
    time. 

    https://github.com/paramiko/paramiko/blob/main/paramiko/sftp_client.py
    """

    def _transfer_with_callback(self, reader, writer, file_size, callback, chunk_size):
        """
        https://github.com/paramiko/paramiko/blob/main/paramiko/sftp_client.py#L675

        Override the custom transfer function for SFTP to enable custom sizing 
        of the chunks to write over
        """
        size = 0
        while True:
            # add in chunk_size to read, to enable smaller chunks
            data = reader.read(chunk_size)

            writer.write(data)
            size += len(data)
            if len(data) == 0:
                break
            if callback is not None:
                callback(size, file_size)
        return size    

    def putfo(self, fl, remotepath, file_size=0, callback=None, confirm=True, chunk_size=32768):
        """
        https://github.com/paramiko/paramiko/blob/main/paramiko/sftp_client.py#L687
        .. versionadded:: 1.10


        """
        with self.file(remotepath, "wb") as fr:
            # set pipelined to false, while it may decrease the speed it ensures all chunks are received. 
            fr.set_pipelined(False)
            size = self._transfer_with_callback(
                reader=fl, writer=fr, file_size=file_size, callback=callback, chunk_size=chunk_size
            )
        if confirm:
            s = self.stat(remotepath)
            if s.st_size != size:
                raise IOError(
                    "size mismatch in put!  {} != {}".format(s.st_size, size)
                )
        else:
            s = SFTPAttributes()
        return s

    def put(self, localpath, remotepath, callback=None, confirm=True, chunk_size=32768):
        """
        https://github.com/paramiko/paramiko/blob/main/paramiko/sftp_client.py#L729
        .. versionadded:: 1.4
        .. versionchanged:: 1.7.4
            ``callback`` and rich attribute return value added.
        .. versionchanged:: 1.7.7
            ``confirm`` param added.

        """
        file_size = os.stat(localpath).st_size
        with open(localpath, "rb") as fl:
            return self.putfo(fl, remotepath, file_size, callback, confirm, chunk_size)


def progress_callback(x, y):
    """
    https://github.com/paramiko/paramiko/blob/main/tests/test_sftp.py#L547
    """
    return (x, y)


def initialise_sftp_connection(hostname, username, password, port=22):
    """
    Initialises a connection to a SFTP server with given hostname,
    username and password

    https://sftpcloud.io/learn/python/paramiko-sftp-examples
    """

    try:

        # create an ssh client
        ssh = CustomSSHClient()

        # used for servers without known host key
        ssh.set_missing_host_key_policy()

        # initialise a conncetion with compression, 
        ssh.connect(
            hostname= hostname,
            port=port,
            username=username,
            password=password,
            compress=True
        )

        # initialise sftp client
        sftp = ssh.open_sftp()        

        return ssh, sftp

    
    except Exception as e:
        print(f"EXCEPTION: {e} - CONNECTION FAILED")


def close_sftp_connection(sftp, ssh):
    """
    Closes the sftp and ssh connections
    """
    sftp.close()
    print("SFTP CONNECTION CLOSED")
    ssh.close()
    print("SSH CONNECTIONM CLOSED")


def transfer_files(sftp, files_and_hashes):
    """
    Given an sftp connection, and a list of files and their hashes

    Transfers the files to the remote server over SFTP connection. 

    Params:
        sftp connection, 
        

    Returns:
        o

    """
    for directory in files_and_hashes:
        print(f"directory: {directory}")

    # for hash, filepath in files_and_hashes:
    #     print(f"hash {hash}")
    #     print(f"filepath {filepath}")

    pass


def run_transfer(files, hostname, username, password):

    hostname, username, password = '', '', ''

    # initialise the ssh and sftp connections
    ssh, sftp = sftp.initialise_sftp_connection(hostname, username, password)

    # start transfer of files 
    transfer_files(sftp, files)

    # Check for files and directories on sftp server 
    stdin, stdout, stderr = ssh.exec_command('ls -l')
    print(f"stdin: {stdin}")
    print(f"stdout: {stdout}")
    print(f"stderr: {stderr}")
    print()

    # close the ssh and sftp connections 
    close_sftp_connection(ssh, sftp)


def main():

    print("in main")
    files, hostname, username, password = '', '', '', ''


    run_transfer(files, hostname, username, password)


if __name__=="__main__":
    main()