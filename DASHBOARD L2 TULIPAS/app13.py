"""
Dashboard de Mantenimiento de Tulipas - Línea 2
Conectado al formulario Streamlit y Google Sheets.
Dashboard Área de Operaciones - Análisis Encajonadora/Desencajonadora.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path
import base64
import re

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Área de Operaciones Línea 2",
    page_icon="🏢",
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

SHEET_ID = "1EjrHHNJXjjBOObeAfIBxQjDfcyCS-o_j4FLaDxOPjRI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

GRID = "rgba(128,128,128,0.15)"
LINE = "rgba(128,128,128,0.30)"

# =====================================================
# ESTILO
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

    div[data-testid="stMetric"] {
        border-radius: 0.5rem;
        padding: 0.5rem;
        border: 1px solid rgba(128,128,128,0.20);
        min-height: 112px;
    }

    div[data-testid="stMetric"] label {
        font-size: 0.88rem;
    }

    div[data-testid="stMetricValue"] {
        white-space: normal;
        overflow-wrap: anywhere;
        font-size: 2rem;
    }

    div[data-testid="stMetricDelta"] {
        white-space: normal;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FUNCIONES BASE
# =====================================================
def aplicar_estilo_figura(fig, title, height=350, l=70, r=60, t=65, b=55):
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


def normalizar_formato(val):
    if pd.isna(val):
        return val

    s = str(val).replace(" ", "").replace(".", "").replace(",", "").upper()
    digits = re.sub(r"[^0-9]", "", s)

    if digits == "2000":
        return "2000 CC"
    elif digits == "2500":
        return "2500 CC"

    return str(val).strip().upper()


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

    ultimo = df_tmp.sort_values("Fecha_orden").iloc[-1]

    fecha = ultimo["Fecha_orden"]
    operador = ultimo["Operador"] if str(ultimo["Operador"]).strip() else "SIN OPERADOR"

    if pd.notna(fecha):
        fecha_txt = fecha.strftime("%d-%m-%Y %H:%M")
    else:
        fecha_txt = "-"

    return fecha_txt, operador


def obtener_tulipa_mas_critica(df):
    if df.empty:
        return "Sin datos", 0

    conteo = (
        df.groupby(["Equipo", "Formato", "Cabezal", "Tulipa"])
        .size()
        .reset_index(name="Intervenciones")
        .sort_values("Intervenciones", ascending=False)
    )

    if conteo.empty:
        return "Sin datos", 0

    top = conteo.iloc[0]

    etiqueta = (
        f"{top['Equipo']} · {top['Formato']} · "
        f"C{int(top['Cabezal'])}-T{int(top['Tulipa'])}"
    )

    return etiqueta, int(top["Intervenciones"])


def calcular_promedio_cambio_goma(df):
    if df.empty:
        return None

    df_tmp = df.copy()

    df_tmp = df_tmp[
        df_tmp["Mantención"]
        .astype(str)
        .str.upper()
        .str.contains("CAMBIO DE GOMA", na=False)
    ].copy()

    if df_tmp.empty:
        return None

    df_tmp = df_tmp.sort_values("Fecha")

    diferencias = []

    for _, grupo in df_tmp.groupby(["Equipo", "Formato", "Cabezal", "Tulipa"]):
        grupo = grupo.sort_values("Fecha").copy()

        if len(grupo) < 2:
            continue

        diffs = grupo["Fecha"].diff().dt.days.dropna()
        diferencias.extend(diffs.tolist())

    if not diferencias:
        return None

    return sum(diferencias) / len(diferencias)


def obtener_operador_menos_registros(df_filtrado, operadores_disponibles):
    if not operadores_disponibles:
        return "Sin operadores", 0

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


def tarjeta_kpi(titulo, valor, detalle=None, alerta=False):
    color_detalle = "#4ade80"
    borde = "rgba(128,128,128,0.22)"
    fondo = "rgba(255,255,255,0.02)"

    if alerta:
        color_detalle = "#facc15"
        borde = "rgba(250,204,21,0.55)"
        fondo = "rgba(250,204,21,0.06)"

    detalle_html = ""

    if detalle:
        detalle_html = f"""
        <div style="
            margin-top: 0.55rem;
            color: {color_detalle};
            font-size: 0.95rem;
            line-height: 1.25;
            white-space: normal;
            word-break: break-word;
        ">
            {detalle}
        </div>
        """

    st.markdown(
        f"""
        <div style="
            border: 1px solid {borde};
            background: {fondo};
            border-radius: 0.55rem;
            padding: 0.85rem 0.9rem;
            min-height: 132px;
            overflow: visible;
            margin-bottom: 1rem;
        ">
            <div style="
                font-size: 0.92rem;
                font-weight: 700;
                margin-bottom: 0.45rem;
                color: inherit;
                white-space: normal;
            ">
                {titulo}
            </div>

            <div style="
                font-size: 1.75rem;
                font-weight: 600;
                line-height: 1.15;
                white-space: normal;
                word-break: break-word;
                overflow-wrap: anywhere;
            ">
                {valor}
            </div>

            {detalle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data(ttl=1)
def cargar_datos():
    df = pd.read_csv(CSV_URL)

    df.columns = [str(c).strip() for c in df.columns]

    columnas_requeridas = [
        "Fecha",
        "Turno",
        "Operador",
        "Equipo",
        "Formato",
        "Cabezal",
        "Tulipa",
        "Mantención",
        "Comentarios"
    ]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en Google Sheets: {faltantes}")

    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

    if "Fecha registro" in df.columns:
        df["Fecha registro"] = pd.to_datetime(df["Fecha registro"], errors="coerce")

    df["Turno"] = df["Turno"].astype(str).str.strip().str.upper()
    df["Operador"] = df["Operador"].fillna("").astype(str).str.strip().str.upper()
    df["Equipo"] = df["Equipo"].astype(str).str.strip()
    df["Formato"] = df["Formato"].apply(normalizar_formato)
    df["Mantención"] = df["Mantención"].fillna("").astype(str).str.strip().str.upper()
    df["Comentarios"] = df["Comentarios"].fillna("").astype(str).str.strip()

    df["Cabezal"] = pd.to_numeric(df["Cabezal"], errors="coerce")
    df["Tulipa"] = pd.to_numeric(df["Tulipa"], errors="coerce")

    df = df.dropna(subset=["Fecha", "Cabezal", "Tulipa"])

    df["Cabezal"] = df["Cabezal"].astype(int)
    df["Tulipa"] = df["Tulipa"].astype(int)

    df = df[
        df["Cabezal"].between(1, 7) &
        df["Tulipa"].between(1, 9)
    ].copy()

    return df


# =====================================================
# GEOMETRÍA
# =====================================================
GEOMETRIA = {
    "2000 CC": {
        "n_cabezales": 7,
        "n_tulipas": 9
    },
    "2500 CC": {
        "n_cabezales": 7,
        "n_tulipas": 6
    }
}

# =====================================================
# GRÁFICOS
# =====================================================
def grafico_tendencia_temporal(df):
    df_tmp = df.copy()
    df_tmp["Fecha_dia"] = df_tmp["Fecha"].dt.date

    tend = (
        df_tmp.groupby("Fecha_dia")
        .size()
        .reset_index(name="Registros")
    )

    tend["Fecha_dia"] = pd.to_datetime(tend["Fecha_dia"])
    tend = tend.sort_values("Fecha_dia")
    tend["Media móvil 7 días"] = tend["Registros"].rolling(7, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tend["Fecha_dia"],
        y=tend["Registros"],
        mode="lines+markers",
        name="Registros diarios",
        line=dict(color="#1e88e5", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(30,136,229,0.10)",
        hovertemplate="<b>%{x|%d-%m-%Y}</b><br>Registros: %{y}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=tend["Fecha_dia"],
        y=tend["Media móvil 7 días"].round(1),
        mode="lines",
        name="Media móvil 7 días",
        line=dict(color="#e53935", width=2, dash="dot"),
        hovertemplate="<b>%{x|%d-%m-%Y}</b><br>MA7: %{y:.1f}<extra></extra>"
    ))

    aplicar_estilo_figura(fig, "Tendencia temporal de registros", 360)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Registros",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def grafico_por_turno(df):
    vc = df["Turno"].value_counts().reset_index()
    vc.columns = ["Turno", "Cantidad"]
    vc = vc.sort_values("Turno")

    fig = go.Figure(data=[go.Bar(
        x=vc["Turno"],
        y=vc["Cantidad"],
        marker=dict(color="#3498db"),
        text=vc["Cantidad"],
        textposition="outside",
        hovertemplate="<b>Turno %{x}</b><br>Registros: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Registros por turno", 320)
    fig.update_layout(
        xaxis_title="Turno",
        yaxis_title="Cantidad",
        showlegend=False
    )

    return fig


def grafico_por_operador(df):
    op = df["Operador"].replace("", "SIN OPERADOR").value_counts().head(10).reset_index()
    op.columns = ["Operador", "Cantidad"]
    op = op.sort_values("Cantidad")

    fig = go.Figure(data=[go.Bar(
        y=op["Operador"],
        x=op["Cantidad"],
        orientation="h",
        marker=dict(color="#2ecc71"),
        text=op["Cantidad"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Registros: %{x}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Top operadores", 320, l=160)
    fig.update_layout(
        xaxis_title="Cantidad",
        showlegend=False
    )

    return fig


def grafico_por_mantencion(df):
    mt = df["Mantención"].replace("", "SIN MANTENCIÓN").value_counts().reset_index()
    mt.columns = ["Mantención", "Cantidad"]
    mt = mt.sort_values("Cantidad")

    fig = go.Figure(data=[go.Bar(
        y=mt["Mantención"],
        x=mt["Cantidad"],
        orientation="h",
        marker=dict(color=mt["Cantidad"], colorscale="Blues", showscale=False),
        text=mt["Cantidad"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Registros: %{x}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Tipos de mantención", 380, l=260)
    fig.update_layout(
        xaxis_title="Cantidad",
        showlegend=False
    )

    return fig


def grafico_equipos_formatos(df):
    dist = (
        df.groupby(["Equipo", "Formato"])
        .size()
        .reset_index(name="Cantidad")
    )

    fig = px.bar(
        dist,
        x="Equipo",
        y="Cantidad",
        color="Formato",
        barmode="group",
        text="Cantidad",
        color_discrete_map={
            "2000 CC": "#3498db",
            "2500 CC": "#e74c3c"
        }
    )

    aplicar_estilo_figura(fig, "Registros por equipo y formato", 340)
    fig.update_layout(
        xaxis_title="Equipo",
        yaxis_title="Cantidad",
        legend_title_text="Formato"
    )

    return fig


def crear_heatmaps_tulipas(df):
    configs = [
        ("Desencajonadora", "2000 CC"),
        ("Encajonadora", "2000 CC"),
        ("Desencajonadora", "2500 CC"),
        ("Encajonadora", "2500 CC"),
    ]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[f"<b>{eq} · {fmt}</b>" for eq, fmt in configs],
        horizontal_spacing=0.10,
        vertical_spacing=0.18,
        column_widths=[0.5, 0.5],
        specs=[
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "heatmap"}]
        ]
    )

    matrices = []
    global_max = 0

    for equipo, formato in configs:
        geo = GEOMETRIA[formato]
        n_cabezales = geo["n_cabezales"]
        n_tulipas = geo["n_tulipas"]

        matriz = np.zeros((n_cabezales, n_tulipas), dtype=int)

        subset = df[
            (df["Equipo"] == equipo) &
            (df["Formato"] == formato)
        ].copy()

        if not subset.empty:
            conteos = subset.groupby(["Cabezal", "Tulipa"]).size()

            for (cab, tul), cnt in conteos.items():
                ci = int(cab) - 1
                ti = int(tul) - 1

                if 0 <= ci < n_cabezales and 0 <= ti < n_tulipas:
                    matriz[ci, ti] = int(cnt)

        global_max = max(global_max, matriz.max())
        matrices.append((matriz, subset, equipo, formato))

    zmax = max(global_max, 1)
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, ((matriz, subset, equipo, formato), (row, col)) in enumerate(zip(matrices, positions)):
        n_cabezales, n_tulipas = matriz.shape

        hover_text = []

        for ci in range(n_cabezales):
            fila_hover = []

            for ti in range(n_tulipas):
                cab_num = ci + 1
                tul_num = ti + 1
                cnt = int(matriz[ci, ti])

                mask = (
                    (subset["Cabezal"] == cab_num) &
                    (subset["Tulipa"] == tul_num)
                )

                mantenciones = (
                    subset.loc[mask, "Mantención"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                comentarios = (
                    subset.loc[mask, "Comentarios"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                mant_block = ""
                if mantenciones:
                    mant_block = "<br><b>Mantenciones:</b><br>" + "<br>".join(
                        f"• {m}" for m in mantenciones[:5]
                    )

                comentarios_validos = [c for c in comentarios if c.strip()]
                com_block = ""
                if comentarios_validos:
                    com_block = "<br><b>Comentarios:</b><br>" + "<br>".join(
                        f"• {c}" for c in comentarios_validos[:3]
                    )

                fila_hover.append(
                    f"<b>{equipo} · {formato}</b><br>"
                    f"Cabezal: <b>{cab_num}</b><br>"
                    f"Tulipa: <b>{tul_num}</b><br>"
                    f"Registros: <b>{cnt}</b>"
                    f"{mant_block}{com_block}"
                )

            hover_text.append(fila_hover)

        text_display = matriz.astype(str)
        text_display[matriz == 0] = ""

        fig.add_trace(
            go.Heatmap(
                z=matriz,
                x=[f"T{i}" for i in range(1, n_tulipas + 1)],
                y=[f"C{i}" for i in range(1, n_cabezales + 1)],
                zmin=0,
                zmax=zmax,
                colorscale="YlOrRd",
                colorbar=dict(
                    title="Registros",
                    x=1.02,
                    y=0.5,
                    len=0.75
                ) if idx == 1 else None,
                showscale=(idx == 1),
                text=text_display,
                texttemplate="%{text}",
                customdata=hover_text,
                hovertemplate="%{customdata}<extra></extra>"
            ),
            row=row,
            col=col
        )

        fig.update_xaxes(
            title_text="Tulipa",
            row=row,
            col=col,
            constrain="domain"
        )

        fig.update_yaxes(
            title_text="Cabezal",
            autorange="reversed",
            row=row,
            col=col,
            scaleanchor=None
        )

    fig.update_layout(
        height=780,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=35, r=85, t=70, b=45),
        font=dict(family="Arial, sans-serif", size=11)
    )

    return fig


def grafico_top_tulipas(df, top_n=15):
    top = (
        df.groupby(["Equipo", "Formato", "Cabezal", "Tulipa"])
        .size()
        .reset_index(name="Frecuencia")
        .sort_values("Frecuencia", ascending=False)
        .head(top_n)
    )

    top["Etiqueta"] = (
        top["Equipo"].astype(str).str[:4] + " " +
        top["Formato"].astype(str) +
        " | C" + top["Cabezal"].astype(str) +
        "-T" + top["Tulipa"].astype(str)
    )

    fig = go.Figure(go.Bar(
        x=top["Frecuencia"],
        y=top["Etiqueta"],
        orientation="h",
        marker=dict(color=top["Frecuencia"], colorscale="YlOrRd", showscale=False),
        text=top["Frecuencia"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>"
    ))

    aplicar_estilo_figura(fig, f"Top {top_n} tulipas más intervenidas", 480, l=190)
    fig.update_layout(
        xaxis_title="Registros",
        yaxis=dict(categoryorder="total ascending")
    )

    return fig


# =====================================================
# CARGA
# =====================================================
try:
    df = cargar_datos()
except Exception as e:
    st.error(f"No se pudieron cargar los datos desde Google Sheets: {e}")
    st.stop()

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
            Área de Operaciones · Línea 2<br>
            Análisis Encajonadora / Desencajonadora
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

fecha_min = df["Fecha"].min()
fecha_max = df["Fecha"].max()

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

equipos_sel = st.sidebar.multiselect(
    "Equipos",
    sorted(df["Equipo"].dropna().unique()),
    default=sorted(df["Equipo"].dropna().unique())
)

formatos_sel = st.sidebar.multiselect(
    "Formatos",
    sorted(df["Formato"].dropna().unique()),
    default=sorted(df["Formato"].dropna().unique())
)

turnos_sel = st.sidebar.multiselect(
    "Turnos",
    sorted(df["Turno"].dropna().unique()),
    default=sorted(df["Turno"].dropna().unique())
)

operadores_base = df["Operador"].replace("", "SIN OPERADOR")

operadores_sel = st.sidebar.multiselect(
    "Operadores",
    sorted(operadores_base.dropna().unique()),
    default=sorted(operadores_base.dropna().unique())
)

mantenciones_sel = st.sidebar.multiselect(
    "Tipos de mantención",
    sorted(df["Mantención"].dropna().unique()),
    default=sorted(df["Mantención"].dropna().unique())
)

cabezales_sel = st.sidebar.multiselect(
    "Cabezales",
    list(range(1, 8)),
    default=list(range(1, 8))
)

tulipas_sel = st.sidebar.multiselect(
    "Tulipas",
    list(range(1, 10)),
    default=list(range(1, 10))
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Gráficos disponibles")

mostrar_grafico_ubicacion = st.sidebar.checkbox(
    "Análisis por ubicación física",
    value=True
)

mostrar_grafico_top_tulipas = st.sidebar.checkbox(
    "Top tulipas más intervenidas",
    value=True
)

mostrar_grafico_tendencia = st.sidebar.checkbox(
    "Tendencia temporal",
    value=True
)

mostrar_grafico_turno = st.sidebar.checkbox(
    "Registros por turno",
    value=True
)

mostrar_grafico_operador = st.sidebar.checkbox(
    "Top operadores",
    value=True
)

mostrar_grafico_equipo_formato = st.sidebar.checkbox(
    "Registros por equipo y formato",
    value=True
)

mostrar_grafico_mantencion = st.sidebar.checkbox(
    "Tipos de mantención",
    value=True
)

mostrar_datos_detallados = st.sidebar.checkbox(
    "Mostrar datos detallados",
    value=True
)

# =====================================================
# FILTRO
# =====================================================
df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["Equipo"].isin(equipos_sel)) &
    (df["Formato"].isin(formatos_sel)) &
    (df["Turno"].isin(turnos_sel)) &
    (operadores_base.isin(operadores_sel)) &
    (df["Mantención"].isin(mantenciones_sel)) &
    (df["Cabezal"].isin(cabezales_sel)) &
    (df["Tulipa"].isin(tulipas_sel))
].copy()

# =====================================================
# KPIS
# =====================================================
st.markdown("### KPIs generales")

ultimo_fecha, ultimo_operador = obtener_ultimo_registro(df_f)
tulipa_critica, intervenciones_criticas = obtener_tulipa_mas_critica(df_f)
promedio_goma = calcular_promedio_cambio_goma(df_f)

operador_menos_registros, cantidad_menos_registros = obtener_operador_menos_registros(
    df_f,
    operadores_sel
)

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Total registros", f"{len(df_f):,}")

with m2:
    st.metric("Días con registros", df_f["Fecha"].nunique())

with m3:
    st.metric("Operadores", df_f["Operador"].replace("", "SIN OPERADOR").nunique())

with m4:
    st.metric(
        "Tulipas intervenidas",
        df_f[["Equipo", "Formato", "Cabezal", "Tulipa"]].drop_duplicates().shape[0]
    )

with m5:
    promedio = len(df_f) / max(df_f["Fecha"].nunique(), 1)
    st.metric("Registros por día", f"{promedio:.1f}")

k1, k2 = st.columns(2)

with k1:
    tarjeta_kpi(
        "Último registro",
        ultimo_fecha,
        f"Operador: {ultimo_operador}"
    )

with k2:
    tarjeta_kpi(
        "Tulipa más crítica",
        tulipa_critica,
        f"{intervenciones_criticas} intervenciones",
        alerta=True
    )

k3, k4 = st.columns(2)

with k3:
    if promedio_goma is None:
        tarjeta_kpi(
            "Cambio promedio de goma",
            "Sin historial",
            "Se requieren registros repetidos por tulipa"
        )
    else:
        tarjeta_kpi(
            "Cambio promedio de goma",
            f"{promedio_goma:.1f} días",
            "Promedio por tulipa con registros repetidos"
        )

with k4:
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

st.markdown("---")

# =====================================================
# CONTENIDO PRINCIPAL
# =====================================================
if df_f.empty:
    st.warning("Sin datos para los filtros seleccionados.")

else:
    if mostrar_grafico_ubicacion:
        st.markdown("## Análisis específico por ubicación física")
        st.caption(
            "Cada celda representa la frecuencia de intervenciones para una combinación Cabezal × Tulipa."
        )

        st.plotly_chart(
            crear_heatmaps_tulipas(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_grafico_top_tulipas:
        st.plotly_chart(
            grafico_top_tulipas(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_grafico_tendencia:
        st.markdown("## Análisis temporal")

        st.plotly_chart(
            grafico_tendencia_temporal(df_f),
            use_container_width=True
        )

        st.markdown("---")

    graficos_generales = [
        mostrar_grafico_turno,
        mostrar_grafico_operador,
        mostrar_grafico_equipo_formato
    ]

    if any(graficos_generales):
        st.markdown("## Análisis general")

        columnas = st.columns(3)

        if mostrar_grafico_turno:
            with columnas[0]:
                st.plotly_chart(grafico_por_turno(df_f), use_container_width=True)

        if mostrar_grafico_operador:
            with columnas[1]:
                st.plotly_chart(grafico_por_operador(df_f), use_container_width=True)

        if mostrar_grafico_equipo_formato:
            with columnas[2]:
                st.plotly_chart(grafico_equipos_formatos(df_f), use_container_width=True)

        st.markdown("---")

    if mostrar_grafico_mantencion:
        st.markdown("## Análisis de mantenciones")

        st.plotly_chart(
            grafico_por_mantencion(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_datos_detallados:
        st.markdown("## Datos detallados")

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

        st.download_button(
            "Descargar datos filtrados",
            df_show.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"datos_tulipas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# =====================================================
# FUENTE DE DATOS
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### Fuente de datos")

fmt_min = df["Fecha"].min().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].min()) else "N/A"
fmt_max = df["Fecha"].max().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].max()) else "N/A"

st.sidebar.info(
    f"Google Sheets\n\n"
    f"- {len(df):,} registros totales\n"
    f"- Período: {fmt_min} → {fmt_max}"
)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align:center; opacity:0.6; font-size:0.8rem;'>
        Dashboard conectado a Google Sheets · Streamlit + Plotly · 
        {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)
