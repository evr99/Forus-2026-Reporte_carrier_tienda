from streamlit import cache_data, session_state, progress, empty
from pandas import DataFrame, to_datetime, ExcelWriter
from numpy import where
from time import sleep
from io import BytesIO

def load_dataframe(df) -> DataFrame:
    
    progress_bar = progress(0)
    status_text = empty()
    detail_text = empty()

    status_text.markdown("### 📊 Procesando archivo Excel")
    detail_text.text("Leyendo archivo...")
    progress_bar.progress(5)
    
    # Formatear nombre columnas
    df.columns = (df.columns.str.strip().str.upper().str.replace(" ", "_"))

    # Eliminar columnas redundantes -> revisar ruta transporte
    cols_to_eliminate = ["BODEGA", "NRO_LOCAL"]
    df.drop(columns = cols_to_eliminate, axis = 1, inplace = True)

    # Cambio de nombre de alguna columnas
    columns_name_change = {
        "LOCAL": "TIENDA",
        "NUMERO_DOCUMENTO": "N° DOCUMENTO",
        "CANT_DOCUMENTO": "UNIDADES",
        "RUTA_TRANSPORTE": "RUTA",
        "FINES_DE_SEMANA": "FINES DE SEMANA",
        "TRUNC(FECHA_GUIA)": "FECHA GUIA",
        "F_RECEPCION_TDA": "FECHA ENTREGA",
        "FECHA_PRERECEPCION_TDA": "FECHA PRERECEPCION",
        "FECHA_DESPACHO": "FECHA DESPACHO",
        "TRUNC(F_RECEPCION_TDA)": "FECHA RECEPCION",
        "HORA_PREC_TDA": "HORA PRE",
        "HORA_RECEP_TDA": "HORA RECEP",
        "ESTADO_ENTREGA": "ESTADO",
        "FIFO_EENTREGA": "FIFO ENTREGA",
        "COMPROMISO_ENTREGA": "COMPROMISO ENTREGA",
        "ESTADO_TRX": "TRX",
        "DIAS_ENTREGA": "DIAS ENTREGA"
    }
    df.rename(columns = columns_name_change, inplace=True)

    progress_bar.progress(20)
    detail_text.text("Ajustando columnas...")
    sleep(0.2)

    # Formatear las columnas con fechas
    cols_datetime = ["FECHA GUIA", "FECHA DESPACHO", "FECHA PRERECEPCION", "FECHA RECEPCION"]
    for col in cols_datetime:
        if col in df.columns:
            df[col] = to_datetime(df[col], errors="coerce")

    # Mapear valores de región.
    df["REGION"] = df["REGION"].map({
        "1": "Tarapaca",
        "2": "Antofagasta",
        "3": "Atacama",
        "4": "Coquimbo",
        "5": "Valparaíso",
        "6": "Libertador Bernardo Ohhigins",
        "7": "Maule",
        "8": "Bio Bio",
        "9": "La Araucania",
        "10": "Los Lagos",
        "11": "Aysén",
        "12": "Magallanes",
        "13A": "Metropolitana"
    })

    # FIFO
    df["FIFO DIAS"] = (df["FECHA RECEPCION"] - df["FECHA DESPACHO"]).dt.days

    # SLA
    df["SLA STATUS"] = where(
        df["FIFO ENTREGA"] < 0, "ADELANTADO",
        where(df["FIFO ENTREGA"] == 0, "A TIEMPO", "ATRASADO")
    )
    df["RUTA"] = df["RUTA"].replace("SR", "SIN RUTA")
    df = df[[
        "ALMACEN",
        "N° DOCUMENTO",
        "UNIDADES",
        "TIENDA",
        "CARRIER",
        "RUTA",
        "REGION",
        "TRX",
        "FECHA GUIA",
        "FECHA DESPACHO",
        "FECHA PRERECEPCION",
        "FECHA RECEPCION",
        "HORA PRE",
        "HORA RECEP",
        "COMPROMISO ENTREGA",
        "FINES DE SEMANA",
        "DIAS ENTREGA",
        "FIFO ENTREGA",
        "FIFO DIAS",
        "ESTADO",
        "SLA STATUS"
    ]]
    
    progress_bar.progress(30)
    detail_text.text("✅ Excel procesado correctamente")
    sleep(0.3)
    session_state["trigger"] = True

    sleep(0.5)
    progress_bar.empty()
    status_text.empty()
    detail_text.empty()
    return df

@cache_data
def create_excel(dataframe: DataFrame):
    dataframe["FECHA DESPACHO"] = to_datetime(dataframe["FECHA DESPACHO"], errors="coerce")
    dataframe["FECHA GUIA"] = to_datetime(dataframe["FECHA GUIA"], errors="coerce", dayfirst = True)
    buffer = BytesIO()
    with ExcelWriter(buffer, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Reporte No entregado")
    excel_data = buffer.getvalue()
    buffer.close()
    return excel_data