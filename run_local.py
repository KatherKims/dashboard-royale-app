"""Run both local services. Ctrl+C shuts down only the children started here."""
from pathlib import Path
import subprocess
import sys
import threading
from dashboard.floor_server import create_server

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    server=create_server()
    threading.Thread(target=server.serve_forever,daemon=True).start()
    process=subprocess.Popen([sys.executable,'-m','streamlit','run',str(root/'app.py'),
                              '--server.address=127.0.0.1','--server.port=8501',
                              '--server.headless=true','--browser.gatherUsageStats=false'],cwd=root)
    print('Dashboard: http://127.0.0.1:8501/\nFloor lab: http://127.0.0.1:8502/floor-lab',flush=True)
    try:process.wait()
    except KeyboardInterrupt:process.terminate();process.wait(timeout=10)
    finally:server.shutdown();server.server_close()
