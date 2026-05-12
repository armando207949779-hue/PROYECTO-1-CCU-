"""
Dashboard de Mantenimiento de Válvulas Krones - Línea 11
Conectado al formulario Streamlit y Google Sheets.
Dashboard Área de Operaciones - Análisis de válvulas Krones.
Actualización: 154 válvulas + SONDA + alerta insumos críticos.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Dashboard Válvulas Krones Línea 11",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# PARÁMETROS GENERALES
# =====================================================
SHEET_ID = "1ompaiCPCIegzgj80wHjPde5GL14660AUBnUTt6iTD_w"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Línea 11 actualizada a 154 válvulas
VALVULAS_TODAS = list(range(1, 155))

TIPOS_MANTENCION = [
    "BLOQUE",
    "O-RINGS",
    "RESORTE",
    "ON/OFF",
    "SONDA",
    "OTRO"
]

OPERADORES_ESPERADOS = [
    "GUSTAVO ADOLFO MORÓN AGUILERA",
    "JAVIER FLORES LLANCANAO",
    "MARCO QUILAHUEQUE CONTRERAS",
    "NEFTALI RUBINOT ALARCON"
]

COLORS_REPUESTO = {
    "BLOQUE": "#3498db",
    "O-RINGS": "#e74c3c",
    "RESORTE": "#2ecc71",
    "ON/OFF": "#f39c12",
    "SONDA": "#16a085",
    "OTRO": "#9b59b6",
    "SIN MANTENCIÓN": "#95a5a6"
}

GRID = "rgba(128,128,128,0.15)"
LINE = "rgba(128,128,128,0.30)"

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
        margin-bottom: 0.2rem;
        color: #0E4C92;
        line-height: 1.15;
    }

    h2 {
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.4rem;
    }

    .alerta-panel {
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.16), rgba(255, 248, 220, 0.72));
        border-left: 6px solid #F4B400;
        border-radius: 12px;
        padding: 14px 18px;
        margin-top: 8px;
        margin-bottom: 16px;
    }

    .alerta-panel-title {
        color: #8A6D00;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .alerta-panel-text {
        color: #6E5A00;
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FUNCIONES BASE
# =====================================================
def aplicar_estilo_figura(fig, title, height=350, l=70, r=80, t=85, b=75):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color="#1a237e"),
            x=0.01
        ),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=l, r=r, t=t, b=b),
        font=dict(family="Arial, sans-serif", size=10),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.98)",
            bordercolor="#1f2937",
            font=dict(color="#111827", size=12)
        )
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        showline=True,
        linecolor=LINE
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        showline=True,
        linecolor=LINE
    )

    return fig


def tarjeta_kpi(titulo, valor, detalle=None, alerta=False):
    with st.container(border=True):
        st.caption(titulo)

        if alerta:
            st.markdown(f"### ⚠️ {valor}")
        else:
            st.markdown(f"### {valor}")

        if detalle:
            if alerta:
                st.warning(detalle)
            else:
                st.success(detalle)


def obtener_ultimo_registro(df):
    if df.empty:
        return "Sin datos", "-"

    df_tmp = df.copy()

    if "Fecha registro" in df_tmp.columns:
        df_tmp["Fecha_orden"] = pd.to_datetime(
            df_tmp["Fecha registro"],
            errors="coerce"
        )
        df_tmp["Fecha_orden"] = df_tmp["Fecha_orden"].fillna(df_tmp["Fecha"])
    else:
        df_tmp["Fecha_orden"] = df_tmp["Fecha"]

    df_tmp = df_tmp.dropna(subset=["Fecha_orden"])

    if df_tmp.empty:
        return "Sin datos", "-"

    ultimo = df_tmp.sort_values("Fecha_orden").iloc[-1]

    fecha = ultimo["Fecha_orden"]
    operador = ultimo["Operador"] if str(ultimo["Operador"]).strip() else "SIN OPERADOR"

    fecha_txt = fecha.strftime("%d-%m-%Y %H:%M") if pd.notna(fecha) else "-"

    return fecha_txt, operador


def obtener_valvula_mas_critica(df):
    if df.empty or "Válvula" not in df.columns:
        return "Sin datos", 0

    conteo = (
        df.groupby("Válvula")
        .size()
        .reset_index(name="Intervenciones")
        .sort_values("Intervenciones", ascending=False)
    )

    if conteo.empty:
        return "Sin datos", 0

    top = conteo.iloc[0]

    return f"Válvula {int(top['Válvula'])}", int(top["Intervenciones"])


def obtener_operador_menos_registros(df_filtrado, operadores_disponibles):
    if not operadores_disponibles:
        return "Sin operadores", 0

    if df_filtrado.empty or "Operador" not in df_filtrado.columns:
        operador = str(operadores_disponibles[0]).strip().upper()
        return operador, 0

    conteo = (
        df_filtrado["Operador"]
        .replace("", "SIN OPERADOR")
        .value_counts()
        .to_dict()
    )

    registros_operadores = []

    for operador in operadores_disponibles:
        operador_txt = str(operador).strip().upper()
        cantidad = conteo.get(operador_txt, 0)

        registros_operadores.append({
            "Operador": operador_txt,
            "Registros": cantidad
        })

    df_operadores = pd.DataFrame(registros_operadores)

    if df_operadores.empty:
        return "Sin operadores", 0

    menor = df_operadores.sort_values(
        ["Registros", "Operador"],
        ascending=[True, True]
    ).iloc[0]

    return menor["Operador"], int(menor["Registros"])


def fig_sin_datos():
    fig = go.Figure()
    fig.add_annotation(
        text="Sin datos",
        showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def crear_dataframe_vacio():
    columnas = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Observaciones",
        "Alerta insumos críticos",
        "Detalle alerta insumo crítico"
    ]

    return pd.DataFrame(columns=columnas)


# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data(ttl=1)
def cargar_datos():
    try:
        df = pd.read_csv(CSV_URL)
    except Exception:
        return crear_dataframe_vacio()

    df.columns = [str(c).strip() for c in df.columns]

    rename_cols = {
        "Número Válvula": "Válvula",
        "Número válvula": "Válvula",
        "Numero Válvula": "Válvula",
        "Numero Valvula": "Válvula",
        "N° Válvula": "Válvula",
        "N° Valvula": "Válvula",
        "Repuesto": "Mantención",
        "Repuesto / Mantención": "Mantención",
        "Repuesto / Mantencion": "Mantención",
        "Fecha Registro": "Fecha registro",
        "Fecha registro": "Fecha registro",
        "Alerta Insumos Críticos": "Alerta insumos críticos",
        "Alerta insumos criticos": "Alerta insumos críticos",
        "Alerta insumos críticos": "Alerta insumos críticos",
        "Detalle alerta insumo critico": "Detalle alerta insumo crítico",
        "Detalle alerta insumo crítico": "Detalle alerta insumo crítico"
    }

    df = df.rename(columns={c: rename_cols[c] for c in df.columns if c in rename_cols})

    columnas_necesarias = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Observaciones"
    ]

    faltantes = [c for c in columnas_necesarias if c not in df.columns]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en Google Sheets: {faltantes}")

    if "Alerta insumos críticos" not in df.columns:
        df["Alerta insumos críticos"] = "No"

    if "Detalle alerta insumo crítico" not in df.columns:
        df["Detalle alerta insumo crítico"] = ""

    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
    df["Válvula"] = pd.to_numeric(df["Válvula"], errors="coerce")

    if "Fecha registro" in df.columns:
        df["Fecha registro"] = pd.to_datetime(df["Fecha registro"], errors="coerce")
        df["Fecha"] = df["Fecha"].fillna(df["Fecha registro"])

    df["Turno"] = df["Turno"].fillna("").astype(str).str.strip().str.upper()
    df["Operador"] = df["Operador"].fillna("").astype(str).str.strip().str.upper()
    df["Mantención"] = df["Mantención"].fillna("").astype(str).str.strip().str.upper()
    df["Observaciones"] = df["Observaciones"].fillna("").astype(str).str.strip()

    df["Alerta insumos críticos"] = (
        df["Alerta insumos críticos"]
        .fillna("No")
        .astype(str)
        .str.strip()
        .str.capitalize()
    )

    df["Alerta insumos críticos"] = df["Alerta insumos críticos"].replace({
        "Si": "Sí",
        "SI": "Sí",
        "SÍ": "Sí",
        "TRUE": "Sí",
        "True": "Sí",
        "1": "Sí",
        "NO": "No",
        "False": "No",
        "FALSE": "No",
        "0": "No",
        "": "No"
    })

    df["Detalle alerta insumo crítico"] = (
        df["Detalle alerta insumo crítico"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df = df.dropna(subset=["Fecha", "Válvula"]).copy()

    if df.empty:
        columnas_finales = [
            "Fecha",
            "Turno",
            "Operador",
            "Válvula",
            "Mantención",
            "Observaciones",
            "Alerta insumos críticos",
            "Detalle alerta insumo crítico"
        ]

        if "Fecha registro" in df.columns:
            columnas_finales.append("Fecha registro")

        if "Origen" in df.columns:
            columnas_finales.append("Origen")

        return pd.DataFrame(columns=columnas_finales)

    df["Válvula"] = df["Válvula"].astype(int)

    # Actualizado: válvulas 1 a 154
    df = df[df["Válvula"].between(1, 154)].copy()

    columnas_finales = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Observaciones",
        "Alerta insumos críticos",
        "Detalle alerta insumo crítico"
    ]

    if "Fecha registro" in df.columns:
        columnas_finales.append("Fecha registro")

    if "Origen" in df.columns:
        df["Origen"] = df["Origen"].fillna("").astype(str).str.strip()
        columnas_finales.append("Origen")

    return df[columnas_finales].copy()


# =====================================================
# GRÁFICOS
# =====================================================
def grafico_tendencia_temporal(df):
    if df.empty:
        return fig_sin_datos()

    df_tmp = df.copy()
    df_tmp["Fecha_dia"] = df_tmp["Fecha"].dt.date

    tend = (
        df_tmp.groupby("Fecha_dia")
        .size()
        .reset_index(name="Registros")
    )

    tend["Fecha_dia"] = pd.to_datetime(tend["Fecha_dia"])
    tend = tend.sort_values("Fecha_dia")
    tend["Fecha_txt"] = tend["Fecha_dia"].dt.strftime("%d-%m-%Y")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=tend["Fecha_txt"],
        y=tend["Registros"],
        name="Registros diarios",
        marker_color="#1e88e5",
        opacity=0.85,
        text=tend["Registros"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Registros: %{y}<extra></extra>"
    ))

    if len(tend) >= 2:
        tend["Media móvil 7 días"] = (
            tend["Registros"]
            .rolling(7, min_periods=1)
            .mean()
        )

        fig.add_trace(go.Scatter(
            x=tend["Fecha_txt"],
            y=tend["Media móvil 7 días"],
            mode="lines+markers",
            name="Media móvil 7 días",
            line=dict(color="#e53935", width=2.5, dash="dot"),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>MA7: %{y:.1f}<extra></extra>"
        ))

    aplicar_estilo_figura(
        fig,
        "Tendencia temporal de registros",
        height=420,
        l=70,
        r=90,
        t=90,
        b=95
    )

    max_y = tend["Registros"].max() if not tend.empty else 1

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Registros",
        showlegend=len(tend) >= 2,
        bargap=0.35,
        margin=dict(l=70, r=90, t=90, b=95)
    )

    fig.update_xaxes(
        type="category",
        tickangle=0 if len(tend) <= 6 else -35
    )

    fig.update_yaxes(
        range=[0, max_y * 1.35 if max_y > 0 else 1],
        dtick=1 if max_y <= 10 else None
    )

    return fig


def grafico_por_turno(df):
    if df.empty:
        return fig_sin_datos()

    vc = df["Turno"].replace("", "SIN TURNO").value_counts().reset_index()
    vc.columns = ["Turno", "Cantidad"]
    vc = vc.sort_values("Turno")

    detalle_operadores = (
        df.assign(Operador=df["Operador"].replace("", "SIN OPERADOR"))
        .assign(Turno=df["Turno"].replace("", "SIN TURNO"))
        .groupby(["Turno", "Operador"])
        .size()
        .reset_index(name="Registros")
        .sort_values(["Turno", "Registros"], ascending=[True, False])
    )

    operadores_por_turno = {}

    for turno in vc["Turno"]:
        subset = detalle_operadores[detalle_operadores["Turno"] == turno]

        if subset.empty:
            operadores_por_turno[turno] = "Sin operadores"
        else:
            operadores_por_turno[turno] = "<br>".join(
                f"• {row['Operador']}: {row['Registros']}"
                for _, row in subset.iterrows()
            )

    vc["Detalle operadores"] = vc["Turno"].map(operadores_por_turno)

    fig = go.Figure(data=[go.Bar(
        x=vc["Turno"],
        y=vc["Cantidad"],
        marker=dict(color="#3498db"),
        text=vc["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        customdata=vc["Detalle operadores"],
        hovertemplate=(
            "<b>Turno %{x}</b><br>"
            "Registros: <b>%{y}</b><br><br>"
            "<b>Operadores:</b><br>%{customdata}"
            "<extra></extra>"
        )
    )])

    aplicar_estilo_figura(fig, "Registros por turno", 380, t=90, b=85)

    fig.update_layout(
        xaxis_title="Turno",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=90)
    )

    max_y = vc["Cantidad"].max() if not vc.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_por_operador(df):
    if df.empty:
        return fig_sin_datos()

    op = (
        df["Operador"]
        .replace("", "SIN OPERADOR")
        .value_counts()
        .head(10)
        .reset_index()
    )

    op.columns = ["Operador", "Cantidad"]
    op = op.sort_values("Cantidad", ascending=False)

    fig = go.Figure(data=[go.Bar(
        x=op["Operador"],
        y=op["Cantidad"],
        marker=dict(color="#2ecc71"),
        text=op["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Registros: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Top operadores", 430, t=90, b=160)

    fig.update_layout(
        xaxis_title="Operador",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=165)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = op["Cantidad"].max() if not op.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_por_mantencion(df):
    if df.empty:
        return fig_sin_datos()

    mt = df["Mantención"].replace("", "SIN MANTENCIÓN").value_counts().reset_index()
    mt.columns = ["Mantención", "Cantidad"]
    mt = mt.sort_values("Cantidad", ascending=False)

    colores = [
        COLORS_REPUESTO.get(m, "#95a5a6")
        for m in mt["Mantención"]
    ]

    fig = go.Figure(data=[go.Bar(
        x=mt["Mantención"],
        y=mt["Cantidad"],
        marker=dict(color=colores),
        text=mt["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Registros: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Tipos de mantención", 440, t=90, b=170)

    fig.update_layout(
        xaxis_title="Tipo de mantención",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=175)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = mt["Cantidad"].max() if not mt.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_alertas_insumos(df):
    if df.empty or "Alerta insumos críticos" not in df.columns:
        return fig_sin_datos()

    alertas = (
        df["Alerta insumos críticos"]
        .fillna("No")
        .replace("", "No")
        .value_counts()
        .reindex(["Sí", "No"], fill_value=0)
        .reset_index()
    )

    alertas.columns = ["Alerta", "Cantidad"]

    colores = ["#f39c12" if a == "Sí" else "#2ecc71" for a in alertas["Alerta"]]

    fig = go.Figure(data=[go.Bar(
        x=alertas["Alerta"],
        y=alertas["Cantidad"],
        marker=dict(color=colores),
        text=alertas["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>Alerta: %{x}</b><br>Registros: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Alertas de insumos críticos", 360, t=90, b=90)

    fig.update_layout(
        xaxis_title="Alerta insumos críticos",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=90)
    )

    max_y = alertas["Cantidad"].max() if not alertas.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25 if max_y > 0 else 1])

    return fig


def grafico_estado_valvulas(df):
    if df.empty or "Válvula" not in df.columns:
        conteos = pd.Series(0, index=VALVULAS_TODAS)
    else:
        conteos = (
            df["Válvula"]
            .value_counts()
            .reindex(VALVULAS_TODAS, fill_value=0)
            .sort_index()
        )

    estado_data = []
    columnas_grid = 16
    total_filas = (len(VALVULAS_TODAS) + columnas_grid - 1) // columnas_grid

    for valvula, cantidad in conteos.items():
        if cantidad == 0:
            estado = "OK"
            color = "#27ae60"
            texto_estado = "Sin registros"
        elif cantidad <= 2:
            estado = "Seguimiento"
            color = "#f39c12"
            texto_estado = "1 a 2 registros"
        else:
            estado = "Crítica"
            color = "#e74c3c"
            texto_estado = "3 o más registros"

        estado_data.append({
            "Válvula": valvula,
            "Mantenciones": cantidad,
            "Estado": estado,
            "Color": color,
            "Texto estado": texto_estado,
            "Fila": (valvula - 1) // columnas_grid,
            "Columna": (valvula - 1) % columnas_grid
        })

    df_estado = pd.DataFrame(estado_data)

    total_ok = int((df_estado["Estado"] == "OK").sum())
    total_seguimiento = int((df_estado["Estado"] == "Seguimiento").sum())
    total_criticas = int((df_estado["Estado"] == "Crítica").sum())

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_estado["Columna"],
        y=df_estado["Fila"],
        mode="markers+text",
        marker=dict(
            size=34,
            color=df_estado["Color"],
            line=dict(
                color="white",
                width=2
            )
        ),
        text=df_estado["Válvula"],
        textfont=dict(
            color="white",
            size=10,
            family="Arial Black"
        ),
        customdata=df_estado[["Mantenciones", "Estado", "Texto estado"]],
        hovertemplate=(
            "<b>Válvula %{text}</b><br>"
            "Estado: <b>%{customdata[1]}</b><br>"
            "Criterio: %{customdata[2]}<br>"
            "Mantenciones: <b>%{customdata[0]}</b>"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title=dict(
            text=(
                "<b>Estado global de válvulas</b><br>"
                f"<span style='font-size:12px'>"
                f"OK: {total_ok} · Seguimiento: {total_seguimiento} · Críticas: {total_criticas}"
                f"</span>"
            ),
            x=0.01,
            font=dict(size=16, color="#1a237e")
        ),
        height=max(560, total_filas * 52 + 130),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=95, b=65),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.98)",
            bordercolor="#1f2937",
            font=dict(color="#111827", size=12)
        )
    )

    fig.update_xaxes(
        visible=False,
        range=[-1, columnas_grid]
    )

    fig.update_yaxes(
        visible=False,
        autorange="reversed",
        range=[total_filas, -1]
    )

    y_leyenda = total_filas + 0.7

    fig.add_annotation(
        x=0,
        y=y_leyenda,
        xref="x",
        yref="y",
        text="🟢 OK = sin registros",
        showarrow=False,
        font=dict(size=12, color="#111827"),
        align="left"
    )

    fig.add_annotation(
        x=5,
        y=y_leyenda,
        xref="x",
        yref="y",
        text="🟠 Seguimiento = 1 a 2 registros",
        showarrow=False,
        font=dict(size=12, color="#111827"),
        align="left"
    )

    fig.add_annotation(
        x=11,
        y=y_leyenda,
        xref="x",
        yref="y",
        text="🔴 Crítica = 3 o más registros",
        showarrow=False,
        font=dict(size=12, color="#111827"),
        align="left"
    )

    return fig


def grafico_valvula_mantencion_burbujas(df):
    if df.empty:
        return fig_sin_datos()

    bubble = (
        df.groupby(["Válvula", "Mantención"])
        .size()
        .reset_index(name="Cantidad")
    )

    fig = go.Figure()

    for tipo in sorted(bubble["Mantención"].unique()):
        subset = bubble[bubble["Mantención"] == tipo]

        fig.add_trace(go.Scatter(
            x=subset["Válvula"],
            y=[tipo] * len(subset),
            mode="markers",
            marker=dict(
                size=subset["Cantidad"] * 4 + 6,
                color=COLORS_REPUESTO.get(tipo, "#95a5a6"),
                opacity=0.75
            ),
            name=tipo,
            hovertemplate=(
                "<b>Válvula %{x}</b><br>"
                f"{tipo}<br>"
                "Registros: %{customdata}<extra></extra>"
            ),
            customdata=subset["Cantidad"]
        ))

    aplicar_estilo_figura(fig, "Distribución válvula × tipo de mantención", 420)

    fig.update_layout(
        xaxis_title="Número de válvula",
        yaxis_title="Tipo de mantención",
        margin=dict(l=70, r=90, t=90, b=85)
    )

    fig.update_xaxes(range=[0, 155])

    return fig


# =====================================================
# CARGA DE DATOS
# =====================================================
try:
    df = cargar_datos()
except Exception as e:
    st.error(f"No se pudieron cargar los datos desde Google Sheets: {e}")
    df = crear_dataframe_vacio()

# =====================================================
# ENCABEZADO CON LOGO CCU
# =====================================================
if LOGO_PATH.exists():
    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 2.4rem;
            margin-bottom: 1.3rem;
        ">
            <img
                src="data:image/png;base64,{logo_base64}"
                style="
                    width: 210px;
                    max-width: 70%;
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

st.markdown(
    """
    <div style='text-align:center; margin-bottom:1.6rem;'>
        <h1 style='margin-top:0;'>
            Área de Operaciones · Línea 11<br>
            Análisis Válvulas Krones
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.markdown("## Filtros")
st.sidebar.success(f"{len(df):,} registros cargados desde Google Sheets")

if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

# -----------------------------------------------------
# Fechas seguras, incluso si no hay datos
# -----------------------------------------------------
fechas_validas = df["Fecha"].dropna() if "Fecha" in df.columns else pd.Series(dtype="datetime64[ns]")

if fechas_validas.empty:
    hoy = datetime.now().date()

    st.sidebar.warning("No hay fechas válidas disponibles.")

    fecha_inicio = st.sidebar.date_input(
        "Desde",
        value=hoy
    )

    fecha_fin = st.sidebar.date_input(
        "Hasta",
        value=hoy
    )
else:
    fecha_min = fechas_validas.min()
    fecha_max = fechas_validas.max()

    fecha_inicio = st.sidebar.date_input(
        "Desde",
        value=fecha_min.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )

    fecha_fin = st.sidebar.date_input(
        "Hasta",
        value=fecha_max.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )

# -----------------------------------------------------
# Opciones seguras para filtros
# -----------------------------------------------------
turnos_opciones = (
    sorted(df["Turno"].dropna().unique())
    if "Turno" in df.columns and not df.empty
    else []
)

operadores_base = (
    df["Operador"].replace("", "SIN OPERADOR")
    if "Operador" in df.columns
    else pd.Series(dtype=str)
)

operadores_opciones = (
    sorted(operadores_base.dropna().unique())
    if not operadores_base.empty
    else []
)

mantencion_opciones = (
    sorted(df["Mantención"].dropna().unique())
    if "Mantención" in df.columns and not df.empty
    else []
)

alerta_opciones = (
    sorted(df["Alerta insumos críticos"].dropna().unique())
    if "Alerta insumos críticos" in df.columns and not df.empty
    else ["No", "Sí"]
)

turnos_sel = st.sidebar.multiselect(
    "Turnos",
    turnos_opciones,
    default=turnos_opciones
)

operadores_sel = st.sidebar.multiselect(
    "Operadores",
    operadores_opciones,
    default=operadores_opciones
)

mantencion_sel = st.sidebar.multiselect(
    "Tipos de mantención",
    mantencion_opciones,
    default=mantencion_opciones
)

alerta_sel = st.sidebar.multiselect(
    "Alerta insumos críticos",
    alerta_opciones,
    default=alerta_opciones
)

valvulas_sel = st.sidebar.multiselect(
    "Válvulas",
    VALVULAS_TODAS,
    default=VALVULAS_TODAS
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Gráficos disponibles")

mostrar_estado_global = st.sidebar.checkbox(
    "Estado global de válvulas",
    value=True
)

mostrar_tendencia = st.sidebar.checkbox(
    "Tendencia temporal",
    value=True
)

mostrar_turno = st.sidebar.checkbox(
    "Registros por turno",
    value=True
)

mostrar_operador = st.sidebar.checkbox(
    "Top operadores",
    value=True
)

mostrar_mantencion = st.sidebar.checkbox(
    "Tipos de mantención",
    value=True
)

mostrar_alertas = st.sidebar.checkbox(
    "Alertas insumos críticos",
    value=True
)

mostrar_burbujas = st.sidebar.checkbox(
    "Distribución válvula × mantención",
    value=True
)

mostrar_datos_detallados = st.sidebar.checkbox(
    "Mostrar datos detallados",
    value=True
)

# =====================================================
# FILTRO DATAFRAME
# =====================================================
if df.empty or fechas_validas.empty:
    df_f = df.copy()
else:
    df_f = df[
        (df["Fecha"].dt.date >= fecha_inicio) &
        (df["Fecha"].dt.date <= fecha_fin) &
        (df["Turno"].isin(turnos_sel)) &
        (operadores_base.isin(operadores_sel)) &
        (df["Mantención"].isin(mantencion_sel)) &
        (df["Alerta insumos críticos"].isin(alerta_sel)) &
        (df["Válvula"].isin(valvulas_sel))
    ].copy()

# =====================================================
# KPIS
# =====================================================
st.markdown("### KPIs generales")

ultimo_fecha, ultimo_operador = obtener_ultimo_registro(df_f)
valvula_critica, intervenciones_criticas = obtener_valvula_mas_critica(df_f)

operador_menos_registros, cantidad_menos_registros = obtener_operador_menos_registros(
    df_f,
    operadores_sel
)

total_registros = f"{len(df_f):,}"
dias_con_registros = df_f["Fecha"].nunique() if "Fecha" in df_f.columns and not df_f.empty else 0
operadores_unicos = (
    df_f["Operador"].replace("", "SIN OPERADOR").nunique()
    if "Operador" in df_f.columns and not df_f.empty
    else 0
)
valvulas_intervenidas = (
    df_f["Válvula"].nunique()
    if "Válvula" in df_f.columns and not df_f.empty
    else 0
)
promedio_registros_dia = len(df_f) / max(dias_con_registros, 1)

alertas_criticas = (
    int((df_f["Alerta insumos críticos"] == "Sí").sum())
    if "Alerta insumos críticos" in df_f.columns and not df_f.empty
    else 0
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    tarjeta_kpi("Total registros", total_registros)

with kpi2:
    tarjeta_kpi("Días con registros", dias_con_registros)

with kpi3:
    tarjeta_kpi("Operadores", operadores_unicos)

with kpi4:
    tarjeta_kpi("Válvulas intervenidas", valvulas_intervenidas)

with kpi5:
    tarjeta_kpi("Registros por día", f"{promedio_registros_dia:.1f}")

kpi6, kpi7, kpi8 = st.columns(3)

with kpi6:
    tarjeta_kpi(
        "Último registro",
        ultimo_fecha,
        f"Operador: {ultimo_operador}"
    )

with kpi7:
    tarjeta_kpi(
        "Válvula más crítica",
        valvula_critica,
        f"{intervenciones_criticas} intervenciones",
        alerta=True
    )

with kpi8:
    tarjeta_kpi(
        "Alertas insumos críticos",
        alertas_criticas,
        "Registros marcados con alerta" if alertas_criticas > 0 else "Sin alertas en el filtro actual",
        alerta=alertas_criticas > 0
    )

kpi9, kpi10 = st.columns(2)

with kpi9:
    valvulas_sin_registro = len(set(valvulas_sel)) - valvulas_intervenidas

    tarjeta_kpi(
        "Válvulas sin registro",
        valvulas_sin_registro,
        "Dentro del rango filtrado"
    )

with kpi10:
    if cantidad_menos_registros == 0:
        tarjeta_kpi(
            "Operador con menos registros",
            operador_menos_registros,
            "No registra intervenciones con los filtros actuales",
            alerta=True
        )
    else:
        tarjeta_kpi(
            "Operador con menos registros",
            operador_menos_registros,
            f"{cantidad_menos_registros} registros"
        )

# Panel de alertas activas
df_alertas = (
    df_f[df_f["Alerta insumos críticos"] == "Sí"].copy()
    if "Alerta insumos críticos" in df_f.columns and not df_f.empty
    else pd.DataFrame()
)

if not df_alertas.empty:
    st.markdown(
        f"""
        <div class="alerta-panel">
            <div class="alerta-panel-title">
                Alertas de insumos críticos activas
            </div>
            <div class="alerta-panel-text">
                Hay {len(df_alertas)} registro(s) con alerta de insumos críticos dentro de los filtros seleccionados.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# =====================================================
# CONTENIDO PRINCIPAL
# =====================================================
if df_f.empty:
    st.warning("Sin datos para los filtros seleccionados.")

    if mostrar_estado_global:
        st.markdown("## Estado global de válvulas")
        st.caption(
            "Vista tipo semáforo: cada círculo representa una válvula. "
            "Verde = sin registros, naranjo = seguimiento, rojo = crítica."
        )

        st.plotly_chart(
            grafico_estado_valvulas(df_f),
            use_container_width=True
        )

else:
    if mostrar_estado_global:
        st.markdown("## Estado global de válvulas")
        st.caption(
            "Vista tipo semáforo: cada círculo representa una válvula. "
            "Verde = sin registros, naranjo = seguimiento, rojo = crítica."
        )

        st.plotly_chart(
            grafico_estado_valvulas(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_tendencia:
        st.markdown("## Tendencia temporal")

        st.plotly_chart(
            grafico_tendencia_temporal(df_f),
            use_container_width=True
        )

        st.markdown("---")

    graficos_generales = [
        mostrar_turno,
        mostrar_operador,
        mostrar_mantencion,
        mostrar_alertas
    ]

    if any(graficos_generales):
        st.markdown("## Análisis general")

        if mostrar_turno:
            st.plotly_chart(
                grafico_por_turno(df_f),
                use_container_width=True
            )

        if mostrar_operador:
            st.plotly_chart(
                grafico_por_operador(df_f),
                use_container_width=True
            )

        if mostrar_mantencion:
            st.plotly_chart(
                grafico_por_mantencion(df_f),
                use_container_width=True
            )

        if mostrar_alertas:
            st.plotly_chart(
                grafico_alertas_insumos(df_f),
                use_container_width=True
            )

        st.markdown("---")

    if mostrar_burbujas:
        st.markdown("## Distribución válvula × tipo de mantención")

        st.plotly_chart(
            grafico_valvula_mantencion_burbujas(df_f),
            use_container_width=True
        )

        st.markdown("---")

# =====================================================
# TABLA DE ALERTAS DE INSUMOS CRÍTICOS
# =====================================================
if not df_alertas.empty:
    st.markdown("## Detalle alertas insumos críticos")

    df_alertas_show = df_alertas.copy()
    df_alertas_show["Fecha"] = df_alertas_show["Fecha"].dt.strftime("%d-%m-%Y")

    columnas_alertas = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Detalle alerta insumo crítico",
        "Observaciones"
    ]

    columnas_alertas = [c for c in columnas_alertas if c in df_alertas_show.columns]

    st.dataframe(
        df_alertas_show[columnas_alertas],
        use_container_width=True,
        height=260
    )

    st.markdown("---")

# =====================================================
# DATOS DETALLADOS
# =====================================================
if mostrar_datos_detallados:
    st.markdown("## Datos detallados")

    if df_f.empty:
        st.info("No hay registros para mostrar.")
    else:
        df_show = df_f.copy()
        df_show["Fecha"] = df_show["Fecha"].dt.strftime("%d-%m-%Y")

        if "Fecha registro" in df_show.columns:
            df_show["Fecha registro"] = pd.to_datetime(
                df_show["Fecha registro"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(
            df_show,
            use_container_width=True,
            height=500
        )

        st.markdown("### Descarga")

        df_dl = df_show.copy()

        st.download_button(
            "Descargar datos filtrados",
            df_dl.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"datos_valvulas_L11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# =====================================================
# FUENTE DE DATOS
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### Fuente de datos")

if "Fecha" in df.columns and not df["Fecha"].dropna().empty:
    fmt_min = df["Fecha"].dropna().min().strftime("%d-%m-%Y")
    fmt_max = df["Fecha"].dropna().max().strftime("%d-%m-%Y")
else:
    fmt_min = "Sin datos"
    fmt_max = "Sin datos"

total_alertas_fuente = (
    int((df["Alerta insumos críticos"] == "Sí").sum())
    if "Alerta insumos críticos" in df.columns and not df.empty
    else 0
)

st.sidebar.info(
    f"Google Sheets\n\n"
    f"- {len(df):,} registros totales\n"
    f"- Alertas insumos críticos: {total_alertas_fuente}\n"
    f"- Período: {fmt_min} → {fmt_max}\n"
    f"- Línea: 11\n"
    f"- Válvulas monitoreadas: 154"
)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align:center; opacity:0.6; font-size:0.8rem;'>
        Dashboard conectado a Google Sheets · Streamlit + Plotly · Línea 11 ·
        Válvulas monitoreadas: 154 ·
        {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)
