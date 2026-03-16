from streamlit import session_state, write, container, subheader, column_config
from Backend.load_excel import create_excel
from streamlit import set_page_config
from plotly.express import box
from pathlib import Path

set_page_config(page_title = "Gráficos", page_icon = "📦", layout = "wide")
subheader("COMPROMISO ENTREGA y FECHA ACTUAL pedidos NO ENTREGADOS", divider = "blue")

try:
    df = session_state["data"]
    data = df.copy()
    data = data[(data["ESTADO"] == "NO ENTREGADO")] 
    columns_to_eliminate = [
        "ALMACEN",
        "TRX",
        "FECHA PRERECEPCION",
        "FECHA RECEPCION",
        "HORA PRE",
        "HORA RECEP",
        "FIFO DIAS"
    ]
    data.drop(columns = columns_to_eliminate, axis = 1, inplace = True)
    
    # Selección de region y carrier.
    regions = list(df["REGION"].unique())
    carriers = list(df["CARRIER"].unique())
    stores = list(df["TIENDA"].unique())
    routes = list(df["RUTA"].unique())

    # Contenedor de los filtros de pedidos no entregados.
    select_container_not_delivered = container(
        horizontal = True,
        horizontal_alignment = "distribute",
        vertical_alignment = "bottom",
        width = "stretch",
        gap = "xsmall"
    )

    # Contenedor de desglose texto a tiempo y atrasados
    messages_container = container(
        horizontal = False,
        horizontal_alignment = "distribute",
        vertical_alignment = "center"
    )

    # Contenedor de los datos no tabulados.
    dataframes_container_not_delivered = container(
        horizontal = False,
        horizontal_alignment = "distribute",
        vertical_alignment = "top",
        width = "stretch",
        gap = "xsmall"
    )

    region_selected = select_container_not_delivered.multiselect("Region", options = regions)
    carrier_selected = select_container_not_delivered.multiselect("Carrier", options = carriers)
    store_selected = select_container_not_delivered.multiselect("Tiendas", options = stores)
    route_selected = select_container_not_delivered.multiselect("Rutas", options = routes)
    download_button = select_container_not_delivered.button("Descarga Excel", key = "download_bar_not_delivered")

    if region_selected:
        data = data[(data["REGION"].isin(region_selected))]

    if carrier_selected:
        data = data[(data["CARRIER"].isin(carrier_selected))]

    if store_selected:
        data = data[(data["TIENDA"].isin(store_selected))]
    
    if route_selected:
        data = data[(data["RUTA"].isin(route_selected))]

    total_past_time = data[(data["SLA STATUS"] == "ATRASADO")].shape[0]
    total_on_time = data[(data["SLA STATUS"] == "A TIEMPO")].shape[0]

    if total_past_time > 0:
        messages_container.write(f"Total de pedidos que se entregaran tarde {total_past_time}")
    if total_on_time > 0:
        messages_container.write(f"Total de pedidos que se podrian entregar a tiempo {total_on_time}")

    columns_to_eliminate = ["TIENDA", "SLA STATUS", "ESTADO", "DIAS ENTREGA"]
    data.drop(columns = columns_to_eliminate, axis = 1, inplace = True)
    with dataframes_container_not_delivered:
        with container(horizontal = True, horizontal_alignment = "distribute", vertical_alignment = "center"):
            dataframe_box = container()
            box_container = container()

        fig = box(
            data_frame = data[["FIFO ENTREGA", "COMPROMISO ENTREGA"]],
            y = "FIFO ENTREGA",
            x = "COMPROMISO ENTREGA"
            )
        
        data_chart = box_container.plotly_chart(fig, width = "stretch", on_select = "rerun")
        
        if data_chart.selection["points"]:
            compromiso_entrega = data_chart.selection["points"][0]["x"]
            fifo_entrega = data_chart.selection["points"][0]["y"]
            data = data[((data["COMPROMISO ENTREGA"] == compromiso_entrega) & (data["FIFO ENTREGA"] == fifo_entrega))]

        dataframe_box.dataframe(
            data,
            hide_index = True,
            column_config = {
                "FECHA GUIA": column_config.DateColumn(format = "DD-MM-YYYY"),
                "FECHA DESPACHO": column_config.DateColumn(format = "DD-MM-YYYY"),
                "RUTA": column_config.Column(width = "medium"),
                "REGION": column_config.Column(width = "medium")
                })

    if download_button:
        download_path = Path.home() / "Downloads" / "Reporte_pedidos_no_entregados.xlsx"
        counter = 1
        stem, suffix = download_path.stem, download_path.suffix
        while download_path.exists():
            download_path = Path.home() / "Downloads" / f"{stem}({counter}){suffix}"
            counter += 1
        data.to_excel(download_path, index = False, engine = "xlsxwriter")

except Exception as e:
    print(e)
    write("Todavia no se ha cargado un excel en la pagina de inicio")