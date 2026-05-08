"""
Portal Global CCU
App principal para navegar entre dashboards y formularios de Línea 2 y Línea 11.
Incluye pestaña de alertas por falta de registros recientes y descarga PDF.

Ubicación:
PROYECTO-1-CCU-/
└── app_global/
    └── app_global.py
"""

import base64
from pathlib import Path
from datetime import datetime, date
from io import BytesIO

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

# Formularios
FORM_L2_TULIPAS = PROJECT_DIR / "FORMULARIO L2 TULIPAS" / "app7.py"
FORM_L2_VALVULAS = PROJECT_DIR / "FORMULARIO L2 VALVULAS" / "app6.py"
FORM_L11_TULIPAS = PROJECT_DIR / "FORMULARIO L11 TULIPAS" / "app.py"
FORM_L11_VALVULAS = PROJECT_DIR / "FORMULARIO L11 VALVULAS" / "app7.py"


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
            "Detalle": "La hoja está vacía o no contiene registros válidos.",
        }

    columna_fecha = detectar_columna_fecha(df)
    columna_operador = detectar_columna_operador(df)

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

    hoy = pd.Timestamp(date.today())
    dias_sin_registro = int((hoy.normalize() - ultima_fecha.normalize()).days)

    if dias_sin_registro < 0:
        estado = "OK"
        detalle = "Último registro tiene fecha futura o igual a hoy."
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
        "Detalle": detalle,
    }


def tarjeta_resumen(titulo, valor, icono=None):
    with st.container(border=True):
        st.caption(titulo)

        if icono:
            st.markdown(f"### {icono} {valor}")
        else:
            st.markdown(f"### {valor}")


def tarjeta_estado_alerta(row):
    estado = row["Estado"]
    dashboard = row["Dashboard"]
    linea = row["Línea"]
    tipo = row["Tipo"]
    ultimo = row["Último registro"]
    ultimo_operador = row.get("Último operador", "No disponible")
    dias = row["Días sin registro"]
    umbral = row["Umbral"]
    registros = row["Registros"]
    detalle = row["Detalle"]

    if estado == "OK":
        icono = "✅"
        estado_txt = "Al día"
    elif estado == "ALERTA":
        icono = "🚨"
        estado_txt = "Revisar"
    else:
        icono = "⚠️"
        estado_txt = "Error"

    if pd.isna(dias):
        dias_txt = "N/A"
    else:
        try:
            dias_txt = str(int(dias))
        except Exception:
            dias_txt = "N/A"

    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([0.45, 2.0, 1.0, 1.0, 2.0])

        with c1:
            st.markdown(f"### {icono}")

        with c2:
            st.markdown(f"**{dashboard}**")
            st.caption(f"{linea} · {tipo}")

        with c3:
            st.caption("Estado")

            if estado == "OK":
                st.success(estado_txt)
            elif estado == "ALERTA":
                st.error(estado_txt)
            else:
                st.warning(estado_txt)

        with c4:
            st.caption("Días sin registro")
            st.markdown(f"### {dias_txt}")

        with c5:
            st.caption("Último registro")
            st.markdown(f"**{ultimo}**")
            st.markdown(f"**Operador:** {ultimo_operador}")
            st.caption(f"Umbral: {umbral} días · Registros: {registros}")

        if estado != "OK":
            st.caption(detalle)


# =====================================================
# PDF ALERTAS
# =====================================================

def generar_pdf_alertas(df_alertas, umbral_global):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        return None

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.1 * cm,
        leftMargin=1.1 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0E4C92"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCenter",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=12,
    )

    normal_style = styles["Normal"]
    normal_style.fontSize = 8
    normal_style.leading = 10

    story = []

    fecha_reporte = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    story.append(Paragraph("Reporte de Alertas - Dashboards CCU", title_style))
    story.append(
        Paragraph(
            f"Generado: {fecha_reporte} | Umbral global: {umbral_global} días sin registro",
            subtitle_style
        )
    )

    total_dashboards = len(df_alertas)
    total_ok = int((df_alertas["Estado"] == "OK").sum())
    total_alertas = int((df_alertas["Estado"] == "ALERTA").sum())
    total_error = int((df_alertas["Estado"] == "ERROR").sum())

    resumen_data = [
        ["Dashboards", "Al día", "Alertas", "Errores"],
        [str(total_dashboards), str(total_ok), str(total_alertas), str(total_error)],
    ]

    resumen_table = Table(
        resumen_data,
        colWidths=[5 * cm, 5 * cm, 5 * cm, 5 * cm]
    )

    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E4C92")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ]))

    story.append(resumen_table)
    story.append(Spacer(1, 0.35 * cm))

    columnas = [
        "Línea",
        "Dashboard",
        "Estado",
        "Último registro",
        "Último operador",
        "Días",
        "Umbral",
        "Registros",
    ]

    data = [columnas]

    df_pdf = df_alertas.copy()

    df_pdf["Días sin registro"] = pd.to_numeric(
        df_pdf["Días sin registro"],
        errors="coerce"
    )

    df_pdf = df_pdf.sort_values(
        by=["Línea", "Días sin registro"],
        ascending=[True, False],
        na_position="last"
    )

    for _, row in df_pdf.iterrows():
        dias = row.get("Días sin registro", None)

        if pd.isna(dias):
            dias_txt = "N/A"
        else:
            dias_txt = str(int(dias))

        data.append([
            str(row.get("Línea", "")),
            str(row.get("Dashboard", "")),
            str(row.get("Estado", "")),
            str(row.get("Último registro", "")),
            str(row.get("Último operador", "No disponible")),
            dias_txt,
            str(row.get("Umbral", "")),
            str(row.get("Registros", "")),
        ])

    table = Table(
        data,
        colWidths=[
            2.3 * cm,
            4.1 * cm,
            2.0 * cm,
            3.1 * cm,
            4.5 * cm,
            1.6 * cm,
            1.7 * cm,
            1.9 * cm,
        ],
        repeatRows=1
    )

    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    for i in range(1, len(data)):
        estado = data[i][2]

        if estado == "ALERTA":
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fee2e2")))
        elif estado == "ERROR":
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fef3c7")))
        else:
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#dcfce7")))

    table.setStyle(TableStyle(table_style))

    story.append(table)
    story.append(Spacer(1, 0.25 * cm))

    story.append(
        Paragraph(
            "Criterio: se genera alerta cuando los días sin registro son mayores al umbral configurado.",
            normal_style
        )
    )

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


# =====================================================
# PÁGINA INICIO
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
                Selecciona un dashboard o formulario desde el menú lateral.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("## Dashboards")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
            **Línea 2 · Tulipas**

            Dashboard de análisis para Encajonadora / Desencajonadora Línea 2.
            """
        )

    with col2:
        st.info(
            """
            **Línea 2 · Válvulas**

            Dashboard de mantenimiento de válvulas Krones Línea 2.
            """
        )

    col3, col4 = st.columns(2)

    with col3:
        st.info(
            """
            **Línea 11 · Tulipas**

            Dashboard de análisis para Encajonadora / Desencajonadora Línea 11.
            """
        )

    with col4:
        st.info(
            """
            **Línea 11 · Válvulas**

            Dashboard de mantenimiento de válvulas Krones Línea 11.
            """
        )

    st.markdown("---")

    st.markdown("## Formularios")

    f1, f2 = st.columns(2)

    with f1:
        st.success(
            """
            **Formularios Línea 2**

            Registro operacional para tulipas y válvulas.
            """
        )

    with f2:
        st.success(
            """
            **Formularios Línea 11**

            Registro operacional para tulipas y válvulas.
            """
        )

    st.markdown("---")

    st.caption("Portal central conectado a dashboards y formularios Streamlit del repositorio GitHub.")


# =====================================================
# PÁGINA ALERTAS
# =====================================================

def pagina_alertas():
    mostrar_logo_centrado()

    st.markdown(
        """
        <div style='text-align:center; margin-bottom:1.2rem;'>
            <h1 style='margin-top:0;'>
                Alertas de registros pendientes
            </h1>
            <p style='font-size:17px; opacity:0.75; margin-top:0.4rem;'>
                Dashboards separados por línea y ordenados por mayor cantidad de días sin registro.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.sidebar.markdown("## Configuración de alertas")

    umbral_global = st.sidebar.number_input(
        "Días máximos sin registro",
        min_value=1,
        max_value=90,
        value=3,
        step=1
    )

    usar_umbral_personalizado = st.sidebar.checkbox(
        "Configurar por dashboard",
        value=False
    )

    umbrales = {}

    if usar_umbral_personalizado:
        for nombre, config in DASHBOARDS_MONITOREADOS.items():
            umbrales[nombre] = st.sidebar.number_input(
                nombre,
                min_value=1,
                max_value=90,
                value=int(config.get("umbral_default", 3)),
                step=1
            )
    else:
        for nombre in DASHBOARDS_MONITOREADOS:
            umbrales[nombre] = umbral_global

    if st.sidebar.button("Actualizar alertas"):
        st.cache_data.clear()
        st.rerun()

    resultados = []

    for nombre, config in DASHBOARDS_MONITOREADOS.items():
        estado = calcular_estado_dashboard(
            nombre=nombre,
            config=config,
            umbral_dias=umbrales[nombre]
        )
        resultados.append(estado)

    df_alertas = pd.DataFrame(resultados)

    if df_alertas.empty:
        st.warning("No hay dashboards configurados para monitorear.")
        return

    df_alertas["Orden días"] = pd.to_numeric(
        df_alertas["Días sin registro"],
        errors="coerce"
    ).fillna(-1)

    df_alertas = (
        df_alertas
        .sort_values(
            by=["Orden días", "Estado"],
            ascending=[False, True]
        )
        .drop(columns=["Orden días"])
        .reset_index(drop=True)
    )

    total_dashboards = len(df_alertas)
    total_ok = int((df_alertas["Estado"] == "OK").sum())
    total_alertas = int((df_alertas["Estado"] == "ALERTA").sum())
    total_error = int((df_alertas["Estado"] == "ERROR").sum())

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        tarjeta_resumen("Dashboards", total_dashboards)

    with k2:
        tarjeta_resumen("Al día", total_ok, "✅")

    with k3:
        tarjeta_resumen("Alertas", total_alertas, "🚨")

    with k4:
        tarjeta_resumen("Errores", total_error, "⚠️")

    if total_alertas > 0:
        st.error(
            f"{total_alertas} dashboard(s) superan el umbral de {umbral_global} días sin registros."
        )
    elif total_error > 0:
        st.warning(
            f"No hay alertas por antigüedad, pero hay {total_error} dashboard(s) con error de lectura."
        )
    else:
        st.success(
            f"Todos los dashboards tienen registros dentro del umbral de {umbral_global} días."
        )

    st.markdown("---")

    df_linea_2 = df_alertas[df_alertas["Línea"] == "Línea 2"].copy()

    st.markdown("## Línea 2")

    if df_linea_2.empty:
        st.info("No hay dashboards configurados para Línea 2.")
    else:
        l2_ok = int((df_linea_2["Estado"] == "OK").sum())
        l2_alertas = int((df_linea_2["Estado"] == "ALERTA").sum())
        l2_error = int((df_linea_2["Estado"] == "ERROR").sum())

        c1, c2, c3 = st.columns(3)

        with c1:
            tarjeta_resumen("Al día Línea 2", l2_ok, "✅")

        with c2:
            tarjeta_resumen("Alertas Línea 2", l2_alertas, "🚨")

        with c3:
            tarjeta_resumen("Errores Línea 2", l2_error, "⚠️")

        for _, row in df_linea_2.iterrows():
            tarjeta_estado_alerta(row)

    st.markdown("---")

    df_linea_11 = df_alertas[df_alertas["Línea"] == "Línea 11"].copy()

    st.markdown("## Línea 11")

    if df_linea_11.empty:
        st.info("No hay dashboards configurados para Línea 11.")
    else:
        l11_ok = int((df_linea_11["Estado"] == "OK").sum())
        l11_alertas = int((df_linea_11["Estado"] == "ALERTA").sum())
        l11_error = int((df_linea_11["Estado"] == "ERROR").sum())

        c1, c2, c3 = st.columns(3)

        with c1:
            tarjeta_resumen("Al día Línea 11", l11_ok, "✅")

        with c2:
            tarjeta_resumen("Alertas Línea 11", l11_alertas, "🚨")

        with c3:
            tarjeta_resumen("Errores Línea 11", l11_error, "⚠️")

        for _, row in df_linea_11.iterrows():
            tarjeta_estado_alerta(row)

    st.markdown("---")

    with st.expander("Ver tabla completa y descargas", expanded=False):
        df_alertas_mostrar = df_alertas.copy()

        df_alertas_mostrar["Días sin registro"] = df_alertas_mostrar[
            "Días sin registro"
        ].fillna("N/A")

        st.dataframe(
            df_alertas_mostrar,
            use_container_width=True,
            height=260
        )

        st.download_button(
            "Descargar resumen de alertas CSV",
            df_alertas.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"alertas_dashboards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        pdf_bytes = generar_pdf_alertas(df_alertas, umbral_global)

        if pdf_bytes is None:
            st.warning(
                "Para descargar PDF, agrega `reportlab` en requirements.txt."
            )
        else:
            st.download_button(
                "Descargar reporte de alertas PDF",
                pdf_bytes,
                file_name=f"reporte_alertas_dashboards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )


# =====================================================
# VALIDACIÓN DE ARCHIVOS
# =====================================================

apps_requeridas = {
    # Dashboards
    "Dashboard Línea 2 · Tulipas": APP_L2_TULIPAS,
    "Dashboard Línea 2 · Válvulas": APP_L2_VALVULAS,
    "Dashboard Línea 11 · Tulipas": APP_L11_TULIPAS,
    "Dashboard Línea 11 · Válvulas": APP_L11_VALVULAS,

    # Formularios
    "Formulario Línea 2 · Tulipas": FORM_L2_TULIPAS,
    "Formulario Línea 2 · Válvulas": FORM_L2_VALVULAS,
    "Formulario Línea 11 · Tulipas": FORM_L11_TULIPAS,
    "Formulario Línea 11 · Válvulas": FORM_L11_VALVULAS,
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
# NAVEGACIÓN ENTRE DASHBOARDS Y FORMULARIOS
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
        "Formularios · Línea 2": [
            st.Page(
                FORM_L2_TULIPAS,
                title="Tulipas",
                icon="📝",
                url_path="formulario-linea-2-tulipas"
            ),
            st.Page(
                FORM_L2_VALVULAS,
                title="Válvulas",
                icon="📝",
                url_path="formulario-linea-2-valvulas"
            ),
        ],
        "Formularios · Línea 11": [
            st.Page(
                FORM_L11_TULIPAS,
                title="Tulipas",
                icon="📝",
                url_path="formulario-linea-11-tulipas"
            ),
            st.Page(
                FORM_L11_VALVULAS,
                title="Válvulas",
                icon="📝",
                url_path="formulario-linea-11-valvulas"
            ),
        ],
    },
    expanded=True
)

pagina.run()
