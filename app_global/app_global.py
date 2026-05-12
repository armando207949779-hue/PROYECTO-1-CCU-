"""
Portal Global CCU
App principal para navegar entre dashboards de Línea 2 y Línea 11.
Incluye pestaña simple de alertas por dashboard.

Ubicación:
PROYECTO-1-CCU-/
└── app_global/
    └── app_global.py
"""

import base64
from pathlib import Path
from datetime import datetime, date

import pandas as pd
import streamlit as st


# =====================================================
# RUTAS DEL PROYECTO
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "CCU_logo_(2018).svg.png"

# Dashboards
APP_L2_TULIPAS = PROJECT_DIR / "DASHBOARD L2 TULIPAS" / "app13.py"
APP_L2_VALVULAS = PROJECT_DIR / "DASHBOARD L2 VALVULAS" / "app13.py"
APP_L11_TULIPAS = PROJECT_DIR / "DASHBOARD L11 TULIPAS" / "app9.py"
APP_L11_VALVULAS = PROJECT_DIR / "DASHBOARD L11 VALVULAS" / "app14.py"


# =====================================================
# GOOGLE SHEETS MONITOREADOS
# =====================================================

DASHBOARDS_MONITOREADOS = {
    "Línea 2 · Tulipas": {
        "sheet_id": "1EjrHHNJXjjBOObeAfIBxQjDfcyCS-o_j4FLaDxOPjRI",
        "tipo": "Tulipas",
        "linea": "Línea 2",
        "umbral_default": 3,
    },
    "Línea 2 · Válvulas": {
        "sheet_id": "12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI",
        "tipo": "Válvulas",
        "linea": "Línea 2",
        "umbral_default": 3,
    },
    "Línea 11 · Tulipas": {
        "sheet_id": "1PmDo4EjBxXZx0fPMGPMJKzBztyAq8AipxqCsJTFI0e0",
        "tipo": "Tulipas",
        "linea": "Línea 11",
        "umbral_default": 3,
    },
    "Línea 11 · Válvulas": {
        "sheet_id": "1ompaiCPCIegzgj80wHjPde5GL14660AUBnUTt6iTD_w",
        "tipo": "Válvulas",
        "linea": "Línea 11",
        "umbral_default": 3,
    },
}


# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Portal Operaciones CCU",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# ESTILO GENERAL
# =====================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 1.4rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
    }

    section[data-testid="stSidebar"] {
        padding-top: 0.5rem;
    }

    h1 {
        text-align: center;
        color: #0E4C92;
        line-height: 1.15;
    }

    h2 {
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.4rem;
    }

    .portal-logo {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 1.2rem;
        margin-bottom: 1.2rem;
    }

    .portal-logo img {
        width: 220px;
        max-width: 70%;
        display: block;
    }

    .portal-header {
        text-align: center;
        margin-bottom: 1.4rem;
    }

    .portal-header h1 {
        margin-top: 0;
        margin-bottom: 0.45rem;
    }

    .portal-header p {
        font-size: 17px;
        opacity: 0.75;
        margin-top: 0.3rem;
    }

    .estado-ok {
        background: linear-gradient(90deg, rgba(46, 204, 113, 0.16), rgba(232, 248, 239, 0.95));
        border-left: 7px solid #27AE60;
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 12px;
        margin-bottom: 18px;
    }

    .estado-ok-title {
        color: #145A32;
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .estado-ok-text {
        color: #196F3D;
        font-size: 0.95rem;
    }

    .estado-alerta {
        background: linear-gradient(90deg, rgba(231, 76, 60, 0.16), rgba(253, 237, 236, 0.95));
        border-left: 7px solid #E74C3C;
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 12px;
        margin-bottom: 18px;
    }

    .estado-alerta-title {
        color: #922B21;
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .estado-alerta-text {
        color: #943126;
        font-size: 0.95rem;
    }

    .kpi-ok {
        background-color: rgba(46, 204, 113, 0.12);
        border: 1px solid rgba(39, 174, 96, 0.35);
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
    }

    .kpi-alerta {
        background-color: rgba(231, 76, 60, 0.12);
        border: 1px solid rgba(192, 57, 43, 0.35);
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
    }

    .kpi-title {
        font-size: 0.88rem;
        opacity: 0.8;
        margin-bottom: 4px;
    }

    .kpi-value-ok {
        font-size: 1.8rem;
        color: #145A32;
        font-weight: 800;
    }

    .kpi-value-alerta {
        font-size: 1.8rem;
        color: #922B21;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# LOGO
# =====================================================

def mostrar_logo_centrado():
    if LOGO_PATH.exists():
        logo_base64 = base64.b64encode(
            LOGO_PATH.read_bytes()
        ).decode("utf-8")

        st.markdown(
            f"""
            <div class="portal-logo">
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
# ESTILO TABLAS ALERTAS
# =====================================================

def estilo_detalle_alertas(row):
    estado = str(row.get("Estado", "")).upper()

    if estado in ["ALERTA", "ERROR"]:
        return [
            "background-color: #FDEDEC; color: #922B21; font-weight: 700;"
            for _ in row
        ]

    return [
        "background-color: #EAFAF1; color: #145A32;"
        for _ in row
    ]


def tarjeta_estado(titulo, valor, alerta=False):
    clase = "kpi-alerta" if alerta else "kpi-ok"
    clase_valor = "kpi-value-alerta" if alerta else "kpi-value-ok"

    st.markdown(
        f"""
        <div class="{clase}">
            <div class="kpi-title">{titulo}</div>
            <div class="{clase_valor}">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# UTILIDADES ALERTAS
# =====================================================

def urls_google_sheet(sheet_id):
    return [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
    ]


@st.cache_data(ttl=1)
def cargar_sheet_alerta(sheet_id):
    ultimo_error = None

    for url in urls_google_sheet(sheet_id):
        try:
            df = pd.read_csv(url)
            df.columns = [str(c).strip() for c in df.columns]
            return df, None
        except Exception as e:
            ultimo_error = e

    return pd.DataFrame(), ultimo_error


def detectar_columna_fecha(df):
    posibles = [
        "Fecha registro",
        "Fecha Registro",
        "FECHA REGISTRO",
        "Fecha",
        "FECHA",
        "fecha",
    ]

    for col in posibles:
        if col in df.columns:
            return col

    return None


def detectar_columna_operador(df):
    posibles = [
        "Operador",
        "OPERADOR",
        "operador",
        "Usuario",
        "USUARIO",
        "usuario",
        "Responsable",
        "RESPONSABLE",
        "responsable",
    ]

    for col in posibles:
        if col in df.columns:
            return col

    return None


def detectar_columna_detalle_alerta(df):
    posibles = [
        "Detalle alerta insumo crítico",
        "Detalle alerta insumo critico",
        "DETALLE ALERTA INSUMO CRÍTICO",
        "DETALLE ALERTA INSUMO CRITICO",
        "Detalle alerta",
        "detalle alerta",
        "Detalle Alerta",
    ]

    for col in posibles:
        if col in df.columns:
            return col

    return None


def calcular_estado_dashboard(nombre, config, umbral_dias):
    df, error = cargar_sheet_alerta(config["sheet_id"])

    if error is not None and df.empty:
        return {
            "Dashboard": nombre,
            "Línea": config["linea"],
            "Tipo": config["tipo"],
            "Estado": "ERROR",
            "Último registro": "No disponible",
            "Último operador": "No disponible",
            "Días sin registro": None,
            "Umbral": umbral_dias,
            "Registros": 0,
            "Detalle alerta insumo crítico": "No disponible",
            "Detalle": f"No se pudo leer Google Sheets: {error}",
        }

    if df.empty:
        return {
            "Dashboard": nombre,
            "Línea": config["linea"],
            "Tipo": config["tipo"],
            "Estado": "ALERTA",
            "Último registro": "Sin registros",
            "Último operador": "Sin registros",
            "Días sin registro": None,
            "Umbral": umbral_dias,
            "Registros": 0,
            "Detalle alerta insumo crítico": "No disponible",
            "Detalle": "La hoja está vacía o no contiene registros válidos.",
        }

    columna_fecha = detectar_columna_fecha(df)
    columna_operador = detectar_columna_operador(df)
    columna_detalle_alerta = detectar_columna_detalle_alerta(df)

    if columna_fecha is None:
        return {
            "Dashboard": nombre,
            "Línea": config["linea"],
            "Tipo": config["tipo"],
            "Estado": "ERROR",
            "Último registro": "No disponible",
            "Último operador": "No disponible",
            "Días sin registro": None,
            "Umbral": umbral_dias,
            "Registros": len(df),
            "Detalle alerta insumo crítico": "No disponible",
            "Detalle": "No se encontró columna Fecha o Fecha registro.",
        }

    df_tmp = df.copy()

    df_tmp["_fecha_alerta"] = pd.to_datetime(
        df_tmp[columna_fecha],
        dayfirst=True,
        errors="coerce"
    )

    df_tmp = df_tmp.dropna(subset=["_fecha_alerta"])

    if df_tmp.empty:
        return {
            "Dashboard": nombre,
            "Línea": config["linea"],
            "Tipo": config["tipo"],
            "Estado": "ALERTA",
            "Último registro": "Sin fechas válidas",
            "Último operador": "No disponible",
            "Días sin registro": None,
            "Umbral": umbral_dias,
            "Registros": len(df),
            "Detalle alerta insumo crítico": "No disponible",
            "Detalle": f"La columna {columna_fecha} no contiene fechas válidas.",
        }

    ultimo = df_tmp.sort_values("_fecha_alerta").iloc[-1]
    ultima_fecha = ultimo["_fecha_alerta"]

    if columna_operador is not None:
        ultimo_operador = str(ultimo[columna_operador]).strip().upper()

        if ultimo_operador in ["", "NAN", "NONE", "NAT"]:
            ultimo_operador = "SIN OPERADOR"
    else:
        ultimo_operador = "No disponible"

    if columna_detalle_alerta is not None:
        detalle_alerta_insumo = str(ultimo[columna_detalle_alerta]).strip()

        if detalle_alerta_insumo.upper() in ["", "NAN", "NONE", "NAT"]:
            detalle_alerta_insumo = "Sin detalle"
    else:
        detalle_alerta_insumo = "No disponible"

    hoy = pd.Timestamp(date.today())

    dias_calculados = int((hoy.normalize() - ultima_fecha.normalize()).days)

    # Evita mostrar días negativos cuando la fecha del registro viene futura
    dias_sin_registro = max(dias_calculados, 0)

    if dias_calculados < 0:
        estado = "OK"
        detalle = "Último registro vigente. Días sin registro ajustado a 0."
    elif dias_sin_registro > umbral_dias:
        estado = "ALERTA"
        detalle = f"Han pasado {dias_sin_registro} días desde el último registro."
    else:
        estado = "OK"
        detalle = f"Último registro dentro del umbral de {umbral_dias} días."

    return {
        "Dashboard": nombre,
        "Línea": config["linea"],
        "Tipo": config["tipo"],
        "Estado": estado,
        "Último registro": ultima_fecha.strftime("%d-%m-%Y %H:%M"),
        "Último operador": ultimo_operador,
        "Días sin registro": dias_sin_registro,
        "Umbral": umbral_dias,
        "Registros": len(df),
        "Detalle alerta insumo crítico": detalle_alerta_insumo,
        "Detalle": detalle,
    }


# =====================================================
# PÁGINA INICIO
# =====================================================

def pagina_inicio():
    mostrar_logo_centrado()

    st.markdown(
        """
        <div class='portal-header'>
            <h1>Portal Área de Operaciones CCU</h1>
            <p>Selecciona un dashboard desde el menú lateral.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("## Dashboards")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "**Línea 2 · Tulipas**\n\n"
            "Dashboard de análisis para Encajonadora / Desencajonadora Línea 2."
        )

    with col2:
        st.info(
            "**Línea 2 · Válvulas**\n\n"
            "Dashboard de mantenimiento de válvulas Krones Línea 2."
        )

    col3, col4 = st.columns(2)

    with col3:
        st.info(
            "**Línea 11 · Tulipas**\n\n"
            "Dashboard de análisis para Encajonadora / Desencajonadora Línea 11."
        )

    with col4:
        st.info(
            "**Línea 11 · Válvulas**\n\n"
            "Dashboard de mantenimiento de válvulas Krones Línea 11."
        )

    st.markdown("---")

    st.caption("Portal central conectado a dashboards Streamlit del repositorio GitHub.")


# =====================================================
# PÁGINA ALERTAS
# =====================================================

def pagina_alertas():
    mostrar_logo_centrado()

    st.markdown(
        """
        <div class='portal-header'>
            <h1>Alertas de registros pendientes</h1>
            <p>Detalle por dashboard con estado de actualización de registros.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown("## Configuración de alertas")

    umbral_global = st.sidebar.number_input(
        "Días máximos sin registro",
        min_value=1,
        max_value=90,
        value=3,
        step=1
    )

    if st.sidebar.button("Actualizar alertas"):
        st.cache_data.clear()
        st.rerun()

    resultados = []

    for nombre, config in DASHBOARDS_MONITOREADOS.items():
        estado = calcular_estado_dashboard(
            nombre=nombre,
            config=config,
            umbral_dias=umbral_global
        )
        resultados.append(estado)

    df_alertas = pd.DataFrame(resultados)

    if df_alertas.empty:
        st.warning("No hay dashboards configurados para monitorear.")
        return

    df_alertas["Días sin registro"] = pd.to_numeric(
        df_alertas["Días sin registro"],
        errors="coerce"
    )

    total_alertas = int((df_alertas["Estado"] == "ALERTA").sum())
    total_errores = int((df_alertas["Estado"] == "ERROR").sum())
    total_problemas = total_alertas + total_errores
    total_ok = int((df_alertas["Estado"] == "OK").sum())

    col_ok, col_alerta = st.columns(2)

    with col_ok:
        tarjeta_estado("Dashboards OK", total_ok, alerta=False)

    with col_alerta:
        tarjeta_estado(
            "Dashboards con alerta/error",
            total_problemas,
            alerta=total_problemas > 0
        )

    if total_problemas > 0:
        st.markdown(
            f"""
            <div class="estado-alerta">
                <div class="estado-alerta-title">
                    Alerta activa
                </div>
                <div class="estado-alerta-text">
                    Hay {total_problemas} dashboard(s) con alerta o error.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="estado-ok">
                <div class="estado-ok-title">
                    Estado operacional OK
                </div>
                <div class="estado-ok-text">
                    Todos los dashboards monitoreados están dentro del umbral configurado.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("## Detalle por dashboard")

    with st.expander("Ver detalle por dashboard", expanded=True):
        df_detalle = df_alertas.copy()

        df_detalle["Días sin registro"] = df_detalle["Días sin registro"].apply(
            lambda x: "N/A" if pd.isna(x) else max(int(x), 0)
        )

        columnas_detalle = [
            "Línea",
            "Tipo",
            "Estado",
            "Último registro",
            "Último operador",
            "Días sin registro",
            "Umbral",
            "Registros",
            "Detalle alerta insumo crítico",
            "Detalle",
        ]

        st.dataframe(
            df_detalle[columnas_detalle].style.apply(estilo_detalle_alertas, axis=1),
            use_container_width=True,
            hide_index=True
        )

    st.download_button(
        "Descargar detalle CSV",
        df_alertas.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"detalle_alertas_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


# =====================================================
# VALIDACIÓN DE ARCHIVOS
# =====================================================

apps_requeridas = {
    "Dashboard Línea 2 · Tulipas": APP_L2_TULIPAS,
    "Dashboard Línea 2 · Válvulas": APP_L2_VALVULAS,
    "Dashboard Línea 11 · Tulipas": APP_L11_TULIPAS,
    "Dashboard Línea 11 · Válvulas": APP_L11_VALVULAS,
}

apps_faltantes = {
    nombre: ruta
    for nombre, ruta in apps_requeridas.items()
    if not ruta.exists()
}

if apps_faltantes:
    mostrar_logo_centrado()

    st.error(
        "No se encontraron una o más apps. Revisa los nombres de carpetas y archivos."
    )

    st.write("### Rutas buscadas")

    for nombre, ruta in apps_requeridas.items():
        if ruta.exists():
            st.success(f"{nombre}: `{ruta}`")
        else:
            st.error(f"{nombre}: `{ruta}`")

    st.stop()


# =====================================================
# NAVEGACIÓN ENTRE DASHBOARDS
# =====================================================

pagina = st.navigation(
    {
        "Inicio": [
            st.Page(
                pagina_inicio,
                title="Inicio",
                icon="🏠",
                url_path="inicio"
            ),
            st.Page(
                pagina_alertas,
                title="Alertas",
                icon="🚨",
                url_path="alertas"
            ),
        ],
        "Dashboards · Línea 2": [
            st.Page(
                APP_L2_TULIPAS,
                title="Tulipas",
                icon="📊",
                url_path="dashboard-linea-2-tulipas"
            ),
            st.Page(
                APP_L2_VALVULAS,
                title="Válvulas",
                icon="📊",
                url_path="dashboard-linea-2-valvulas"
            ),
        ],
        "Dashboards · Línea 11": [
            st.Page(
                APP_L11_TULIPAS,
                title="Tulipas",
                icon="📊",
                url_path="dashboard-linea-11-tulipas"
            ),
            st.Page(
                APP_L11_VALVULAS,
                title="Válvulas",
                icon="📊",
                url_path="dashboard-linea-11-valvulas"
            ),
        ],
    },
    expanded=True
)

pagina.run()
