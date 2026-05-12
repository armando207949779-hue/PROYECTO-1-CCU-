# App Streamlit Formulario Válvulas Línea 11 - MATRIZ POR FORMATO
# Versión homologada con Tulipas Línea 2, con logo CCU y formato actualizado

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Formulario Mantenimiento Válvulas Línea 11",
    page_icon="🏢",
    layout="centered"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1PmDo4EjBxXZx0fPMGPMJKzBztyAq8AipxqCsJTFI0e0/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

# =====================================================
# RUTAS DEL PROYECTO / LOGO
# =====================================================
BASE_DIR = Path(__file__).resolve().parent

LOGO_CANDIDATES = [
    BASE_DIR / "assets" / "CCU_logo_(2018).svg.png",
    BASE_DIR.parent / "assets" / "CCU_logo_(2018).svg.png",
]

LOGO_PATH = next(
    (path for path in LOGO_CANDIDATES if path.exists()),
    LOGO_CANDIDATES[0]
)

# =====================================================
# LISTAS FORMULARIO
# =====================================================
TURNOS = ["", "A", "B", "C"]

OPERADORES = [
    "",
    "JORGE MUÑOZ",
    "LUIS SOTO",
    "ISMAEL BRIONES",
    "OTRO"
]

EQUIPOS = ["", "Encajonadora", "Desencajonadora"]

FORMATOS = ["", "237 CC", "350 CC", "1000 CC", "1250 CC"]

CABEZALES_POR_FORMATO = {
    "237 CC": list(range(1, 7)),      # C1 a C6
    "350 CC": list(range(1, 8)),      # C1 a C7
    "1000 CC": list(range(1, 10)),    # C1 a C9
    "1250 CC": list(range(1, 10))     # C1 a C9
}

VALVULAS = list(range(1, 155))        # V1 a V154

MANTENCIONES = [
    "",
    "CAMBIO DE GOMA VÁLVULA",
    "CAMBIO CUERPO VÁLVULA PLÁSTICA",
    "CAMBIO DE RESORTE",
    "CAMBIO DE VÁSTAGO",
    "CAMBIO DE SEGURO DE VÁSTAGO",
    "CAMBIO DE CONECTOR NEUMÁTICO",
    "OTRO"
]


# =====================================================
# GOOGLE SHEETS
# =====================================================
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
        "Válvula",
        "Mantención",
        "Comentarios",
        "Alerta insumos críticos",
        "Fecha registro"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:K1", [headers])
    except Exception:
        ws.update("A1:K1", [headers])


def guardar_registros(filas):
    ws = conectar()
    init_sheet(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


# =====================================================
# ESTILO GENERAL
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 1.2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 900px;
        margin: 0 auto;
    }

    h1 {
        text-align: center;
        margin-bottom: 0.2rem;
        color: #0E4C92;
        line-height: 1.15;
    }

    h2 {
        color: #2E86C1;
    }

    h3 {
        color: #0E4C92;
    }

    div[data-testid="stCheckbox"] {
        margin-bottom: -10px;
    }

    div[data-testid="stCheckbox"] label {
        font-size: 0.76rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    .logo-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 1.2rem;
        padding-bottom: 2.8rem;
        margin-bottom: 0.4rem;
    }

    .logo-wrapper img {
        width: 190px;
        max-width: 70%;
        display: block;
    }

    .header-wrapper {
        text-align: center;
        padding: 0px 10px 8px 10px;
        max-width: 850px;
        margin: 0 auto 1.2rem auto;
    }

    .header-wrapper h1 {
        color: #0E4C92;
        margin-top: 0px;
        margin-bottom: 18px;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    .header-wrapper h2 {
        color: #2E86C1;
        margin-top: 0px;
        margin-bottom: 18px;
        font-size: 1.25rem;
        font-weight: 600;
    }

    .header-wrapper p {
        color: #5D6D7E;
        font-size: 1rem;
        margin-top: 0px;
        margin-bottom: 18px;
    }

    .header-wrapper hr {
        border: 1px solid #D6EAF8;
        width: 75%;
        margin-top: 10px;
        margin-bottom: 0px;
    }

    .matriz-valvulas {
        padding-left: 10px;
        padding-right: 10px;
        margin-top: 6px;
    }

    .valvulas-resumen {
        background-color: rgba(30, 144, 255, 0.14);
        color: #1E90FF;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 10px 4px 10px;
        font-size: 0.95rem;
    }

    .alerta-insumos {
        background-color: rgba(255, 193, 7, 0.16);
        color: #8A6D00;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 12px;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# FUNCIÓN LOGO
# =====================================================
def mostrar_logo():
    if LOGO_PATH.exists():
        logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")

        st.markdown(
            f"""
            <div class="logo-wrapper">
                <img
                    src="data:image/png;base64,{logo_base64}"
                    alt="Logo CCU"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =====================================================
# ENCABEZADO
# =====================================================
mostrar_logo()

st.markdown(
    """
    <div class='header-wrapper'>
        <h1>
            FORMULARIO DE MANTENIMIENTO
        </h1>
        <h2>
            LÍNEA 11 · VÁLVULAS
        </h2>
        <p>
            Registro de mantenciones por formato, cabezal y válvula
        </p>
        <hr>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("Complete todos los campos requeridos antes de guardar el registro.")


# =====================================================
# DATOS GENERALES
# =====================================================
with st.container(border=True):
    st.subheader("Datos generales")

    fecha = st.date_input("Fecha", value=None)

    turno = st.selectbox("Turno", TURNOS)

    operador_sel = st.selectbox("Operador", OPERADORES)

    operador_manual = ""

    if operador_sel == "OTRO":
        operador_manual = st.text_input(
            "Especificar operador",
            placeholder="Ingrese nombre del operador"
        ).upper().strip()

    operador_final = operador_manual if operador_sel == "OTRO" else operador_sel

    equipo = st.selectbox("Equipo", EQUIPOS)

    formato = st.selectbox("Formato", FORMATOS)


# =====================================================
# SELECCIÓN DE VÁLVULAS
# =====================================================
with st.container(border=True):
    st.subheader("Selección de válvulas")

    seleccion_valvulas = []

    if formato == "":
        st.warning("Seleccione primero el formato para desplegar la matriz.")
    else:
        cabezales = CABEZALES_POR_FORMATO[formato]

        st.caption(
            f"Formato seleccionado: {formato} | "
            f"Cabezales disponibles: C1 a C{max(cabezales)} | "
            f"Válvulas disponibles: V1 a V154"
        )

        st.markdown(
            """
            <div class="matriz-valvulas">
            """,
            unsafe_allow_html=True
        )

        header = st.columns(len(cabezales) + 1, gap="small")

        with header[0]:
            st.markdown("**Válvula**")

        for idx, c in enumerate(cabezales, start=1):
            with header[idx]:
                st.markdown(f"**C{c}**")

        for v in VALVULAS:
            cols = st.columns(len(cabezales) + 1, gap="small")

            with cols[0]:
                st.markdown(f"**V{v}**")

            for idx, c in enumerate(cabezales, start=1):
                with cols[idx]:
                    key = f"formato_{formato}_cabezal_{c}_valvula_{v}"

                    seleccionado = st.checkbox(
                        label="",
                        key=key,
                        label_visibility="collapsed"
                    )

                    if seleccionado:
                        seleccion_valvulas.append({
                            "Cabezal": c,
                            "Válvula": v
                        })

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="valvulas-resumen">
                Válvulas seleccionadas: {len(seleccion_valvulas)}
            </div>
            """,
            unsafe_allow_html=True
        )

        if seleccion_valvulas:
            st.write(seleccion_valvulas)


# =====================================================
# MANTENCIÓN
# =====================================================
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

    alerta_insumos_criticos = st.checkbox(
        "Alerta insumos críticos",
        help="Marcar cuando falte algún insumo crítico para realizar o completar la mantención."
    )

    if alerta_insumos_criticos:
        st.markdown(
            """
            <div class="alerta-insumos">
                Se marcará este registro con alerta por falta de insumos críticos.
            </div>
            """,
            unsafe_allow_html=True
        )


# =====================================================
# RESUMEN
# =====================================================
with st.container(border=True):
    st.subheader("Resumen")

    st.write("Fecha:", fecha)
    st.write("Turno:", turno)
    st.write("Operador:", operador_final)
    st.write("Equipo:", equipo)
    st.write("Formato:", formato)
    st.write("Mantención:", mantencion_final)
    st.write("Válvulas seleccionadas:", seleccion_valvulas if seleccion_valvulas else "-")
    st.write(
        "Alerta insumos críticos:",
        "Sí" if alerta_insumos_criticos else "No"
    )

    guardar = st.button("Guardar registro", use_container_width=True)


# =====================================================
# VALIDACIÓN Y GUARDADO
# =====================================================
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

    if not seleccion_valvulas:
        errores.append("Seleccionar al menos una válvula")

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

        for item in seleccion_valvulas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador_final,
                equipo,
                formato,
                item["Cabezal"],
                item["Válvula"],
                mantencion_final,
                comentario,
                "Sí" if alerta_insumos_criticos else "No",
                fecha_registro
            ])

        try:
            guardar_registros(filas)
            st.success(f"{len(filas)} registros guardados correctamente.")

        except Exception as e:
            st.error(f"Error al guardar: {e}")


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; opacity: 0.6; font-size: 0.85rem;'>
        <b>Formulario Mantenimiento Válvulas Línea 11</b> · v4.0<br>
        Streamlit · Google Sheets
    </div>
    """,
    unsafe_allow_html=True
)
