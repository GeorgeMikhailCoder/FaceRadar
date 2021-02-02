import subprocess
import sys

packages = ["face_recognition",
            "opencv-python",
            "requests"
]
for package in packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])