"""
Portal Global CCU
App principal para navegar entre dashboards de Línea 2 y Línea 11.

Ubicación recomendada:
PROYECTO-1-CCU-/
└── app_global/
    └── app.py
"""

import base64
from pathlib import Path

import streamlit as st


# =====================================================
# RUTAS DEL PROYECTO
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "CCU_logo_(2018).svg.png"

APP_L2_TULIPAS = PROJECT_DIR / "DASHBOARD L2 TULIPAS" / "app13.py"
APP_L2_VALVULAS = PROJECT_DIR / "DASHBOARD L2 VALVULAS" / "app13.py"
APP_L11_TULIPAS = PROJECT_DIR / "DASHBOARD L11 TULIPAS" / "app9.py"
APP_L11_VALVULAS = PROJECT_DIR / "DASHBOARD L11 VALVULAS" / "app14.py"


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
        padding-top: 0.5rem;
        padding-bottom: 1rem;
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
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 2.2rem;
                margin-bottom: 1.4rem;
            ">
                <img
                    src="data:image/png;base64,{logo_base64}"
                    style="
                        width: 230px;
                        max-width: 75%;
                        display: block;
                    "
                    alt="Logo CCU"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =====================================================
# PÁGINA DE INICIO
# =====================================================

def pagina_inicio():
    mostrar_logo_centrado()

    st.markdown(
        """
        <div style='text-align:center; margin-bottom:1.6rem;'>
            <h1 style='margin-top:0;'>
                Portal Área de Operaciones CCU
            </h1>
            <p style='font-size:18px; opacity:0.75; margin-top:0.4rem;'>
                Selecciona un dashboard desde el menú lateral para revisar análisis de tulipas y válvulas.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
            **Línea 2 · Tulipas**

            Dashboard de análisis para Encajonadora / Desencajonadora Línea 2.

            Incluye mapas por ubicación física, KPIs, tendencia temporal,
            registros por turno, operador, formato y mantención.
            """
        )

    with col2:
        st.info(
            """
            **Línea 2 · Válvulas**

            Dashboard de mantenimiento de válvulas Krones Línea 2.

            Incluye estado global de válvulas, KPIs, tendencia temporal,
            análisis por turno, operador y tipo de mantención.
            """
        )

    col3, col4 = st.columns(2)

    with col3:
        st.info(
            """
            **Línea 11 · Tulipas**

            Dashboard de análisis para Encajonadora / Desencajonadora Línea 11.

            Incluye análisis por formato, cabezal, tulipa, equipo,
            operador, turno y tipo de mantención.
            """
        )

    with col4:
        st.info(
            """
            **Línea 11 · Válvulas**

            Dashboard de mantenimiento de válvulas Krones Línea 11.

            Incluye estado global de 152 válvulas, KPIs, registros por turno,
            operador, tipo de mantención y datos detallados.
            """
        )

    st.markdown("---")

    st.caption(
        "Portal central conectado a dashboards Streamlit del repositorio GitHub."
    )


# =====================================================
# VALIDACIÓN DE ARCHIVOS
# =====================================================

apps_requeridas = {
    "Línea 2 · Tulipas": APP_L2_TULIPAS,
    "Línea 2 · Válvulas": APP_L2_VALVULAS,
    "Línea 11 · Tulipas": APP_L11_TULIPAS,
    "Línea 11 · Válvulas": APP_L11_VALVULAS,
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
                icon="🏠"
            )
        ],
        "Línea 2": [
            st.Page(
                APP_L2_TULIPAS,
                title="Tulipas",
                icon="🧩"
            ),
            st.Page(
                APP_L2_VALVULAS,
                title="Válvulas",
                icon="⚙️"
            ),
        ],
        "Línea 11": [
            st.Page(
                APP_L11_TULIPAS,
                title="Tulipas",
                icon="🧩"
            ),
            st.Page(
                APP_L11_VALVULAS,
                title="Válvulas",
                icon="⚙️"
            ),
        ],
    }
)

pagina.run()
