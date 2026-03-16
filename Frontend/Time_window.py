from streamlit import session_state, write, dataframe, container, subheader, column_config, toggle
from streamlit import set_page_config
from pathlib import Path

set_page_config(page_title = "Reporte de pedidos", page_icon = "📦", layout = "wide")
subheader("Reporte ventana de tiempo Pedidos", divider = "gray")
    
try:
    df = session_state["data"]
    data = df.copy()
    CD_names = list(data["ALMACEN"].unique())
    carriers = list(data["CARRIER"].unique())
    
    columns_to_eliminate = [
        "ALMACEN",
        "REGION",
        "FECHA GUIA",
        "FINES DE SEMANA",
        "DIAS ENTREGA",
        "FIFO DIAS",
        "FECHA PRERECEPCION",
        "HORA PRE",
        "HORA RECEP",
        "SLA STATUS",
        "TRX"
    ]
    
    data.drop(columns = columns_to_eliminate, index = 1, inplace = True)

    filter_container = container(
        horizontal = True,
        horizontal_alignment = "left",
        vertical_alignment = "top",
        width = "stretch"
    )

    years = list(data["FECHA DESPACHO"].dt.year.unique())
    years_selection = filter_container.pills(label = "Años disponibles", options = years)

    if years_selection:
        months_data = data[data["FECHA DESPACHO"].dt.year == years_selection]
        months = list(data[data["FECHA DESPACHO"].dt.year == years_selection]["FECHA DESPACHO"].dt.month.unique())
        months = [int(month) for month in months]
        months_selection = filter_container.pills(label = "Meses disponibles", options = months)

        if months_selection:
            month_data = months_data[months_data["FECHA DESPACHO"].dt.month == months_selection]
            days = list(month_data[month_data["FECHA DESPACHO"].dt.month == months_selection]["FECHA DESPACHO"].dt.day.unique())
            days = sorted([int(day) for day in days])
            day = filter_container.select_slider("Seleccione rango de dias", options=days, value = (days[0], days[-1]))

            data_filtered = month_data[
                (month_data["FECHA DESPACHO"].dt.day >= day[0]) & (month_data["FECHA DESPACHO"].dt.day <= day[1])
                ]
            
            trigger_select_container = container(
                horizontal = True,
                horizontal_alignment = "distribute",
                vertical_alignment = "bottom"
            )
            stores = list(data_filtered["TIENDA"].unique())
            with trigger_select_container:
                select_store = trigger_select_container.multiselect("Tiendas", options = stores)
                document = trigger_select_container.number_input(label = "Numero documento", value = None, width = "stretch", step = 1)
                download_button = trigger_select_container.button("Descarga Excel", key = "download_time_window_delivered")
            
            trigger = toggle(label = "PEDIDOS NO ENTREGADOS")
            if trigger:
                data_filtered = data_filtered[(data_filtered["ESTADO"] == "NO ENTREGADO")]
            else:
                data_filtered = data_filtered[(data_filtered["ESTADO"] == "ENTREGADO")]

            if select_store:
                data_filtered = data_filtered[(data_filtered["TIENDA"].isin(select_store))]

            if document:
                data_filtered = data_filtered[(data_filtered["N° DOCUMENTO"] == document)]

            dataframe(
                data_filtered,
                hide_index = True,
                column_config = {
                    "FECHA DESPACHO": column_config.DateColumn(format="DD-MM-YYYY"),
                    "FECHA RECEPCION": column_config.DateColumn(format="DD-MM-YYYY"),
                    "UNIDADES": column_config.Column(width="small"),
                    "TIENDA": column_config.Column(width="medium"),
                    "RUTA": column_config.Column(width=125)
                }
            )
        if download_button:
            if trigger:
                status = "NO ENTREGADO"
            else:
                status = "ENTREGADO"
            download_path = Path.home() / "Downloads" / f"Reporte_temporal_{status}.xlsx"
            counter = 1
            stem, suffix = download_path.stem, download_path.suffix
            while download_path.exists():
                download_path = Path.home() / "Downloads" / f"{stem}({counter}){suffix}"
                counter += 1
            data.to_excel(download_path, index = False, engine = "xlsxwriter")

except KeyError:
    write("Todavia no se ha cargado un excel en la pagina de inicio")