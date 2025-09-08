import logging
import os
import stat
from pathlib import Path

import paramiko

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, hostname, username, password, port=22, timeout=10):
        """Initialize SSH and SFTP clients for the given host."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        self.sftp = self.client.open_sftp()

    def close(self):
        """Close the underlying SSH and SFTP connections."""
        self.sftp.close()
        self.client.close()

    def send_command(self, command: str) -> str:
        """Execute a command on the remote host and return stdout/stderr."""
        try:
            logger.info("connecting to host to run command")
            stdin, stdout, stderr = self.client.exec_command(command)

            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")

            return f"stdout: {out}\nstderr: {err}"
        except Exception as e:
            raise e

    # ----------------- File Operations ----------------- #

    def upload_file(self, local_path: str, remote_path: str):
        self.sftp.put(local_path, remote_path)

    def download_file(self, remote_path, local_path):
        self.sftp.get(remote_path, local_path)

    # ----------------- Directory Operations ----------------- #

    def upload_dir(self, remote_dir, local_dir):
        """Recursively upload a directory."""
        try:
            self.sftp.chdir(remote_dir)
        except IOError:
            self.sftp.mkdir(remote_dir)
            self.sftp.chdir(remote_dir)

        for item in os.listdir(local_dir):
            local_path = os.path.join(local_dir, item)
            remote_path = remote_dir + "/" + item
            if os.path.isfile(local_path):
                self.sftp.put(local_path, remote_path)
            else:
                self.upload_dir(remote_path, local_path)

    def download_dir(self, remote_dir, local_dir):
        """Recursively download a directory."""
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        for item in self.sftp.listdir_attr(remote_dir):
            remote_path = remote_dir + "/" + item.filename
            local_path = os.path.join(local_dir, item.filename)
            if stat.S_ISDIR(item.st_mode):
                self.download_dir(remote_path, local_path)
            else:
                self.sftp.get(remote_path, local_path)


if __name__ == "__main__":
    host = "10.196.24.84"
    username = "root"
    password = "Password1"
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Adjust .parent calls as needed to reach your desired root
    data_dir = project_root / "utils" / "local_utils"
    remote_dir = "/home/local_utils/"
    manager = ConnectionManager(host, username, password)
    manager.upload_dir(remote_dir, data_dir)
    command = "python3 /home/local_utils/traps_installer.py -ver 9.0.0.138540"
    manager.send_command(command)
    manager.close()
