from streamlit import session_state, container, write, columns, subheader, dataframe, title, subheader
from streamlit import set_page_config

set_page_config(page_title = "Dashboard", page_icon = "📈", layout = "wide")
subheader("Cuadros resumen", divider = "gray")

def clear_all_multi():
    keys = ["region", "tienda", "carrier"]
    for key in keys:
        session_state[key] = []

try:
    df = session_state["data"]
  
    filter_container = container(
        horizontal = True,
        horizontal_alignment = "distribute",
        vertical_alignment = "bottom",
        width = "stretch"
    )

    region_sel = filter_container.multiselect(
        "Región",
        sorted(df["REGION"].dropna().unique()),
        placeholder = "",
        key = "region"
    )
    
    tienda_sel = filter_container.multiselect(
        "Tienda",
        sorted(df["TIENDA"].dropna().unique()),
        placeholder = "",
        key = "tienda"
    )    
    
    carrier_sel = filter_container.multiselect(
        "Carrier",
        sorted(df["CARRIER"].dropna().unique()),
        placeholder = "",
        key = "carrier"
    )    
    
    filter_container.button("Quitar Filtros", type = "primary", on_click = clear_all_multi)

    if region_sel:
        df = df[df["REGION"].isin(region_sel)]

    if tienda_sel:
        df = df[df["TIENDA"].isin(tienda_sel)]

    if carrier_sel:
        df = df[df["CARRIER"].isin(carrier_sel)]

    # Cuadros de resumen
    col1, col2, col3 = columns(3, width = "stretch")

    with col1:
        subheader("SLA por Región")
        sla_region = (
            df.groupby(["REGION", "SLA STATUS"])
            .size()
            .unstack(fill_value = 0)
            .reset_index()
        )
        dataframe(sla_region, width = "stretch", height = 250, hide_index = True)

    with col2:
        subheader("Ranking FIFO Local")
        ranking_fifo = (
            df.groupby("TIENDA")["FIFO DIAS"]
            .mean()
            .sort_values(ascending = False)
            .reset_index()
        )
        dataframe(ranking_fifo, width = "stretch", height = 250, hide_index = True)

    with col3:
        subheader("Ranking Carriers")
        ranking_carrier = (
            df.groupby("CARRIER")["FIFO DIAS"]
            .mean()
            .sort_values(ascending = False)
            .reset_index()
        )
        dataframe(ranking_carrier, width = "stretch", height = 250, hide_index = True)
    pass

except KeyError:
    write("Todavia no se ha cargado un excel en la pagina de inicio")