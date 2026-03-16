from streamlit import session_state, write, container, subheader, multiselect, subheader, column_config, button
from streamlit import dataframe, plotly_chart
from Backend.load_excel import create_excel
from streamlit import set_page_config
from plotly.express import bar
from pandas import merge
from pathlib import Path

set_page_config(page_title="Gráficos", page_icon="📦", layout="wide")

try:
    df = session_state["data"]
    carriers = list(df["CARRIER"].unique())

    columns_to_eliminate = [
        "ALMACEN",
        "N° DOCUMENTO",
        "UNIDADES",
        "TIENDA",
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
        "ESTADO"
    ]

    # datos de pedidos entregados
    df_delivered = df[(df["ESTADO"] == "ENTREGADO")]
    df_not_delivered = df[(df["ESTADO"] == "NO ENTREGADO")]

    # # Se borran las columnas que no son necesarias.
    df_delivered.drop(columns = columns_to_eliminate, axis = 1)
    df_not_delivered.drop(columns = columns_to_eliminate, axis = 1)
    
    # Se juntan los datos por carrier y SLA, esto entrega el total por carrier y SLA.
    df_delivered = df_delivered.groupby("CARRIER")["SLA STATUS"].value_counts().reset_index()
    df_not_delivered = df_not_delivered.groupby("CARRIER")["SLA STATUS"].value_counts().reset_index()

    # Se cuenta el total por carrier tanto para los pedidos no entregados como entregados.
    carrier_load_delivered = df_delivered.groupby("CARRIER")["count"].sum().reset_index()
    carrier_load_not_delivered = df_not_delivered.groupby("CARRIER")["count"].sum().reset_index()

    # Se hace un merge de ambas tablas para saber la participación de los carrier considerando el total de pedidos.
    carrier_load = merge(left = carrier_load_delivered, right = carrier_load_not_delivered, on = "CARRIER")
    carrier_load["TOTAL"] = carrier_load["count_x"] + carrier_load["count_y"]
    total_deliveries = carrier_load["TOTAL"].sum()
    carrier_load["PORCENTAJE"] = round(carrier_load["TOTAL"]/total_deliveries, 2) * 100
    
    # Gráfico de la participación en el total de pedidos por carrier.
    graph_load = bar(
        carrier_load,
        x = "TOTAL",
        y = [""] * len(carrier_load),
        color = "CARRIER",
        orientation = "h",
        barmode = "stack",
        custom_data = "PORCENTAJE",
        width = 1000,
        height = 200
        )
    graph_load.update_layout(
        title = dict(
            text = f"Total de pedidos registrados: {total_deliveries}",
            x = 0,
            y = 0.95,
            font = dict(size = 24)
            ),
        yaxis_visible = False,
        xaxis_visible = False,
        width = 1000,
        height = 200,
        legend = dict(orientation = "h", yanchor = "top")
        )
    graph_load.update_traces(
        hovertemplate = (
            "Total de pedidos asignados: %{x:.}<br>"
            "Porcentaje de participación: %{customdata[0]}%<br><extra></extra>"
            )
    )
    load = plotly_chart(graph_load, width="stretch", on_select = "rerun")

    # En el caso de que se pinche un grafico de la zona izquierda -> seleccion por region
    if load.selection["points"]:
        trigger = False
        trigger_delivered = False
        carry = load.selection["points"][0]["legendgroup"]
        subheader(f"Reporte del carrier {carry}")
        carry_data = df[(df["CARRIER"] == carry)]
        columns_to_eliminate = [
            "ALMACEN",
            "UNIDADES",
            "CARRIER",
            "TRX",
            "FECHA GUIA",
            "FECHA PRERECEPCION",
            "HORA PRE",
            "HORA RECEP",
            "FINES DE SEMANA",
            "DIAS ENTREGA",
            "FIFO DIAS"
        ]
        carry_data.drop(columns = columns_to_eliminate, axis = 1)
        regions = carry_data["REGION"].unique().tolist()
        routes = carry_data["RUTA"].unique().tolist()
        with container(horizontal = True):
            region = multiselect(label="Regiones disponibles", options = regions)
            route = multiselect(label="Rutas disponibles", options = routes)

        if region:
            carry_data = carry_data[(carry_data["REGION"].isin(region))]
            try:
                carry_not_delivered = carry_data[(carry_data["ESTADO"] == "NO ENTREGADO")]
                carry_not_delivered.drop(columns = ["FECHA RECEPCION"], axis = 1)
                carry_delivered = carry_data[(carry_data["ESTADO"] == "ENTREGADO")]
            except:
                carry_not_delivered = []
                carry_delivered = []
        if route:
            carry_data = carry_data[(carry_data["RUTA"].isin(route))]
            try:
                carry_not_delivered = carry_data[(carry_data["ESTADO"] == "NO ENTREGADO")]
                carry_not_delivered.drop(columns = ["FECHA RECEPCION"], axis = 1)
                carry_delivered = carry_data[(carry_data["ESTADO"] == "ENTREGADO")]
            except:
                carry_not_delivered = []
                carry_delivered = []

        else:
            carry_delivered = carry_data[(carry_data["ESTADO"] == "ENTREGADO")]
            carry_not_delivered = carry_data[(carry_data["ESTADO"] == "NO ENTREGADO")]
            carry_not_delivered.drop(columns = ["FECHA RECEPCION"], axis = 1)

        with container(horizontal = True, border = True):
            try:
                with container(horizontal = False):
                    carry_not_delivered = carry_not_delivered.groupby("REGION")["ESTADO"].value_counts().reset_index()
                    total_not_delivered = carry_not_delivered["count"].sum()
                    graph_total_not_delivered = bar(carry_not_delivered, x = "REGION", y = "count", color = "REGION")
                    graph_total_not_delivered.update_layout(
                        title = dict(
                            text = f"Total de pedidos no entregados: {total_not_delivered}",
                            x = 0,
                            y = 0.95,
                            font = dict(size = 24)
                        ),
                        yaxis_title = "total de pedidos",
                        xaxis_title = "",
                        xaxis_visible = False,
                        height = 500,
                        legend = dict(orientation = "h", yanchor = "top")
                        )
                    region_select = plotly_chart(graph_total_not_delivered, width = "stretch", height = "stretch", on_select = "rerun")
                    if region_select.selection["points"]:
                        region_bar_selected = region_select.selection["points"][0]["label"]
                        carry_not_delivered = carry_not_delivered[(carry_not_delivered["REGION"] == region_bar_selected)]
                        total_not_delivered = carry_not_delivered["count"]
                        trigger = True
                    else:
                        trigger = False
                    dataframe(
                        carry_not_delivered,
                        hide_index = True,
                        column_config = {"count": "TOTAL"}
                        )

                with container(horizontal = False):
                    if trigger:
                        carry_delivered = carry_delivered.groupby("REGION")["SLA STATUS"].value_counts().reset_index()
                        carry_delivered = carry_delivered[(carry_delivered["REGION"] == region_bar_selected)]
                        total_delivered = carry_delivered["count"].sum()
                    else:
                        carry_delivered = carry_delivered.groupby("REGION")["SLA STATUS"].value_counts().reset_index()
                        total_delivered = carry_delivered["count"].sum()
                    graph_total_delivered = bar(
                        carry_delivered,
                        x = "REGION",
                        y = "count",
                        color = "SLA STATUS",
                        color_discrete_map={
                            "ADELANTADO": "#00aeef",
                            "ATRASADO": "#FF0000",
                            "A TIEMPO": "#224e9c"
                        },
                        barmode = "stack"
                    )
                    graph_total_delivered.update_layout(
                        title = dict(
                            text = f"Total de pedidos entregados: {total_delivered}",
                            x = 0,
                            y = 0.95,
                            font = dict(size = 24)
                        ),
                        xaxis_title = "",
                        yaxis_title = "total de pedidos",
                        height = 500,
                        )
                    delivery_time = plotly_chart(graph_total_delivered, width="stretch", height="stretch", on_select="rerun")

                    if delivery_time.selection["points"]:
                        sla_status = delivery_time.selection["points"][0]["legendgroup"]
                        region_label = delivery_time.selection["points"][0]["label"]
                        trigger_delivered = True
                    else:
                        trigger_delivered = False

                    dataframe(
                        carry_delivered,
                        hide_index = True,
                        column_config = {
                            "count": "TOTAL"
                            })
            except:
                write("Seleccione una opcion")

        if trigger:
            data_not_delivered = df[((df["REGION"] == region_bar_selected) & (df["ESTADO"] == "NO ENTREGADO"))]
            session_state["download_excel"] = create_excel(data_not_delivered)
            with container(horizontal = True, horizontal_alignment = "distribute", vertical_alignment = "bottom"):
                subheader(f"Reporte de los pedidos NO ENTREGADOS")
                
                if button("Descarga Excel", key = "download_home_page_not_delivered"):
                    download_path = Path.home() / "Downloads" / "Reporte_home_page_no_entregados.xlsx"
                    counter = 1
                    stem, suffix = download_path.stem, download_path.suffix
                    while download_path.exists():
                        download_path = Path.home() / "Downloads" / f"{stem}({counter}){suffix}"
                        counter += 1
                    data_not_delivered.to_excel(download_path, index=False, engine="xlsxwriter")

            dataframe(
                data_not_delivered,
                hide_index = True,
                column_config = {
                    "FECHA GUIA": column_config.DateColumn("FECHA GUIA", format="DD-MM-YYYY"),
                    "FECHA DESPACHO": column_config.DateColumn("FECHA DESPACHO", format="DD-MM-YYYY"),
                    }
                )

        if trigger_delivered:
            data_delivered_sla = df[(df["ESTADO"] == "ENTREGADO")]
            data_delivered_sla = data_delivered_sla[
                ((data_delivered_sla["REGION"] == region_label) & (data_delivered_sla["SLA STATUS"] == sla_status))]
            

            with container(horizontal = True, horizontal_alignment = "distribute", vertical_alignment = "bottom"):
                subheader(f"Reporte de los pedidos ENTREGADOS con estado {sla_status}")
                if button("Descarga Excel", key = "download_home_page_delivered"):
                    download_path = Path.home() / "Downloads" / f"Reporte_home_page_entregados_{sla_status}.xlsx"
                    counter = 1
                    stem, suffix = download_path.stem, download_path.suffix
                    while download_path.exists():
                        download_path = Path.home() / "Downloads" / f"{stem}({counter}){suffix}"
                        counter += 1
                    data_delivered_sla.to_excel(download_path, index=False, engine="xlsxwriter")
                    print("hola")

            dataframe(
                data_delivered_sla,
                hide_index = True,
                column_config = {
                    "FECHA GUIA": column_config.DateColumn("FECHA GUIA", format="DD-MM-YYYY"),
                    "FECHA DESPACHO": column_config.DateColumn("FECHA DESPACHO", format="DD-MM-YYYY"),
                    "FECHA PRERECEPCION": column_config.DateColumn("FECHA PRERECEPCION", format="DD-MM-YYYY"),
                    "FECHA RECEPCION": column_config.DateColumn("FECHA RECEPCION", format="DD-MM-YYYY")
                    }
                )

except Exception as e:
    print(e)
    write("Todavia no se ha cargado un excel en la pagina de inicio")