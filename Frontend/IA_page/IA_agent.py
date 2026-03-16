from streamlit import session_state, container, subheader, column_config, empty, progress, columns, chat_input, button, write
from Frontend.IA_page.IA_model import generate_answer, load_model
from streamlit import set_page_config
from time import monotonic, sleep

# callbacks
def stream_response(message: str):
    for letter in message:
        yield letter
        sleep(0.005)

def restore_dataframe():
    session_state["dataframe"] = session_state["data"]

# configuracion de la página
set_page_config(page_title="Agente IA", page_icon="📦", layout="wide")
subheader("Consultas personalizadas", divider = "gray")

ia_response = ""
status_ia_text = empty()
progress_ia_bar = progress(0).empty()
detail_ia_text = empty()

if "model_loaded" not in session_state:
    status_ia_text.markdown("### Inicializando modelos IA")
        
    # Cargar modelo con callback de progreso
    progress_ia_bar.progress(40)
    detail_ia_text.text("📦 Preparando carga de los modelxos...")

    load_model()

    progress_ia_bar.progress(100)
    detail_ia_text.text("✅ Modelos IA cargado en el sistema")
    session_state["model_loaded"] = True
    sleep(0.5)

    sleep(0.5)
    progress_ia_bar.empty()
    status_ia_text.empty()
    detail_ia_text.empty()

try:
    if session_state["ia_trigger"]: pass
except:
    session_state["ia_trigger"] = False

try:
    size = session_state["size"]

    with container(
        horizontal = True,
        horizontal_alignment = "distribute",
        vertical_alignment = "center"):
        
        chat = chat_input(
            placeholder = "Escribe tu consulta aquí",
            key = "chatbox"
        )
        button(
            "Carga datos",
            type = "primary",
            on_click = restore_dataframe
        )

    col1, col2 = columns([2, 1.20])
    with col1:
        df_container = container(
            horizontal_alignment = "distribute",
        )
    with col2:
        doc_search_input = container(horizontal=True)
        ia_response_container = container(
            border = True,
            vertical_alignment = "distribute",
            gap = "xxsmall"
        )

    if chat:
        start = monotonic()
        response = generate_answer(prompt = chat, max_tokens = 256, tipo = 1)
        print(response)

        if response == "no puedo procesar la consulta":
            ia_response_container.write_stream(
                stream_response("No pude procesar o entender la consulta")
                )
            end = monotonic()
            write(f"Tiempo total de inferencia: {end - start:.2f} segundos")

        elif "df" in response:
            try:
                if not session_state["ia_trigger"]:
                    df = session_state["data"]
                    df = eval(response)
                    if len(df) == 0:
                        ia_response_container.write_stream(
                            stream_response("No se encontraron resultados para esta busqueda")
                            )
                    else:
                        session_state["dataframe"] = df
                        texto = f"""
                                Total de pedidos: {len(df)}\n
                                Total de unidades: {df["UNIDADES"].sum()}\n
                                Total de pedidos no entregados: {len(df[(df['ESTADO'] == 'NO ENTREGADO')])}\n
                                Total de pedidos entregados: {len(df[(df['ESTADO'] == 'ENTREGADO')])}\n
                                Regiones abarcadas: {str(df['REGION'].unique().tolist())}\n
                                Carriers usados: {str(df['CARRIER'].unique().tolist())[1:-1].replace("'","")}\n
                                """
                        ia_response_container.write_stream(
                            stream_response(texto)
                            )
                    session_state["ia_trigger"] = True

                elif session_state["ia_trigger"]:
                    df = session_state["dataframe"]
                    df = eval(response)
                    if len(df) == 0:
                        ia_response_container.write_stream(
                           stream_response("No se encontraron resultados para esta busqueda")
                           )
                    else:
                        session_state["dataframe"] = df
                        texto = f"""
                                Total de pedidos: {len(df)}\n
                                Total de unidades: {df["UNIDADES"].sum()}\n
                                Total de pedidos no entregados: {len(df[(df['ESTADO'] == 'NO ENTREGADO')])}\n
                                Total de pedidos entregados: {len(df[(df['ESTADO'] == 'ENTREGADO')])}\n
                                Regiones abarcadas: {str(df['REGION'].unique().tolist())[1:-1].replace("'","")}\n
                                Carriers usados: {str(df['CARRIER'].unique().tolist())[1:-1].replace("'","")}\n
                                """
                        ia_response_container.write_stream(
                            stream_response(texto)
                            )
            except Exception as e:
                print(e)
            end = monotonic()
            write(f"Tiempo total de respuesta: {end - start:.2f} segundos")

    df_container.dataframe(
        session_state["dataframe"],
        width = "content",
        hide_index = True,
        column_config = {
            "FECHA GUIA": column_config.DateColumn(format = "DD-MM-YYYY"),
            "FECHA DESPACHO": column_config.DateColumn(format = "DD-MM-YYYY"),
            "FECHA PRERECEPCION": column_config.DateColumn(format = "DD-MM-YYYY"),
            "FECHA RECEPCION": column_config.DateColumn(format = "DD-MM-YYYY")
        }
    )

except Exception as e:
    print(e)