from streamlit import session_state, write, container, subheader, dataframe, multiselect, plotly_chart, column_config
from streamlit import set_page_config
from pandas import to_datetime
from plotly.express import bar

set_page_config(page_title = "Gráficos", page_icon = "📦", layout = "wide")
subheader("Reporte general recepcion tiendas", divider = "blue")

try:
    df = session_state["data"]
    df = df[(df["ESTADO"] == "ENTREGADO")]
    df = df[(df["TRX"] == "R")]

    df["FECHA PRERECEPCION"] = to_datetime(df["FECHA PRERECEPCION"].dt.date.astype(str) + " " + df["HORA PRE"])
    df["FECHA RECEPCION"] = to_datetime(df["FECHA RECEPCION"].dt.date.astype(str) + " " + df["HORA RECEP"])
    columns_to_eliminate = [
        "ALMACEN",
        "CARRIER",
        "TRX",
        "FECHA GUIA",
        "FECHA DESPACHO",
        "COMPROMISO ENTREGA",
        "FINES DE SEMANA",
        "DIAS ENTREGA",
        "FIFO ENTREGA",
        "FIFO DIAS",
        "HORA PRE",
        "HORA RECEP",
        "RUTA"
        ]
    df.drop(columns = columns_to_eliminate, axis = 1, inplace = True)
    df["FECHA PRERECEPCION"] = to_datetime(df["FECHA PRERECEPCION"])
    df["FECHA RECEPCION"] = to_datetime(df["FECHA RECEPCION"])
    df["HORAS"] = round((df["FECHA RECEPCION"] - df["FECHA PRERECEPCION"]).dt.total_seconds()/3600, 2)

    regions = list(df["REGION"].unique())
    stores = list(df["TIENDA"].unique())

    with container(horizontal = True, horizontal_alignment = "distribute"):
        region = multiselect(label = "Regiones", options = regions)

    if region:
        df = df[(df["REGION"].isin(region))]

    df["MINUTOS"] = round(df["HORAS"] * 60, 2)
    df["UNIDADESxMINUTOS"] = df["UNIDADES"]/df["MINUTOS"]

    df_outliers = df[((df["UNIDADESxMINUTOS"] <= 0) | (df["MINUTOS"] == 0))]
    df_outliers.drop(columns = ["SLA STATUS", "HORAS", "UNIDADESxMINUTOS"], axis = 1)
    df = df[(df["MINUTOS"] > 0)]

    df.drop(columns = ["SLA STATUS", "HORAS"], axis = 1, inplace = True)

    df = df.groupby("TIENDA").agg(
        UNIDADESxMINUTOS = ("UNIDADESxMINUTOS", "mean"),
        DOCUMENTOS = ("N° DOCUMENTO", "count")
        ).reset_index()

    df = df.sort_values(by = "UNIDADESxMINUTOS", ascending = False)
    best_ten = df.iloc[0:9]
    worst_ten = df.iloc[-10:-1]

    with container(horizontal = True):

        with container(horizontal = False, border = True):
            graph_best_ten = bar(
                best_ten,
                x = "UNIDADESxMINUTOS",
                y = "TIENDA",
                orientation = "h",
                color = "TIENDA"
                )
            graph_best_ten.update_layout(
                title = dict(
                    text = "Tiendas con mejor ratio",
                    x = 0,
                    y = 0.95,
                    font = dict(size = 24)
                    ),
                height = 500,
                showlegend = False,
                xaxis_title = "Unidades por minuto",
                yaxis_title = "Tiendas",
                )
            graph_best_ten.update_traces(
                hovertemplate = (
                    "Tienda: %{y}<br>"
                    "Unidades por minuto: %{x:.2f}<br><extra></extra>"
                    )
                )
            plotly_chart(graph_best_ten, width = "stretch", height = "stretch")

            dataframe(
                data = best_ten,
                hide_index = True,
                column_config = {
                    "UNIDADES": column_config.Column("UNIDADES", width = "small")
                }
            )

        with container(horizontal = False, border = True):
            graph_worst_ten = bar(worst_ten, x = "UNIDADESxMINUTOS", y = "TIENDA", orientation = "h", color = "TIENDA")
            graph_worst_ten.update_layout(
                title = dict(
                    text = "Tiendas con peor ratio",
                    x = 0,
                    y = 0.95,
                    font = dict(size = 24)
                    ),
                height = 500,
                xaxis_title = "Unidades por minuto",
                yaxis_title = "Tiendas",
                showlegend = False
                )
            graph_worst_ten.update_traces(
                hovertemplate = (
                    "Tienda: %{y}<br>"
                    "Unidades por minuto: %{x:.2f}<br><extra></extra>"
                    )
                )
            plotly_chart(graph_worst_ten, width = "stretch", height = "stretch")

            dataframe(
                data = worst_ten,
                hide_index = True,
                column_config = {
                    "UNIDADES": column_config.Column(width = "small")
                }
            )

    write(f":blue-badge[Casos no considerados en el promedio]")
    dataframe(
        df_outliers,
        hide_index = True,
        column_config = {
            "FECHA PRERECEPCION": column_config.DatetimeColumn(format="DD-MM-YYYY"),
            "FECHA RECEPCION": column_config.DateColumn(format="DD-MM-YYYY")
            }
        )

except Exception as e:
    print(e)
    write("Todavia no se ha cargado un excel en la pagina de inicio")