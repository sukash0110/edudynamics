import os
import subprocess
import time

import uvicorn

from study_env.api import app


def _start_streamlit():
    return subprocess.Popen(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port=8502",
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.baseUrlPath=ui",
        ]
    )


def main():
    streamlit_process = _start_streamlit()
    time.sleep(2)
    port = int(os.getenv("PORT", "8501"))
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    finally:
        streamlit_process.terminate()


if __name__ == "__main__":
    main()
