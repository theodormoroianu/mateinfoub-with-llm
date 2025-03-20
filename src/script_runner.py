"""
This module is useful for running containerized python scripts, and capture stdout.
"""

import os
import subprocess
import logging
import tempfile


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def run_script(
    script: str,
    timeout: int = 30,
) -> str:
    """
    Runs the python script in a container, and captures the stdout. If the script takes more than `timeout` seconds to
    run, it is killed and "Timeout" is returned.

    :param script: The python script to run.
    :param timeout: The maximum time in seconds to run the script.
    :return: The stdout of the script, or "Timeout" if the script ran for more than timeout seconds.
    """

    script = script.strip()
    if script.startswith("```python"):
        script = script[len("```python") :]
    if script.startswith("```"):
        script = script[len("```") :]
    if script.endswith("```"):
        script = script[: -len("```")]

    logger.info("Running script...")
    logger.debug(f"Script: {script}")

    # Create a temporary directory.
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write the script to a file.
        script_file = os.path.join(temp_dir, "script.py")
        with open(script_file, "w") as f:
            f.write(script)

        # Run the script in a container.
        command = [
            "docker",
            "run",
            "--rm",
            "--cpus=1",  # Limit to 1 CPU
            "--memory=8g",  # Limit to 8GB of RAM
            "--name",
            "script_runner",
            "-v",
            f"{temp_dir}:/app",
            "python",
            "python",
            "/app/script.py",
        ]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", "script_runner"])
            process.kill()
            stdout, stderr = process.communicate()
            logger.warning(
                f"Timeout expired for script. Make sure that the python image is downloaded."
            )
            return "Timeout"

        if b"database static dir" in stderr:
            logger.error(
                "Unable to run the script. This is probably because you are "
                "trying to run the script from a snap container (VSCode) or "
                "something similar. Please run the script from a normal terminal."
            )
            raise Exception("Unable to run the script.")

    logger.info("Script ran successfully.")
    return stdout.decode("utf-8").strip()
