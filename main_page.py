from streamlit import session_state, html
from Backend.load_excel import load_dataframe
from streamlit import Page, navigation
from pandas import read_excel

html("""<style>.stAppHeader {background-color: #00aeef;}</style>""")
html("""<style>.appview-container .main .block-container{{padding-top: {padding_top}rem;}}</style>""")

excel_path = "FENTREGA_HORA.xlsx"
try:
    if session_state["excel_load"]:
        pass
except:
    excel_data = read_excel(excel_path)
    df = load_dataframe(excel_data)
    session_state["data"] = df
    session_state["size"] = f"El archivo tiene un tamaño de {df.shape[0]} filas y {df.shape[1]} columnas"
    session_state["excel_load"] = True

pages = {
    "Home Page": [Page("Frontend/Carrier_load.py", title = "Participación Carriers")],
    "Dashboard": [Page("Frontend/Dashboard.py", title = "Dashboard")],
    "Reporte Carriers": [
        Page("Frontend/Graphs_page/Bar_not_delivered.py", title = "Reporte pedidos no entregados"),
        Page("Frontend/Graphs_page/Bar_delivered.py", title = "Reporte pedidos entregados")
        ],
    "Reporte Tiendas": [
        Page("Frontend/Graphs_page/Store_general.py", title = "General recepcion tiendas"),
        Page("Frontend/Graphs_page/Store_performance.py", title = "Detalle recepcion tiendas")
    ],
    "Reporte temporal": [Page("Frontend/Time_window.py", title = "Reporte Temporal")],
    "Agente IA": [Page("Frontend/IA_page/IA_agent.py", title = "Consultas personalizadas")]
}

app = navigation(pages = pages, position = "top")
app.run()