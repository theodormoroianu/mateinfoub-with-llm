"""
This module is useful for running containerized python scripts, and capture stdout.
"""

import os
import subprocess
import tempfile


def run_script(
        script: str,
        timeout: int = 10,
) -> str:
    """
    Runs the python script in a container, and captures the stdout. If the script takes more than `timeout` seconds to
    run, it is killed and "Timeout" is returned.

    :param script: The python script to run.
    :param timeout: The maximum time in seconds to run the script.
    :return: The stdout of the script, or "Timeout" if the script ran for more than timeout seconds.
    """
    # Create a temporary directory.
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write the script to a file.
        script_file = os.path.join(temp_dir, "script.py")
        with open(script_file, "w") as f:
            f.write(script)

        # Run the script in a container.
        command = ["docker", "run", "--rm", "-v", f"{temp_dir}:/app", "python", "python", "/app/script.py"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return "Timeout"

        return stdout.decode("utf-8")