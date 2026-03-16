from transformers import AutoTokenizer
from optimum.intel.openvino import OVModelForCausalLM
from streamlit import cache_resource
import threading

lock_model_1 = threading.Lock()
lock_model_2 = threading.Lock()

@cache_resource
def load_model():
    model_path = "OpenVino-Qwen2.5-coder"
    model = OVModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    dummy_messages = [{"role": "user", "content": "test"}]
    dummy_text = tokenizer.apply_chat_template(dummy_messages, tokenize=False, add_generation_prompt=True)
    dummy_inputs = tokenizer([dummy_text], return_tensors="pt")
    _ = model.generate(**dummy_inputs, max_new_tokens=10, do_sample=False)

    return model, tokenizer

def prompt_1(prompt):
    messages = [
        {
            "role": "system",
            "content": (""" 
                Trabajas con Python y pandas y existe un DataFrame llamado df ya cargado en memoria con las siguientes columnas
                Las columnas del dataframe son las siguientes:
                ALMACEN: nombre de la bodega de origen, estos pueden ser CD FORUSBEE, CD MAIPU, CD LO ESPEJO, CD LOP7, CD UND MAIPU, CD UND LO ESPEJO.
                N° DOCUMENTO: número de la guía de despacho del pedido.
                UNIDADES: total de unidades declaradas en la guia de despacho.                        
                TIENDA: nombre de la TIENDA destino, lo ideal es filtrar tipo excel es decir, si esta contenido lo solicitado en mayusculas en el nombre de la TIENDA.
                CARRIER: nombre del transportista que lleva el respectivo pedido, estos pueden ser BLUEXPRESS, TNT, TSI, CONOSUR, CORREOS, NEW TRANS, OTL, ROCK TRUCK.
                RUTA: ruta de transporte que sigue el carrier.
                REGION: nombre de la región de Chile de destino del pedido, estas son Tarapaca, Antofagasta, Atacama, Coquimbo, Valparaíso, Libertador Bernardo Ohhigins, Maule, Bio Bio, La Araucania, Los Lagos, Aysén, Magallanes y antártica chilena, Metropolitana.
                TRX: estado de la guia de despacho, I para guias en transito y R para guias recepcionadas.
                FECHA GUIA: fecha de creacion de la guía de despacho en formato año-mes-día datetime64[ns].
                FECHA DESPACHO: fecha de despacho desde la bodega en formato año-mes-día datetime64[ns].
                FECHA PRERECEPCION: fecha de prerecepcion del pedido en la TIENDA en formato año-mes-día datetime64[ns].
                FECHA RECEPCION: fecha de recepcion del pedido en la TIENDA en formato año-mes-día datetime64[ns].
                COMPROMISO ENTREGA: compromiso en cantidad de dias para entregar un pedido.
                FINES DE SEMANA: cantidad de dias de fin de semana entre la fecha de despacho y la fecha actual o de recepcion en la TIENDA.
                DIAS ENTREGA: cantidad de días entre FECHA_DESPACHO y F_RECEPCION_TDA si el pedido es R, o cantidad de dias entre FECHA_DESPACHO y la fecha actual si es I.
                FIFO ENTREGA: cantidad de dias de atraso en la entrega del pedido.
                FIFO DIAS: diferencia de dias entre FECHA_ENTREGA y FECHA_DESPACHO.
                ESTADO: ENTREGADO si la guia de despacho fue entregada en la TIENDA, o NO ENTREGADO si la guia de despacho no ha sido entregada en la TIENDA.
                SLA STATUS: si el pedido se recibio ATRASADO, ADELANTADO o A TIEMPO.    
                Debes responder SOLO con una expresión válida de Python en UNA SOLA LINEA que pueda ejecutarse con eval() y que retorne un DataFrame o valor válido.
                REGLAS ESTRICTAS:
                La respuesta debe comenzar obligatoriamente con df y deben ser de una linea.
                No usar asignaciones sobre df
                solo devolver la expresion
                No usar markdown
                No usar ```
                No explicar nada
                No texto adicional
                No saltos de línea
                Solo una expresión Python válida
                Usar únicamente pandas y Python estándar
                Para múltiples condiciones usar & o | con paréntesis
                Si no entiendes la consulta responder exactamente: no puedo procesar la consulta 
                        
                EJEMPLOS DE SINTAXIS CORRECTA:
                - Una condición: df[df['REGION'] == 'Metropolitana']
                - Dos condiciones: df[(df['REGION'] == 'Metropolitana') & (df['SLA STATUS'] == 'ATRASADO')]
                - Tres condiciones: df[(df['REGION'] == 'Metropolitana') & (df['ALMACEN'] == 'CD MAIPU') & (df['SLA STATUS'] == 'ATRASADO')]
                - Con selección de columna: df[(df['REGION'] == 'Aysén') & (df['SLA STATUS'] == 'ADELANTADO')]['TIENDA']
                - Con contencion de str df[(df["ALMACEN"].str.contains("FORUSBEE"))]
                - Con agrupación: df.groupby('CARRIER')['UNIDADES'].sum().reset_index()
                - Con ordenamiento: df.groupby('TIENDA')['N° DOCUMENTO'].count().sort_values(ascending=False)
                - Con promedio: df.groupby('REGION')['DIAS ENTREGA'].mean().reset_index()

                SINTAXIS INCORRECTA (NUNCA HACER):
                - df[df['REGION'] == 'Aysén' & df['SLA_STATUS'] == 'ADELANTADO']; (faltan paréntesis en este caso)
                - df[df['REGION'] == 'Metropolitana' | df['REGION'] == 'Aysén']
                """
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    return messages

def generate_answer(prompt: str, max_tokens: int, tipo: int) -> str:

    model, tokenizer = load_model()
    if tipo == 1:
        messages = prompt_1(prompt)
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt")

        with lock_model_1:
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                use_cache=False
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )
        return response.strip()