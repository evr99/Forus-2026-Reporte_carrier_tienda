from time import sleep, ctime, strptime, strftime
from webview import create_window, start
from threading import Thread, Event
from datetime import datetime
from os.path import getmtime
from subprocess import Popen
from win32com import client
from pathlib import Path
import subprocess
import sys
import os

streamlit_process = None

# Carpeta raiz del proyecto (donde esta este main.py)
BASE_DIR = Path(__file__).resolve().parent

def get_python() -> str:
    """Retorna python embebido si existe, sino el python actual."""
    embedded = BASE_DIR / "python" / "python.exe"
    if embedded.exists():
        return str(embedded)
    return sys.executable

def run_streamlit():
    global streamlit_process
    python    = get_python()
    main_page = BASE_DIR / "main_page.py"

    print(f"Usando Python: {python}")
    print(f"Lanzando:      {main_page}")

    streamlit_process = Popen(
        [
            python,
            "-m", "streamlit", "run", str(main_page),
            "--server.headless", "true",
            "--server.port",     "8501",
            "--server.address",  "localhost",
            "--browser.gatherUsageStats", "false"
        ],
        cwd=str(BASE_DIR)
    )

def run_update_excel():
    excel_path = str(BASE_DIR / "FENTREGA_HORA.xlsx")

    actual_time     = datetime.now().strftime(format="%Y-%m-%d %H:%M")
    excel_file_time = getmtime(excel_path)
    excel_file_time = strftime("%Y-%m-%d %H:%M", strptime(ctime(excel_file_time)))

    actual_time     = datetime.strptime(actual_time,     "%Y-%m-%d %H:%M")
    excel_file_time = datetime.strptime(excel_file_time, "%Y-%m-%d %H:%M")

    delta = (actual_time - excel_file_time).total_seconds() / 3600

    if delta > 1:
        print("Actualizando Excel...")
        try:
            excel = client.Dispatch("Excel.Application")
            excel.Visible       = False
            excel.DisplayAlerts = False
            wb = excel.Workbooks.Open(excel_path)
            wb.RefreshAll()
            excel.CalculateUntilAsyncQueriesDone()
            wb.Save()
            wb.Close()
            excel.Quit()
        except:
            pass

def closed_window():
    """Mata Streamlit y sus procesos hijo al cerrar la ventana."""
    global streamlit_process
    print("Ventana cerrada, terminando Streamlit...")
    if streamlit_process is not None:
        try:
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(streamlit_process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            streamlit_process.wait(timeout=5)
            print("Streamlit terminado.")
        except Exception as e:
            print(f"Error al terminar Streamlit: {e}")
            try:
                streamlit_process.kill()
            except:
                pass

if __name__ == "__main__":
    run_update_excel()
    sleep(3)
    t = Thread(target=run_streamlit, daemon=True)
    t.start()
    sleep(3)

    app = create_window(
        title     = "Reporte pedidos",
        url       = "http://localhost:8501",
        width     = 1000,
        height    = 550,
        resizable = True
    )
    app.events.closed += closed_window
    start()