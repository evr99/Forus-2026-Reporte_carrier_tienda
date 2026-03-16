# Documentación proyecto Reporte Tiendas-Carrier

Sistema de reportería y análisis logístico con Agente IA, construido sobre Streamlit y empaquetado como aplicación de escritorio con pywebview.

---

## Estructura del Proyecto

```
Proyecto/
├── main.py                         # Punto de entrada, lanza Streamlit + pywebview
├── main_page.py                    # Carga del Excel y definición de navegación
├── FENTREGA_HORA.xlsx              # Archivo fuente de datos
├── Backend/
│   └── load_excel.py               # Procesamiento del DataFrame y utilidades Excel
└── Frontend/
    ├── Carrier_load.py             # Home Page: participación y desglose por carrier
    ├── Dashboard.py                # Dashboard de resumen con filtros globales
    ├── Time_window.py              # Reporte temporal filtrado por año/mes/día
    ├── Graphs_page/
    │   ├── Bar_delivered.py        # Boxplot pedidos entregados
    │   ├── Bar_not_delivered.py    # Boxplot pedidos no entregados
    │   ├── Store_general.py        # Ranking general de rendimiento por tienda
    │   └── Store_performance.py    # Detalle de rendimiento por tienda individual
    └── IA_page/
        ├── IA_agent.py             # Interfaz del agente IA con chat interactivo
        └── IA_model.py             # Carga del modelo OpenVino y generación de respuestas
```

---

## Esquema de Datos

Columnas disponibles en `session_state["data"]` tras el procesamiento de `load_dataframe()`:

| Columna | Descripción |
|---|---|
| `ALMACEN` | Bodega de origen: CD FORUSBEE, CD MAIPU, CD LO ESPEJO, CD LOP7, CD UND MAIPU, CD UND LO ESPEJO |
| `N° DOCUMENTO` | Número de guía de despacho |
| `UNIDADES` | Total de unidades declaradas en la guía |
| `TIENDA` | Nombre de la tienda destino |
| `CARRIER` | Transportista: BLUEXPRESS, TNT, TSI, CONOSUR, CORREOS, NEW TRANS, OTL, ROCK TRUCK |
| `RUTA` | Ruta de transporte (SR reemplazado por SIN RUTA) |
| `REGION` | Nombre completo de la región de destino en Chile |
| `TRX` | I = en tránsito, R = recepcionado |
| `FECHA GUIA` | Fecha de creación de la guía (`datetime64`) |
| `FECHA DESPACHO` | Fecha de despacho desde bodega (`datetime64`) |
| `FECHA PRERECEPCION` | Fecha de prerecepción en tienda (`datetime64`) |
| `FECHA RECEPCION` | Fecha de recepción final en tienda (`datetime64`) |
| `HORA PRE` | Hora de prerecepción (string HH:MM) |
| `HORA RECEP` | Hora de recepción (string HH:MM) |
| `COMPROMISO ENTREGA` | Días comprometidos para la entrega |
| `FINES DE SEMANA` | Días de fin de semana en el período de entrega |
| `DIAS ENTREGA` | Días reales de entrega (o días desde despacho si TRX=I) |
| `FIFO ENTREGA` | Días de atraso (negativo = adelantado) |
| `FIFO DIAS` | Diferencia en días entre FECHA RECEPCION y FECHA DESPACHO (calculado) |
| `ESTADO` | ENTREGADO o NO ENTREGADO |
| `SLA STATUS` | ADELANTADO, A TIEMPO o ATRASADO (calculado desde FIFO ENTREGA) |

---

## Backend

### `load_excel.py`

Módulo central de procesamiento de datos. Transforma el Excel crudo en un DataFrame limpio y estandarizado listo para ser consumido por todas las páginas del frontend.

#### `load_dataframe(df)`

| | Detalle |
|---|---|
| **Entrada** | DataFrame crudo leído desde el Excel fuente |
| **Retorno** | DataFrame limpio y enriquecido con columnas estándar |
| **session_state** | Escribe `session_state["trigger"] = True` al finalizar |

Pasos que ejecuta internamente:
1. Normaliza nombres de columnas: strip, upper, reemplaza espacios por guión bajo
2. Elimina columnas redundantes: `BODEGA`, `NRO_LOCAL`
3. Renombra columnas al esquema estándar del proyecto (`LOCAL → TIENDA`, `CANT_DOCUMENTO → UNIDADES`, etc.)
4. Convierte columnas de fechas a `datetime64[ns]` con `to_datetime()`
5. Mapea códigos de región numéricos a nombres completos (`1 → Tarapaca`, `13A → Metropolitana`, etc.)
6. Calcula `FIFO DIAS`: diferencia en días entre `FECHA RECEPCION` y `FECHA DESPACHO`
7. Calcula `SLA STATUS`: ADELANTADO si `FIFO ENTREGA < 0`, A TIEMPO si `== 0`, ATRASADO si `> 0`
8. Reemplaza rutas `SR` por `SIN RUTA`
9. Reordena las columnas al esquema definitivo del proyecto
10. Muestra barra de progreso con mensajes de estado en la UI de Streamlit

#### `create_excel(dataframe)`

Decorada con `@cache_data`. Serializa un DataFrame a bytes `.xlsx` en memoria usando `xlsxwriter`.

| | Detalle |
|---|---|
| **Entrada** | DataFrame pandas a exportar |
| **Retorno** | `bytes` del archivo `.xlsx` |
| **Sheet** | `Reporte No entregado` |
| **Cache** | `@cache_data` — mismo DataFrame retorna bytes cacheados |

---

## Punto de Entrada

### `main.py`

Orquestador de la aplicación de escritorio. Envuelve Streamlit en una ventana nativa usando pywebview, gestiona el ciclo de vida del proceso y actualiza el Excel fuente si tiene más de 1 hora de antigüedad.

| Función | Descripción |
|---|---|
| `get_python()` | Detecta si existe un Python embebido en `./python/`; si no, usa el Python del sistema |
| `run_streamlit()` | Lanza `streamlit run main_page.py` como subproceso con `headless=true` en puerto 8501 |
| `run_update_excel()` | Abre `FENTREGA_HORA.xlsx` con Excel COM, ejecuta `RefreshAll()` y guarda si el archivo tiene >1h sin modificarse |
| `closed_window()` | Callback del evento `closed` de pywebview: mata el proceso Streamlit y sus hijos con `taskkill /F /T` |

**Flujo de arranque:**
1. `run_update_excel()` — refresca el Excel si es necesario
2. `sleep(3)` — espera que Excel termine
3. `Thread(run_streamlit)` — lanza Streamlit en hilo daemon
4. `sleep(3)` — espera que Streamlit esté disponible en `:8501`
5. `create_window()` — abre ventana pywebview apuntando a `http://localhost:8501`
6. `start()` — bloquea hasta que el usuario cierra la ventana

### `main_page.py`

Página raíz de Streamlit. Carga el Excel una única vez por sesión, inicializa `session_state` y define la estructura de navegación multi-página.

**Lógica de carga:**
- Verifica `session_state["excel_load"]` para no releer el archivo en cada rerun
- Lee `FENTREGA_HORA.xlsx` con `pandas.read_excel()`
- Procesa el DataFrame con `load_dataframe()` del backend
- Guarda `df` en `session_state["data"]` y metadatos de tamaño en `session_state["size"]`

**Estructura de navegación:**

| Sección | Páginas |
|---|---|
| Home Page | `Carrier_load.py` — Participación Carriers |
| Dashboard | `Dashboard.py` — Cuadros resumen |
| Reporte Carriers | `Bar_not_delivered.py`, `Bar_delivered.py` |
| Reporte Tiendas | `Store_general.py`, `Store_performance.py` |
| Reporte temporal | `Time_window.py` |
| Agente IA | `IA_agent.py` |

---

## Frontend

### `Carrier_load.py` — Home Page: Participación Carriers

Página principal de análisis por carrier. Muestra la distribución de carga de pedidos entre transportistas y permite hacer drill-down interactivo hasta el detalle por región y estado SLA.

**Flujo de visualización:**
1. Calcula el total de pedidos entregados y no entregados por carrier usando `groupby` + `merge`
2. Computa el porcentaje de participación de cada carrier sobre el total
3. Renderiza un gráfico de barras apiladas horizontal (stacked bar) con Plotly Express
4. Al seleccionar un carrier en el gráfico, muestra filtros de Región y Ruta
5. Muestra dos gráficos secundarios: pedidos NO entregados por región y pedidos entregados por región coloreados por SLA STATUS
6. Al seleccionar una barra de región en el gráfico de no entregados, activa `trigger = True`
7. Con `trigger` activo: muestra tabla detallada de pedidos NO entregados con botón de descarga Excel
8. Con `trigger_delivered` activo: muestra tabla de pedidos entregados filtrados por SLA y región con botón de descarga Excel

**Variables de control:**

| Variable | Descripción |
|---|---|
| `trigger` | `True` cuando el usuario selecciona una región en el gráfico de no entregados |
| `trigger_delivered` | `True` cuando el usuario selecciona un SLA en el gráfico de entregados |
| `region_bar_selected` | Nombre de la región seleccionada en el gráfico |
| `carry` | Nombre del carrier seleccionado en el gráfico principal |

---

### `Dashboard.py` — Cuadros Resumen

Dashboard de resumen ejecutivo con tres tablas analíticas filtradas globalmente por región, tienda y carrier.

- Filtros globales: Región, Tienda, Carrier con `multiselect` y botón **Quitar Filtros**
- **Tabla SLA por Región**: pivot de conteo agrupado por `REGION` y `SLA STATUS`
- **Ranking FIFO Local**: promedio de `FIFO DIAS` por tienda, ordenado descendente
- **Ranking Carriers**: promedio de `FIFO DIAS` por carrier, ordenado descendente
- `clear_all_multi()`: callback que vacía los tres filtros del `session_state` simultáneamente

---

### `Time_window.py` — Reporte Temporal

Página de análisis temporal con navegación jerárquica año → mes → rango de días.

- Selección de año con `st.pills` — al seleccionar, carga los meses disponibles de ese año
- Selección de mes con `st.pills` — al seleccionar, carga los días disponibles del mes
- Slider de rango de días para acotar el período exacto de análisis
- Toggle **PEDIDOS NO ENTREGADOS** para alternar entre entregados y no entregados
- Filtros adicionales: Tienda (`multiselect`) y N° Documento (`number_input`)
- Botón **Descarga Excel**: guarda el DataFrame filtrado en `~/Downloads` con manejo de duplicados

> **Nota:** el download actualmente guarda `data` (DataFrame pre-filtro completo). Para exportar solo el rango filtrado, cambiar a `data_filtered.to_excel()`.

---

### `Graphs_page/Bar_delivered.py` — Boxplot Pedidos Entregados

Análisis de dispersión de pedidos entregados usando gráfico boxplot interactivo de `FIFO ENTREGA` vs `COMPROMISO ENTREGA`.

- Filtra el DataFrame por `ESTADO == "ENTREGADO"`
- Filtros: Región, Carrier, Tienda, Ruta (todos `multiselect`)
- Muestra totales de pedidos ATRASADO, A TIEMPO y ADELANTADO como texto informativo
- Gráfico boxplot Plotly: eje X = `COMPROMISO ENTREGA`, eje Y = `FIFO ENTREGA`
- Al seleccionar un punto del boxplot, filtra la tabla por el par `(COMPROMISO ENTREGA, FIFO ENTREGA)` exacto
- Descarga Excel del DataFrame visible en `~/Downloads` con manejo de duplicados

---

### `Graphs_page/Bar_not_delivered.py` — Boxplot Pedidos No Entregados

Misma estructura que `Bar_delivered.py` pero filtra por `ESTADO == "NO ENTREGADO"`. Excluye columnas de fechas de recepción ya que el pedido aún no fue recibido.

- Columnas adicionales eliminadas: `FECHA PRERECEPCION`, `FECHA RECEPCION`, `FIFO DIAS`
- Muestra solo totales de ATRASADO y A TIEMPO
- Descarga Excel en `~/Downloads` como `Reporte_pedidos_no_entregados.xlsx`

---

### `Graphs_page/Store_general.py` — Ranking General Tiendas

Análisis comparativo de rendimiento de recepción entre todas las tiendas usando el ratio de unidades procesadas por minuto.

- Filtra por `ESTADO == "ENTREGADO"` y `TRX == "R"` (guías recepcionadas)
- Combina `FECHA PRERECEPCION + HORA PRE` y `FECHA RECEPCION + HORA RECEP` para obtener timestamps exactos
- Calcula `HORAS` = diferencia en horas entre recepción y prerecepción
- Calcula `UNIDADESxMINUTOS = UNIDADES / MINUTOS` como ratio de productividad
- Excluye outliers: registros con `UNIDADESxMINUTOS <= 0` o `MINUTOS == 0`
- Agrupa por `TIENDA`: promedio de `UNIDADESxMINUTOS` y conteo de `DOCUMENTOS`
- Muestra Top 9 mejores y Top 10 peores tiendas en barras horizontales
- Tabla de outliers excluidos al pie de la página

---

### `Graphs_page/Store_performance.py` — Detalle Recepción Tienda

Vista de serie temporal del rendimiento de recepción para una tienda específica, agrupada por fecha de prerecepción.

- Selector de tienda con `selectbox`
- Selector de `SLA STATUS` con `multiselect` para filtrar por tipo de entrega
- Slider de rango de fechas basado en `FECHA RECEPCION`
- Agrupa por `FECHA PRERECEPCION`: suma de `UNIDADES`, promedio de `HORAS` (convertido a `MINUTOS`), conteo de `DOCUMENTOS`
- Gráfico de barras: eje X = `ORDEN` (índice numérico), eje Y = `MINUTOS`, color = `DOCUMENTOS`
- Hover muestra: total de documentos, promedio de minutos y fecha de prerecepción

---

## Agente IA

### `IA_model.py` — Modelo y Prompts

Módulo de inferencia local usando el modelo **Qwen2.5-Coder-1.5B-Instruct** optimizado con OpenVino en precisión int4.

#### `load_model()`
- Decorada con `@cache_resource` — el modelo se carga una única vez en toda la sesión
- Carga `OVModelForCausalLM` desde la carpeta local `OpenVino-Qwen2.5-coder`
- Ejecuta un warmup dummy con `max_new_tokens=10` para compilar los kernels de OpenVino
- Retorna la tupla `(model, tokenizer)`

#### `prompt_1(prompt)`
Construye el mensaje `system + user`. El system prompt instruye al modelo a:
- Responder **solo** con una expresión Python válida en una línea ejecutable con `eval()`
- La respuesta debe comenzar obligatoriamente con `df`
- No usar markdown, no explicar, no usar saltos de línea
- Ante consulta no entendida, responder exactamente: `no puedo procesar la consulta`

Incluye descripción de las 20 columnas del DataFrame, restricciones de sintaxis y ejemplos de expresiones correctas e incorrectas.

#### `generate_answer(prompt, max_tokens, tipo)`

| Parámetro | Descripción |
|---|---|
| `prompt` | Texto de la consulta del usuario |
| `max_tokens` | Límite de tokens generados (recomendado: 256) |
| `tipo` | Selector de prompt: `1` = `prompt_1` |
| **Retorno** | String con la expresión Python generada, sin tokens especiales |

- Usa `threading.Lock()` para serializar llamadas al modelo y evitar condiciones de carrera
- Decodifica solo los tokens nuevos: `outputs[0][inputs["input_ids"].shape[1]:]`
- `do_sample=False` y `use_cache=False` para inferencia determinista

---

### `IA_agent.py` — Interfaz del Agente

Página de chat interactivo que permite consultar el DataFrame en lenguaje natural. El modelo genera expresiones Python que se evalúan dinámicamente con `eval()`.

**Flujo de ejecución:**
1. Al cargar la página, verifica `session_state["model_loaded"]`
2. Si el modelo no está cargado, muestra barra de progreso y llama a `load_model()`
3. El usuario escribe una consulta en el `chat_input`
4. Se llama a `generate_answer()` — la respuesta raw se imprime en consola para debugging
5. Si la respuesta es `"no puedo procesar la consulta"`, muestra mensaje de error con stream
6. Si la respuesta contiene `"df"`, ejecuta `eval(response)` sobre el DataFrame activo
7. Si el resultado tiene filas, actualiza `session_state["dataframe"]` y muestra estadísticas resumidas
8. Si el resultado está vacío, informa que no hay resultados
9. El botón **Carga datos** ejecuta `restore_dataframe()` para resetear el DataFrame al original

**Variables de `session_state`:**

| Variable | Descripción |
|---|---|
| `session_state["data"]` | DataFrame original completo (solo lectura en esta página) |
| `session_state["dataframe"]` | DataFrame activo filtrado por el agente IA |
| `session_state["ia_trigger"]` | `False` en la primera consulta (usa `data`), `True` en las siguientes (usa `dataframe`) |
| `session_state["model_loaded"]` | Flag para evitar recargar el modelo en cada rerun |
| `session_state["size"]` | String con dimensiones del DataFrame, requerido para que la página renderice |

> `stream_response(message)`: generador que emite la respuesta letra a letra con `sleep(0.005)` para efecto de escritura animada.