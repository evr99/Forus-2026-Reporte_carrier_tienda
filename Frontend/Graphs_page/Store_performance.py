from streamlit import session_state, write, container, subheader, dataframe, column_config
from streamlit import set_page_config
from pandas import to_datetime, Timedelta
from plotly.express import bar

set_page_config(page_title = "Gráficos", page_icon = "📦", layout = "wide")
subheader("Reporte recepcion tiendas", divider = "blue")

try:
    df = session_state["data"]
    df = df[(df["ESTADO"] == "ENTREGADO")]
    df = df[(df["TRX"] == "R")]
    columns_to_eliminate = [
        "ALMACEN",
        "CARRIER",
        "REGION",
        "TRX",
        "FECHA GUIA",
        "COMPROMISO ENTREGA",
        "FINES DE SEMANA",
        "DIAS ENTREGA",
        "FIFO ENTREGA",
        "FIFO DIAS",
        "ESTADO"
        ]
    df.drop(columns = columns_to_eliminate, axis = 1, inplace = True)
    df["N° DOCUMENTO"] = df["N° DOCUMENTO"].astype(str)
    selection_container = container(
        horizontal = True,
        horizontal_alignment = "distribute",
        vertical_alignment = "center"
    )
    bar_chart_container = container(border = True)

    store_names = df["TIENDA"].unique()
    store = selection_container.selectbox("Selección de tienda", (store_names))
    
    if store:
        df = df[(df["TIENDA"] == store)]
        df.drop(columns = ["TIENDA"], axis = 1, inplace = True)
        sla_status = df["SLA STATUS"].unique().tolist()

        sla = selection_container.multiselect("Tiempo de entrega pedido", sla_status)

        if sla:
            df = df[(df["SLA STATUS"].isin(sla))]

        df.drop(columns = ["SLA STATUS"], axis = 1, inplace = True)
        df["FECHA PRERECEPCION"] = to_datetime(df["FECHA PRERECEPCION"].dt.date.astype(str) + " " + df["HORA PRE"])
        df["FECHA RECEPCION"] = to_datetime(df["FECHA RECEPCION"].dt.date.astype(str) + " " + df["HORA RECEP"])
        df.drop(columns = ["HORA PRE", "HORA RECEP"], axis = 1, inplace = True)
        fechas = df["FECHA RECEPCION"].dt.date.unique().tolist()

        start, end = bar_chart_container.slider(
            label = "Rango de fechas",
            min_value = min(fechas),
            max_value = max(fechas),
            value = (min(fechas), max(fechas))
            )

        start = to_datetime(start)
        end = to_datetime(end) + Timedelta(days=1)
        df["FECHA PRERECEPCION"] = to_datetime(df["FECHA PRERECEPCION"])
        df["FECHA RECEPCION"] = to_datetime(df["FECHA RECEPCION"])
        df = df[(df["FECHA RECEPCION"] >= start) & (df["FECHA RECEPCION"] < end)]
        df["HORAS"] = round((df["FECHA RECEPCION"] - df["FECHA PRERECEPCION"]).dt.total_seconds()/3600, 2)

        df = df.groupby("FECHA PRERECEPCION").agg(
            UNIDADES = ("UNIDADES", "sum"),
            HORAS = ("HORAS", "mean"),
            DOCUMENTOS = ("N° DOCUMENTO", "count")
            ).reset_index()
        
        df = df.sort_values(by = "FECHA PRERECEPCION") #, ascending = True
        df["ORDEN"] = [i for i in range(len(df["FECHA PRERECEPCION"]))]
        df["HORAS"] = df["HORAS"]*60
        df.rename(columns = {"HORAS": "MINUTOS"}, inplace =True)
        dataframe(
            df,
            hide_index = True,
            column_config = {
                "ORDEN": None,
                "FECHA PRERECEPCION": column_config.DateColumn(format = "DD-MM-YYYY HH:mm")
                }
            )
        fig = bar(
            df,
            x = "ORDEN",
            y = "MINUTOS",
            text = "DOCUMENTOS",
            barmode = "group",
            color = "DOCUMENTOS",
            custom_data = ["DOCUMENTOS", "FECHA PRERECEPCION"]
            )
        fig.update_layout(
            title = dict(
                text = "",
                x = 0,
                y = 0.95,
                font = dict(size = 24)
                ),
            xaxis = dict(visible = False),
            )
        fig.update_traces(
            hovertemplate = (
                "Total de documentos: %{customdata[0]}<br>"
                "Promedio minutos usados: %{y:.2f}<br>"
                "Fecha Prerecepcion: %{customdata[1]}<br><extra></extra>"
                )
            )
        bar_chart_container.plotly_chart(fig)

except KeyError:
    write("Todavia no se ha cargado un excel en la pagina de inicio")