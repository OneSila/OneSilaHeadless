import os
import subprocess

async def restart_huey():
    # return os.system('sudo superuserctl restart huey')
    return subprocess.run(
        ["sudo", 'superuserctl', 'restart', 'huey'],  # Command as a list
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True  # Ensures output is returned as a string
    )
