# App Streamlit: Panel compacto de registro mantenimiento válvulas KRONES Línea 2

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Panel Mantenimiento Válvulas L2",
    page_icon="🔧",
    layout="wide"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

TURNOS = ["A", "B", "C"]
NUMEROS_VALVULA = list(range(1, 113))
REPUESTOS = ["BLOQUE", "O-RINGS", "RESORTE", "ON/OFF", "OTRO"]

# =====================================================
# CONEXIÓN GOOGLE SHEETS
# =====================================================
@st.cache_resource
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
        "Número Válvula",
        "Repuesto",
        "Observaciones",
        "Fecha registro"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:G1", [headers])
    except Exception:
        ws.update("A1:G1", [headers])


def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def guardar_registros(filas):
    ws = conectar()
    init_sheet(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


# =====================================================
# ESTADO DE CHECKBOXES
# =====================================================
for numero in NUMEROS_VALVULA:
    key = f"chk_valvula_{numero}"
    if key not in st.session_state:
        st.session_state[key] = False


def seleccionar_todas():
    for numero in NUMEROS_VALVULA:
        st.session_state[f"chk_valvula_{numero}"] = True


def limpiar_seleccion():
    for numero in NUMEROS_VALVULA:
        st.session_state[f"chk_valvula_{numero}"] = False


def obtener_valvulas_seleccionadas():
    return [
        numero for numero in NUMEROS_VALVULA
        if st.session_state.get(f"chk_valvula_{numero}", False)
    ]


# =====================================================
# ESTILO COMPACTO
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
    }

    div[data-testid="stCheckbox"] {
        margin-bottom: -14px;
    }

    div[data-testid="stCheckbox"] label {
        font-size: 0.72rem;
        min-height: 0.8rem;
    }

    div[data-testid="stCheckbox"] p {
        font-size: 0.72rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    h1, h2, h3 {
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# ENCABEZADO
# =====================================================
st.markdown(
    """
    <div style='text-align:center; padding: 4px 0 8px 0;'>
        <h1 style='color:#0E4C92; margin-bottom:2px;'>🔧 PANEL DE MANTENIMIENTO</h1>
        <h3 style='color:#2E86C1; margin-top:0px;'>VÁLVULAS KRONES · LÍNEA 2</h3>
        <p style='color:#5D6D7E; margin-bottom:4px;'>Seleccione las válvulas intervenidas y registre la mantención.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# PANEL DE DATOS GENERALES
# =====================================================
with st.container(border=True):
    st.subheader("📝 Datos generales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fecha = st.date_input("📅 Fecha")

    with col2:
        turno = st.selectbox("👷 Turno", TURNOS)

    with col3:
        operador = st.text_input(
            "👤 Operador",
            placeholder="Ej: JUAN PEREZ"
        ).upper()

    with col4:
        repuesto = st.selectbox("📦 Repuesto", REPUESTOS)

    observaciones = st.text_area(
        "📋 Observaciones",
        placeholder="Ingrese observaciones generales del mantenimiento...",
        height=70
    )

# =====================================================
# PANEL DE SELECCIÓN DE VÁLVULAS
# =====================================================
with st.container(border=True):
    st.subheader("🔘 Selección de válvulas")

    col_a, col_b, col_c = st.columns([1, 1, 4])

    with col_a:
        st.button(
            "✅ Seleccionar todas",
            use_container_width=True,
            on_click=seleccionar_todas
        )

    with col_b:
        st.button(
            "🧹 Limpiar",
            use_container_width=True,
            on_click=limpiar_seleccion
        )

    seleccionadas = obtener_valvulas_seleccionadas()

    with col_c:
        st.info(
            f"Seleccionadas: {len(seleccionadas)}",
            icon="📌"
        )

    columnas = 14

    for inicio in range(1, 113, columnas):
        cols = st.columns(columnas)

        for i, numero in enumerate(range(inicio, min(inicio + columnas, 113))):
            with cols[i]:
                st.checkbox(
                    f"{numero}",
                    key=f"chk_valvula_{numero}"
                )

# =====================================================
# RESUMEN Y GUARDADO
# =====================================================
with st.container(border=True):
    st.subheader("📌 Resumen y guardado")

    seleccionadas = obtener_valvulas_seleccionadas()

    if seleccionadas:
        st.success(
            f"Total seleccionadas: {len(seleccionadas)} | "
            f"Válvulas: {', '.join([str(v) for v in seleccionadas])}"
        )
    else:
        st.warning("No hay válvulas seleccionadas.")

    guardar = st.button(
        "💾 Guardar registros en Google Sheets",
        use_container_width=True,
        type="primary"
    )

# =====================================================
# GUARDADO FINAL
# =====================================================
if guardar:
    seleccionadas = obtener_valvulas_seleccionadas()

    if not operador.strip():
        st.error("❌ El operador no puede estar vacío.")

    elif len(seleccionadas) == 0:
        st.error("❌ Debe seleccionar al menos una válvula.")

    else:
        fecha_registro = obtener_hora_chile()

        filas = []

        for valvula in seleccionadas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador,
                valvula,
                repuesto,
                observaciones,
                fecha_registro
            ])

        try:
            guardar_registros(filas)

            st.success(
                f"✅ Se guardaron {len(filas)} registros correctamente en Google Sheets."
            )

            st.balloons()
            limpiar_seleccion()

        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
