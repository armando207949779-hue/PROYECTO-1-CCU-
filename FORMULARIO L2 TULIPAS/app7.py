# App8 Streamlit Formulario Tulipas Línea 2 - MATRIZ ACTUALIZADA

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Formulario Mantenimiento Tulipas Línea 2",
    layout="centered"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1EjrHHNJXjjBOObeAfIBxQjDfcyCS-o_j4FLaDxOPjRI/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

TURNOS = ["", "A", "B", "C"]

OPERADORES = [
    "",
    "RICHARD RUZ",
    "DIDIMO VALERO",
    "JORGE GONZALES",
    "JUAN RUPERTUS MONDACA",
    "OTRO"
]

EQUIPOS = ["", "Encajonadora", "Desencajonadora"]
FORMATOS = ["", "2000 CC", "2500 CC"]

MANTENCIONES = [
    "",
    "CAMBIO DE GOMA TULIPA",
    "CAMBIO CUERPO TULIPA PLÁSTICA",
    "CAMBIO DE RESORTE",
    "CAMBIO DE VÁSTAGO",
    "CAMBIO DE SEGURO DE VÁSTAGO",
    "CAMBIO DE CONECTOR NEUMÁTICO",
    "OTRO"
]


@st.cache_resource(ttl=60)
def conectar():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL).sheet1


def init_sheet(ws):
    headers = [
        "Fecha",
        "Turno",
        "Operador",
        "Equipo",
        "Formato",
        "Cabezal",
        "Tulipa",
        "Mantención",
        "Comentarios",
        "Fecha registro"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:J1", [headers])
    except Exception:
        ws.update("A1:J1", [headers])


def guardar_registros(filas):
    ws = conectar()
    init_sheet(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


st.markdown(
    """
    <div style='text-align: center; padding: 12px 10px 4px 10px;'>
        <h1 style='color:#0E4C92; margin-bottom:4px; font-size: 2.1rem;'>
            FORMULARIO DE MANTENIMIENTO
        </h1>
        <h2 style='color:#2E86C1; margin-top:0px; font-size: 1.25rem; font-weight: 600;'>
            LÍNEA 2 · TULIPAS
        </h2>
        <p style='color:#5D6D7E; font-size: 1rem; margin-top: 8px;'>
            Registro de mantenciones de tulipas
        </p>
        <hr style='border: 1px solid #D6EAF8; width:75%; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("Complete todos los campos requeridos antes de guardar el registro.")


with st.container(border=True):
    st.subheader("Datos generales")

    fecha = st.date_input("Fecha", value=None)

    turno = st.selectbox("Turno", TURNOS)

    operador_sel = st.selectbox("Operador", OPERADORES)

    operador_manual = ""

    if operador_sel == "OTRO":
        operador_manual = st.text_input("Especificar operador").upper().strip()

    operador_final = operador_manual if operador_sel == "OTRO" else operador_sel

    equipo = st.selectbox("Equipo", EQUIPOS)

    formato = st.selectbox("Formato", FORMATOS)


with st.container(border=True):
    st.subheader("Selección de tulipas")

    seleccion_tulipas = []

    if formato == "":
        st.warning("Seleccione primero el formato.")
    else:
        n_cabezales = 7
        n_tulipas = 9 if formato == "2000 CC" else 6

        header = st.columns(n_cabezales + 1)

        with header[0]:
            st.markdown("**Tulipa**")

        for c in range(1, n_cabezales + 1):
            with header[c]:
                st.markdown(f"**C{c}**")

        for t in range(1, n_tulipas + 1):
            cols = st.columns(n_cabezales + 1)

            with cols[0]:
                st.markdown(f"**T{t}**")

            for c in range(1, n_cabezales + 1):
                with cols[c]:
                    key = f"cabezal_{c}_tulipa_{t}"

                    seleccionado = st.checkbox(
                        label="",
                        key=key,
                        label_visibility="collapsed"
                    )

                    if seleccionado:
                        seleccion_tulipas.append({
                            "Cabezal": c,
                            "Tulipa": t
                        })

        st.info(f"Tulipas seleccionadas: {len(seleccion_tulipas)}")

        if seleccion_tulipas:
            st.write(seleccion_tulipas)


with st.container(border=True):
    st.subheader("Mantención")

    mantencion_sel = st.selectbox("Tipo de mantención", MANTENCIONES)

    mantencion_manual = ""

    if mantencion_sel == "OTRO":
        mantencion_manual = st.text_input(
            "Especificar mantención",
            placeholder="Ingrese tipo de mantención"
        ).upper().strip()

    mantencion_final = mantencion_manual if mantencion_sel == "OTRO" else mantencion_sel

    comentario = st.text_area(
        "Comentarios",
        height=120,
        placeholder="Escriba observaciones adicionales..."
    )


with st.container(border=True):
    st.subheader("Resumen")

    st.write("Fecha:", fecha)
    st.write("Turno:", turno)
    st.write("Operador:", operador_final)
    st.write("Equipo:", equipo)
    st.write("Formato:", formato)
    st.write("Mantención:", mantencion_final)
    st.write("Tulipas seleccionadas:", seleccion_tulipas)

    guardar = st.button("Guardar registro", use_container_width=True)


if guardar:

    errores = []

    if fecha is None:
        errores.append("Seleccionar fecha")

    if not turno:
        errores.append("Seleccionar turno")

    if not operador_final:
        errores.append("Seleccionar operador")

    if not equipo:
        errores.append("Seleccionar equipo")

    if not formato:
        errores.append("Seleccionar formato")

    if not seleccion_tulipas:
        errores.append("Seleccionar al menos una tulipa")

    if not mantencion_sel:
        errores.append("Seleccionar mantención")

    if mantencion_sel == "OTRO" and not mantencion_manual:
        errores.append("Especificar mantención")

    if errores:
        for error in errores:
            st.error(error)

    else:
        filas = []
        fecha_registro = obtener_hora_chile()

        for item in seleccion_tulipas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador_final,
                equipo,
                formato,
                item["Cabezal"],
                item["Tulipa"],
                mantencion_final,
                comentario,
                fecha_registro
            ])

        try:
            guardar_registros(filas)
            st.success(f"{len(filas)} registros guardados correctamente.")

        except Exception as e:
            st.error(f"Error al guardar: {e}")


st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; opacity: 0.6; font-size: 0.85rem;'>
        <b>Formulario Mantenimiento Tulipas Línea 2</b> · v8.2<br>
        Streamlit · Google Sheets
    </div>
    """,
    unsafe_allow_html=True
)
