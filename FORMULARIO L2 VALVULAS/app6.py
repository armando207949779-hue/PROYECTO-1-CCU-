# App6 Streamlit para formulario de mantenimiento VALVULAS Línea 2 - VERTICAL

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Formulario de Mantenimiento VALVULAS Línea 2",
    page_icon="🔧",
    layout="centered"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

TURNOS = ["A", "B", "C"]
NUMEROS_VALVULA = list(range(1, 113))
REPUESTOS = ["BLOQUE", "O-RINGS", "RESORTE", "ON/OFF", "OTRO"]

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
        "Fecha", "Turno", "Operador", "Número Válvula", "Repuesto",
        "Observaciones", "Fecha registro"
    ]
    try:
        if ws.row_values(1) != headers:
            ws.update("A1:G1", [headers])
    except:
        ws.update("A1:G1", [headers])

def guardar(data):
    ws = conectar()
    init_sheet(ws)
    ws.append_row(data, value_input_option="USER_ENTERED")

def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")

st.markdown(
    """
    <div style='text-align: center; padding: 12px 10px 4px 10px;'>
        <h1 style='color:#0E4C92; margin-bottom:4px; font-size: 2.2rem;'>
            🔧 FORMULARIO DE MANTENIMIENTO
        </h1>
        <h2 style='color:#2E86C1; margin-top:0px; font-size: 1.25rem; font-weight: 600;'>
            VÁLVULAS KRONES · LÍNEA 2
        </h2>
        <p style='color:#5D6D7E; font-size: 1rem; margin-top: 8px;'>
            Registro de mantenciones de válvulas (1-112)
        </p>
        <hr style='border: 1px solid #D6EAF8; width:75%; margin-top: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("📝 Complete el formulario para guardar el registro en Google Sheets.")

with st.container(border=True):
    with st.form("form_mantenimiento_valvulas", clear_on_submit=True):
        
        fecha = st.date_input("📅 Fecha")
        
        turno = st.selectbox("👷 Turno", TURNOS)
        
        operador = st.text_input(
            "👤 Operador",
            placeholder="Ej: JUAN PEREZ",
            help="Ingrese nombre y apellido en MAYÚSCULAS"
        ).upper()

        numero_valvula = st.selectbox("🔧 Número de Válvula", NUMEROS_VALVULA)
        
        repuesto = st.selectbox("📦 Repuesto", REPUESTOS)

        observaciones = st.text_area(
            "📋 Observaciones",
            height=120,
            placeholder="Escriba aquí observaciones adicionales..."
        )

        submit = st.form_submit_button("💾 Guardar registro", use_container_width=True)

if submit:
    if not operador.strip():
        st.error("❌ El operador no puede estar vacío")
    else:
        # Guardar registro
        fila = [
            fecha.strftime("%d-%m-%Y"),
            turno,
            operador,
            numero_valvula,
            repuesto,
            observaciones,
            obtener_hora_chile()
        ]
        
        try:
            guardar(fila)
            st.success("✅ Registro guardado correctamente en Google Sheets.")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
