# App Streamlit: Registro mantenimiento válvulas KRONES Línea 11
# Versión con logo, formato mejorado, margen corregido, operadores actualizados
# resumen homologado a Línea 2 Válvulas y selector "Seleccione"
# Actualización: 154 válvulas + alerta insumos críticos con detalle + SONDA

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Registro Mantenimiento Válvulas L11",
    page_icon="🏢",
    layout="wide"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ompaiCPCIegzgj80wHjPde5GL14660AUBnUTt6iTD_w/edit?usp=sharing"
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
    "GUSTAVO ADOLFO MORÓN AGUILERA",
    "JAVIER FLORES LLANCANAO",
    "MARCO QUILAHUEQUE CONTRERAS",
    "NEFTALI RUBINOT ALARCON",
    "OTRO"
]

REPUESTOS = [
    "BLOQUE",
    "O-RINGS",
    "RESORTE",
    "ON/OFF",
    "SONDA",
    "OTRO"
]

# Línea 11 considera 154 válvulas
NUMEROS_VALVULA = list(range(1, 155))


# =====================================================
# GOOGLE SHEETS
# =====================================================
@st.cache_resource(ttl=60)
def conectar_google_sheet():
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


def inicializar_hoja(ws):
    headers = [
        "Fecha",
        "Turno",
        "Operador",
        "Número Válvula",
        "Repuesto / Mantención",
        "Observaciones",
        "Alerta insumos críticos",
        "Detalle alerta insumo crítico",
        "Fecha Registro",
        "Origen"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:J1", [headers])
    except Exception:
        ws.update("A1:J1", [headers])


def obtener_fecha_registro():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def guardar_registros(filas):
    ws = conectar_google_sheet()
    inicializar_hoja(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


# =====================================================
# ESTILO GENERAL
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 1.2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1180px;
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
        max-width: 900px;
        margin: 0 auto 1.2rem auto;
    }

    .header-wrapper h1 {
        color: #0E4C92;
        margin-top: 0px;
        margin-bottom: 26px;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    .header-wrapper h2 {
        color: #2E86C1;
        margin-top: 0px;
        margin-bottom: 26px;
        font-size: 1.25rem;
        font-weight: 600;
    }

    .header-wrapper p {
        color: #5D6D7E;
        font-size: 1rem;
        margin-top: 0px;
        margin-bottom: 22px;
    }

    .header-wrapper hr {
        border: 1px solid #D6EAF8;
        width: 75%;
        margin-top: 10px;
        margin-bottom: 0px;
    }

    .valvula-resumen {
        background-color: rgba(30, 144, 255, 0.14);
        color: #1E90FF;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 18px 4px 18px;
        font-size: 0.95rem;
    }

    .valvula-lista {
        padding-left: 18px;
        padding-right: 18px;
        margin-top: 6px;
    }

    .alerta-card-title {
        color: #0E4C92;
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .alerta-card-subtitle {
        color: #5D6D7E;
        font-size: 0.95rem;
        margin-bottom: 14px;
    }

    .alerta-box {
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.18), rgba(255, 248, 220, 0.65));
        border-left: 5px solid #F4B400;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    .alerta-box-title {
        color: #8A6D00;
        font-size: 0.98rem;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .alerta-box-text {
        color: #6E5A00;
        font-size: 0.9rem;
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
# FUNCIONES ALERTA INSUMOS CRÍTICOS
# =====================================================
def seleccionar_alerta_si():
    if st.session_state.get("alerta_insumos_si", False):
        st.session_state["alerta_insumos_no"] = False
    elif not st.session_state.get("alerta_insumos_no", False):
        st.session_state["alerta_insumos_no"] = True


def seleccionar_alerta_no():
    if st.session_state.get("alerta_insumos_no", False):
        st.session_state["alerta_insumos_si"] = False
    elif not st.session_state.get("alerta_insumos_si", False):
        st.session_state["alerta_insumos_no"] = True


# =====================================================
# ENCABEZADO
# =====================================================
mostrar_logo()

st.markdown(
    """
    <div class='header-wrapper'>
        <h1>
            REGISTRO DE MANTENIMIENTO
        </h1>
        <h2>
            LÍNEA 11 · VÁLVULAS KRONES
        </h2>
        <p>
            Formulario para registrar mantenciones operacionales de válvulas
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

    col1, col2, col3 = st.columns(3)

    with col1:
        fecha = st.date_input("Fecha", value=date.today())

    with col2:
        turno = st.selectbox("Turno", TURNOS)

    with col3:
        operador_sel = st.selectbox("Operador", OPERADORES)

    operador_manual = ""

    if operador_sel == "OTRO":
        operador_manual = st.text_input("Especificar operador").upper().strip()

    operador_final = operador_manual if operador_sel == "OTRO" else operador_sel


# =====================================================
# REPUESTO / MANTENCIÓN
# =====================================================
with st.container(border=True):
    st.subheader("Repuesto / Mantención")

    col1, col2 = st.columns([1, 2])

    with col1:
        repuesto_sel = st.selectbox("Seleccione", [""] + REPUESTOS)

    with col2:
        otro_repuesto = ""

        if repuesto_sel == "OTRO":
            otro_repuesto = st.text_input("Especificar OTRO").upper().strip()

    repuesto_final = otro_repuesto if repuesto_sel == "OTRO" else repuesto_sel

    observaciones = st.text_area(
        "Observaciones",
        height=100,
        placeholder="Escriba observaciones adicionales..."
    )


# =====================================================
# ALERTA INSUMOS CRÍTICOS
# =====================================================
with st.container(border=True):
    st.markdown(
        """
        <div class="alerta-card-title">
            Alerta insumos críticos
        </div>
        <div class="alerta-card-subtitle">
            Marque si existe algún insumo crítico faltante para completar la mantención.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Valor inicial por defecto: NO
    if "alerta_insumos_si" not in st.session_state:
        st.session_state["alerta_insumos_si"] = False

    if "alerta_insumos_no" not in st.session_state:
        st.session_state["alerta_insumos_no"] = True

    col_si, col_no, col_espacio = st.columns([1, 1, 4])

    with col_si:
        alerta_si = st.checkbox(
            "Sí",
            key="alerta_insumos_si",
            on_change=seleccionar_alerta_si
        )

    with col_no:
        alerta_no = st.checkbox(
            "No",
            key="alerta_insumos_no",
            on_change=seleccionar_alerta_no
        )

    alerta_insumos_criticos = "Sí" if alerta_si else "No"

    detalle_alerta_insumo = ""

    if alerta_si:
        st.markdown(
            """
            <div class="alerta-box">
                <div class="alerta-box-title">
                    Detalle de alerta
                </div>
                <div class="alerta-box-text">
                    Indique cuál es el insumo crítico faltante o la alerta detectada.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        detalle_alerta_insumo = st.text_area(
            "Detalle alerta insumo crítico",
            height=90,
            placeholder="Ejemplo: Falta stock de O-RINGS, resorte específico, bloque, kit de reparación, sonda, etc.",
            label_visibility="collapsed"
        ).upper().strip()


# =====================================================
# SELECCIÓN DE VÁLVULAS
# =====================================================
with st.container(border=True):
    st.subheader("Selección de válvulas")

    st.caption("Seleccione una o más válvulas intervenidas. Línea 11 considera 154 válvulas.")

    st.markdown(
        """
        <div class="valvula-lista">
        """,
        unsafe_allow_html=True
    )

    columnas = 16

    for inicio in range(1, 155, columnas):
        cols = st.columns(columnas, gap="small")

        for i, num in enumerate(range(inicio, min(inicio + columnas, 155))):
            with cols[i]:
                st.checkbox(str(num), key=f"val_{num}")

    st.markdown("</div>", unsafe_allow_html=True)

    valvulas = [
        n for n in NUMEROS_VALVULA
        if st.session_state.get(f"val_{n}", False)
    ]

    st.markdown(
        f"""
        <div class="valvula-resumen">
            Válvulas seleccionadas: {len(valvulas)}
        </div>
        """,
        unsafe_allow_html=True
    )

    if valvulas:
        st.write(valvulas)


# =====================================================
# RESUMEN
# =====================================================
with st.container(border=True):
    st.subheader("Resumen")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Fecha:", fecha)
        st.write("Turno:", turno)
        st.write("Operador:", operador_final)

    with col2:
        st.write("Repuesto / Mantención:", repuesto_final)
        st.write("Válvulas seleccionadas:", valvulas)
        st.write("Alerta insumos críticos:", alerta_insumos_criticos)

    if observaciones:
        st.write("Observaciones:", observaciones)

    if alerta_insumos_criticos == "Sí":
        st.write(
            "Detalle alerta insumo crítico:",
            detalle_alerta_insumo if detalle_alerta_insumo else "-"
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
        errores.append("Ingresar operador")

    if not valvulas:
        errores.append("Seleccionar al menos una válvula")

    if not repuesto_sel:
        errores.append("Seleccionar repuesto / mantención")

    if repuesto_sel == "OTRO" and not otro_repuesto:
        errores.append("Especificar el repuesto / mantención en OTRO")

    if alerta_si and not detalle_alerta_insumo:
        errores.append("Indicar cuál es la alerta de insumo crítico")

    if errores:
        st.warning("Faltan campos obligatorios:")

        for e in errores:
            st.error(e)

    else:
        filas = []
        fecha_reg = obtener_fecha_registro()

        for v in valvulas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador_final,
                v,
                repuesto_final,
                observaciones,
                alerta_insumos_criticos,
                detalle_alerta_insumo,
                fecha_reg,
                "Streamlit - Línea 11"
            ])

        try:
            guardar_registros(filas)
            st.success(f"{len(filas)} registros guardados correctamente en Google Sheets.")

        except Exception as e:
            st.error(f"Error al guardar registros: {e}")


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; opacity: 0.6; font-size: 0.85rem;'>
        <b>Formulario Mantenimiento Válvulas KRONES Línea 11</b> · v1.7<br>
        Streamlit · Google Sheets
    </div>
    """,
    unsafe_allow_html=True
)
