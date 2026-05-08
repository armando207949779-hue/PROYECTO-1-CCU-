"""
Dashboard de Mantenimiento de Tulipas - Embotelladora CCU
Streamlit App para GitHub + Streamlit Cloud
Conectado a Google Sheets
LÍNEA 11
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

# ============================================================================
# CONFIG STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Dashboard Tulipas CCU Línea 11",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# RUTAS DEL PROYECTO / LOGO
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

LOGO_CANDIDATES = [
    BASE_DIR / "assets" / "CCU_logo_(2018).svg.png",
    BASE_DIR.parent / "assets" / "CCU_logo_(2018).svg.png",
]

LOGO_PATH = next(
    (path for path in LOGO_CANDIDATES if path.exists()),
    LOGO_CANDIDATES[0]
)

# ============================================================================
# ESTILOS CSS
# ============================================================================

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
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================================
# PARÁMETROS GENERALES
# ============================================================================

SHEET_ID = "1PmDo4EjBxXZx0fPMGPMJKzBztyAq8AipxqCsJTFI0e0"

FORMATOS_ORDEN = ["237 CC", "350 CC", "1.000 CC", "1.250 CC"]
EQUIPOS_ORDEN = ["Desencajonadora", "Encajonadora"]

GEOMETRIA = {
    "237 CC": {"n_cabezales": 6, "total_tulipas": 30},
    "350 CC": {"n_cabezales": 7, "total_tulipas": 30},
    "1.000 CC": {"n_cabezales": 9, "total_tulipas": 30},
    "1.250 CC": {"n_cabezales": 9, "total_tulipas": 30},
}

GRID = "rgba(128,128,128,0.15)"
LINE = "rgba(128,128,128,0.30)"

# ============================================================================
# FUNCIONES BASE
# ============================================================================

def normalizar_formato(val):
    if pd.isna(val):
        return val

    s = str(val).replace(" ", "").replace(".", "").replace(",", "").upper()
    digits = re.sub(r"[^0-9]", "", s)

    if digits == "237":
        return "237 CC"
    elif digits == "350":
        return "350 CC"
    elif digits == "1000":
        return "1.000 CC"
    elif digits == "1250":
        return "1.250 CC"

    return str(val).strip()


def limpiar_texto_serie(serie, vacio="Sin dato"):
    return (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .replace({"": vacio, "nan": vacio, "None": vacio, "NaN": vacio})
    )


def aplicar_estilo_figura(fig, title, height=350, l=70, r=70, t=80, b=70):
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

    ultimo = df_tmp.sort_values("Fecha_orden").iloc[-1]

    fecha = ultimo["Fecha_orden"]
    operador = ultimo["Operador"] if str(ultimo["Operador"]).strip() else "SIN OPERADOR"

    fecha_txt = fecha.strftime("%d-%m-%Y %H:%M") if pd.notna(fecha) else "-"

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


# ============================================================================
# CARGA DE DATOS
# ============================================================================

@st.cache_data(ttl=1)
def load_data_from_sheets():
    urls = [
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv",
    ]

    last_error = None

    for csv_url in urls:
        try:
            df = pd.read_csv(csv_url)
            df.columns = [str(c).strip() for c in df.columns]

            columnas_base = [
                "Fecha", "Turno", "Operador", "Equipo", "Formato",
                "Cabezal", "Tulipa", "Mantención", "Comentarios"
            ]

            faltantes = [c for c in columnas_base if c not in df.columns]

            if faltantes:
                raise ValueError(f"Faltan columnas requeridas: {faltantes}")

            if "Fecha registro" in df.columns:
                df["Fecha registro"] = pd.to_datetime(
                    df["Fecha registro"],
                    errors="coerce"
                )

            df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

            if "Fecha registro" in df.columns:
                df["Fecha"] = df["Fecha"].fillna(df["Fecha registro"])

            df["Equipo"] = limpiar_texto_serie(df["Equipo"], "Sin equipo")
            df["Formato"] = df["Formato"].apply(normalizar_formato)
            df["Turno"] = limpiar_texto_serie(df["Turno"], "Sin turno").str.upper()
            df["Operador"] = limpiar_texto_serie(df["Operador"], "Sin operador").str.upper()
            df["Mantención"] = limpiar_texto_serie(df["Mantención"], "Sin mantención").str.upper()
            df["Comentarios"] = limpiar_texto_serie(df["Comentarios"], "")

            df["Cabezal"] = pd.to_numeric(df["Cabezal"], errors="coerce")
            df["Tulipa"] = pd.to_numeric(df["Tulipa"], errors="coerce")

            df = df.dropna(subset=["Fecha", "Cabezal", "Tulipa"]).copy()

            df["Cabezal"] = df["Cabezal"].astype(int)
            df["Tulipa"] = df["Tulipa"].astype(int)

            df = df[
                df["Formato"].isin(FORMATOS_ORDEN) &
                df["Cabezal"].between(1, 9) &
                df["Tulipa"].between(1, 30)
            ].copy()

            df = df.sort_values(
                ["Fecha", "Equipo", "Formato", "Cabezal", "Tulipa"]
            ).reset_index(drop=True)

            return df, None

        except Exception as e:
            last_error = e

    return None, last_error


@st.cache_data
def load_data_example():
    np.random.seed(42)
    fechas = pd.date_range("2026-01-01", "2026-04-17", freq="D")
    n = 1200

    data = {
        "Fecha": np.random.choice(fechas, n),
        "Turno": np.random.choice(["A", "B", "C"], n),
        "Operador": np.random.choice(["JORGE MUÑOZ", "LUIS SOTO", "ISMAEL BRIONES"], n),
        "Equipo": np.random.choice(["Encajonadora", "Desencajonadora"], n),
        "Formato": np.random.choice(FORMATOS_ORDEN, n),
        "Cabezal": np.random.choice(range(1, 10), n),
        "Tulipa": np.random.choice(range(1, 31), n),
        "Mantención": np.random.choice([
            "CAMBIO DE GOMA TULIPA",
            "CAMBIO CUERPO TULIPA PLÁSTICA",
            "CAMBIO DE RESORTE",
            "CAMBIO DE VÁSTAGO",
            "CAMBIO DE SEGURO DE VÁSTAGO",
            "CAMBIO DE CONECTOR NEUMÁTICO",
            "OTRO"
        ], n),
        "Comentarios": np.random.choice(["", "SIN NOVEDAD", "REVISAR", "URGENTE"], n),
    }

    df = pd.DataFrame(data)
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    return df


# ============================================================================
# FIGURA SIN DATOS
# ============================================================================

def fig_sin_datos():
    fig = go.Figure()
    fig.add_annotation(text="Sin datos", showarrow=False)
    fig.update_layout(
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ============================================================================
# HEATMAPS
# ============================================================================

def crear_heatmaps(df_filtrado):
    configs = [(fmt, eq) for fmt in FORMATOS_ORDEN for eq in EQUIPOS_ORDEN]
    subtitles = [f"<b>{eq} · {fmt}</b>" for fmt, eq in configs]

    fig = make_subplots(
        rows=4,
        cols=2,
        subplot_titles=subtitles,
        horizontal_spacing=0.10,
        vertical_spacing=0.15,
        column_widths=[0.5, 0.5],
        specs=[
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "heatmap"}],
            [{"type": "heatmap"}, {"type": "heatmap"}],
        ]
    )

    global_max = 0
    matrices_all = []

    for fmt, eq in configs:
        geo = GEOMETRIA[fmt]
        n_cabezales = geo["n_cabezales"]
        n_tulipas = geo["total_tulipas"]

        matriz = np.zeros((n_cabezales, n_tulipas), dtype=int)

        subset = df_filtrado[
            (df_filtrado["Equipo"] == eq) &
            (df_filtrado["Formato"] == fmt)
        ].copy()

        if not subset.empty:
            conteos = subset.groupby(["Cabezal", "Tulipa"]).size()

            for (cab, tul), cnt in conteos.items():
                ci = int(cab) - 1
                ti = int(tul) - 1

                if 0 <= ci < n_cabezales and 0 <= ti < n_tulipas:
                    matriz[ci, ti] = int(cnt)

        global_max = max(global_max, int(matriz.max()) if matriz.size else 0)
        matrices_all.append((matriz, fmt, eq, subset))

    positions = [
        (1, 1), (1, 2),
        (2, 1), (2, 2),
        (3, 1), (3, 2),
        (4, 1), (4, 2),
    ]

    zmax = max(global_max, 1)

    for idx, ((matriz, fmt, eq, subset), (row, col)) in enumerate(zip(matrices_all, positions)):
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

                mant_list = (
                    subset.loc[mask, "Mantención"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                comentarios_list = (
                    subset.loc[mask, "Comentarios"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                mant_block = ""

                if mant_list:
                    mant_str = "<br>".join(f"• {m}" for m in mant_list[:5])

                    if len(mant_list) > 5:
                        mant_str += f"<br><i>…y {len(mant_list) - 5} más</i>"

                    mant_block = f"<br><b>Mantención:</b><br>{mant_str}"

                comentarios_validos = [c for c in comentarios_list if str(c).strip()]
                comentarios_block = ""

                if comentarios_validos:
                    com_str = "<br>".join(f"• {c}" for c in comentarios_validos[:3])

                    if len(comentarios_validos) > 3:
                        com_str += f"<br><i>…y {len(comentarios_validos) - 3} más</i>"

                    comentarios_block = f"<br><b>Comentarios:</b><br>{com_str}"

                fila_hover.append(
                    f"<b>{eq} · {fmt}</b><br>"
                    f"Cabezal: <b>{cab_num}</b><br>"
                    f"Tulipa: <b>{tul_num}</b><br>"
                    f"Registros: <b>{cnt}</b>"
                    f"{mant_block}{comentarios_block}"
                )

            hover_text.append(fila_hover)

        text_display = matriz.astype(str)
        text_display[matriz == 0] = ""

        show_colorbar = idx == 1

        fig.add_trace(
            go.Heatmap(
                z=matriz,
                x=[f"T{i + 1}" for i in range(n_tulipas)],
                y=[f"C{i + 1}" for i in range(n_cabezales)],
                zmin=0,
                zmax=zmax,
                colorscale=[
                    [0.0, "#f7fbff"],
                    [0.15, "#c6dbef"],
                    [0.35, "#fdae6b"],
                    [0.6, "#f16913"],
                    [0.8, "#d94801"],
                    [1.0, "#7f2704"],
                ],
                showscale=show_colorbar,
                colorbar=dict(
                    title=dict(text="Registros", font=dict(size=10)),
                    thickness=12,
                    len=0.25,
                    y=0.88,
                    x=1.02,
                    tickfont=dict(size=9),
                ) if show_colorbar else None,
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_text,
                text=text_display,
                texttemplate="%{text}",
                textfont=dict(size=8),
                name=""
            ),
            row=row,
            col=col
        )

        fig.update_xaxes(
            title_text="Tulipa",
            tickfont=dict(size=7),
            row=row,
            col=col,
            constrain="domain"
        )

        fig.update_yaxes(
            title_text="Cabezal",
            tickfont=dict(size=8),
            autorange="reversed",
            row=row,
            col=col,
            scaleanchor=None
        )

    fig.update_layout(
        height=1450,
        showlegend=False,
        font=dict(family="Arial, sans-serif", size=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=90, t=80, b=50),
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(size=11))

    return fig


# ============================================================================
# GRÁFICOS
# ============================================================================

def grafico_tendencia(df):
    if len(df) == 0:
        return fig_sin_datos()

    tend = (
        df.groupby(df["Fecha"].dt.date)
        .size()
        .reset_index(name="Registros")
    )

    tend.columns = ["Fecha", "Registros"]
    tend["Fecha"] = pd.to_datetime(tend["Fecha"])
    tend = tend.sort_values("Fecha")
    tend["Fecha_txt"] = tend["Fecha"].dt.strftime("%d-%m-%Y")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=tend["Fecha_txt"],
        y=tend["Registros"],
        name="Registros diarios",
        marker_color="#4a90d9",
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
            name="Media móvil 7 días",
            mode="lines+markers",
            line=dict(color="#e74c3c", width=2.5, dash="dot"),
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

    fig.update_yaxes(
        range=[0, max_y * 1.35 if max_y > 0 else 1],
        dtick=1 if max_y <= 10 else None
    )

    fig.update_xaxes(
        type="category",
        tickangle=0 if len(tend) <= 6 else -35
    )

    return fig


def grafico_formatos(df):
    if len(df) == 0:
        return fig_sin_datos()

    dist = df.groupby(["Equipo", "Formato"]).size().reset_index(name="Cantidad")

    fig = px.bar(
        dist,
        x="Equipo",
        y="Cantidad",
        color="Formato",
        barmode="group",
        text="Cantidad",
        title="<b>Registros por equipo y formato</b>",
        height=420,
        labels={"Cantidad": "Registros"},
        category_orders={"Formato": FORMATOS_ORDEN},
        color_discrete_map={
            "237 CC": "#3498db",
            "350 CC": "#2ecc71",
            "1.000 CC": "#f39c12",
            "1.250 CC": "#e74c3c",
        }
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Formato: %{fullData.name}<br>"
            "Registros: %{y}<extra></extra>"
        )
    )

    aplicar_estilo_figura(fig, "Registros por equipo y formato", 420, t=90, b=95)

    fig.update_layout(
        xaxis_title="Equipo",
        yaxis_title="Registros",
        legend_title_text="Formato",
        margin=dict(l=70, r=90, t=90, b=100)
    )

    max_y = dist["Cantidad"].max() if not dist.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_turno(df):
    if len(df) == 0:
        return fig_sin_datos()

    dist = df["Turno"].value_counts().reset_index()
    dist.columns = ["Turno", "Cantidad"]
    dist = dist.sort_values("Turno")

    detalle_operadores = (
        df.assign(Operador=df["Operador"].replace("", "SIN OPERADOR"))
        .groupby(["Turno", "Operador"])
        .size()
        .reset_index(name="Registros")
        .sort_values(["Turno", "Registros"], ascending=[True, False])
    )

    operadores_por_turno = {}

    for turno in dist["Turno"]:
        subset = detalle_operadores[detalle_operadores["Turno"] == turno]

        if subset.empty:
            operadores_por_turno[turno] = "Sin operadores"
        else:
            operadores_por_turno[turno] = "<br>".join(
                f"• {row['Operador']}: {row['Registros']}"
                for _, row in subset.iterrows()
            )

    dist["Detalle operadores"] = dist["Turno"].map(operadores_por_turno)

    colores = {
        "A": "#3498db",
        "B": "#2ecc71",
        "C": "#e74c3c",
        "SIN TURNO": "#95a5a6",
        "Sin turno": "#95a5a6"
    }

    fig = go.Figure(go.Bar(
        x=dist["Turno"],
        y=dist["Cantidad"],
        marker=dict(color=[colores.get(t, "#95a5a6") for t in dist["Turno"]]),
        text=dist["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        customdata=dist["Detalle operadores"],
        hovertemplate=(
            "<b>Turno %{x}</b><br>"
            "Registros: <b>%{y}</b><br><br>"
            "<b>Operadores:</b><br>%{customdata}"
            "<extra></extra>"
        )
    ))

    aplicar_estilo_figura(fig, "Registros por turno", 380, t=90, b=80)

    fig.update_layout(
        xaxis_title="Turno",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=85)
    )

    max_y = dist["Cantidad"].max() if not dist.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_mantencion(df):
    if len(df) == 0:
        return fig_sin_datos()

    mant = df["Mantención"].value_counts().head(12).reset_index()
    mant.columns = ["Mantención", "Cantidad"]
    mant = mant.sort_values("Cantidad", ascending=False)

    fig = go.Figure(go.Bar(
        x=mant["Mantención"],
        y=mant["Cantidad"],
        marker=dict(color=mant["Cantidad"], colorscale="Viridis", showscale=False),
        text=mant["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>%{y} registros<extra></extra>"
    ))

    aplicar_estilo_figura(fig, "Tipos de mantención más frecuentes", 460, t=90, b=170)

    fig.update_layout(
        xaxis_title="Tipo de mantención",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=175)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = mant["Cantidad"].max() if not mant.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_operador(df):
    if len(df) == 0:
        return fig_sin_datos()

    dist = df["Operador"].value_counts().reset_index()
    dist.columns = ["Operador", "Cantidad"]
    dist = dist.sort_values("Cantidad", ascending=False)

    fig = go.Figure(go.Bar(
        x=dist["Operador"],
        y=dist["Cantidad"],
        marker=dict(color=dist["Cantidad"], colorscale="Blues", showscale=False),
        text=dist["Cantidad"],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>%{y} registros<extra></extra>"
    ))

    aplicar_estilo_figura(fig, "Registros por operador", 440, t=90, b=155)

    fig.update_layout(
        xaxis_title="Operador",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=160)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = dist["Cantidad"].max() if not dist.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_top_tulipas(df, top_n=15):
    if len(df) == 0:
        return fig_sin_datos()

    top = (
        df.groupby(["Equipo", "Formato", "Cabezal", "Tulipa"])
        .size()
        .reset_index(name="Frecuencia")
        .sort_values("Frecuencia", ascending=False)
        .head(top_n)
    )

    top["Etiqueta"] = (
        top["Equipo"].astype(str).str[:4] + " " +
        top["Formato"].astype(str) + " | C" +
        top["Cabezal"].astype(str) + "-T" +
        top["Tulipa"].astype(str)
    )

    top["Detalle"] = (
        top["Equipo"].astype(str) +
        " · " +
        top["Formato"].astype(str) +
        "<br>Cabezal: " +
        top["Cabezal"].astype(str) +
        "<br>Tulipa: " +
        top["Tulipa"].astype(str)
    )

    fig = go.Figure(go.Bar(
        x=top["Etiqueta"],
        y=top["Frecuencia"],
        marker=dict(color=top["Frecuencia"], colorscale="YlOrRd", showscale=False),
        text=top["Frecuencia"],
        textposition="outside",
        cliponaxis=False,
        customdata=top["Detalle"],
        hovertemplate=(
            "<b>%{customdata}</b><br>"
            "Frecuencia: <b>%{y}</b><extra></extra>"
        )
    ))

    aplicar_estilo_figura(fig, f"Top {top_n} tulipas más afectadas", 540, t=90, b=180)

    fig.update_layout(
        xaxis_title="Tulipa",
        yaxis_title="Registros",
        showlegend=False,
        margin=dict(l=70, r=90, t=90, b=185)
    )

    fig.update_xaxes(tickangle=-45)

    max_y = top["Frecuencia"].max() if not top.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


# ============================================================================
# INTERFAZ
# ============================================================================

df, error_carga = load_data_from_sheets()

if df is None:
    st.error(f"No se pudo cargar Google Sheets: {error_carga}")
    st.info("Se usarán datos de ejemplo para que el dashboard siga funcionando.")
    df = load_data_example()

# ============================================================================
# ENCABEZADO CON LOGO
# ============================================================================

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
            Análisis Encajonadora / Desencajonadora
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================================
# FILTROS
# ============================================================================

st.sidebar.markdown("## Filtros")
st.sidebar.success(f"{len(df):,} registros cargados desde Google Sheets")

if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

fecha_min = df["Fecha"].min()
fecha_max = df["Fecha"].max()

col_f1, col_f2 = st.sidebar.columns(2)

with col_f1:
    fecha_inicio = st.date_input(
        "Desde",
        value=fecha_min.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )

with col_f2:
    fecha_fin = st.date_input(
        "Hasta",
        value=fecha_max.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )

equipos_opciones = sorted(df["Equipo"].dropna().unique())
equipos_sel = st.sidebar.multiselect(
    "Equipos",
    equipos_opciones,
    default=equipos_opciones
)

formatos_opciones = [f for f in FORMATOS_ORDEN if f in df["Formato"].dropna().unique()]
formatos_sel = st.sidebar.multiselect(
    "Formatos",
    formatos_opciones,
    default=formatos_opciones
)

turnos_opciones = sorted(df["Turno"].dropna().unique())
turnos_sel = st.sidebar.multiselect(
    "Turnos",
    turnos_opciones,
    default=turnos_opciones
)

operadores_opciones = sorted(df["Operador"].dropna().unique())
operadores_sel = st.sidebar.multiselect(
    "Operadores",
    operadores_opciones,
    default=operadores_opciones
)

mantenciones_opciones = sorted(df["Mantención"].dropna().unique())
mantenciones_sel = st.sidebar.multiselect(
    "Tipos de mantención",
    mantenciones_opciones,
    default=mantenciones_opciones
)

cabezales_sel = st.sidebar.multiselect(
    "Cabezales",
    list(range(1, 10)),
    default=list(range(1, 10))
)

tulipas_sel = st.sidebar.multiselect(
    "Tulipas",
    list(range(1, 31)),
    default=list(range(1, 31))
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Gráficos disponibles")

mostrar_heatmap = st.sidebar.checkbox(
    "Análisis por ubicación física",
    value=True
)

mostrar_top_tulipas = st.sidebar.checkbox(
    "Top tulipas más afectadas",
    value=True
)

mostrar_tendencia = st.sidebar.checkbox(
    "Tendencia temporal",
    value=True
)

mostrar_formatos = st.sidebar.checkbox(
    "Registros por equipo y formato",
    value=True
)

mostrar_turno = st.sidebar.checkbox(
    "Registros por turno",
    value=True
)

mostrar_mantencion = st.sidebar.checkbox(
    "Tipos de mantención",
    value=True
)

mostrar_operador = st.sidebar.checkbox(
    "Registros por operador",
    value=True
)

mostrar_datos_detallados = st.sidebar.checkbox(
    "Mostrar datos detallados",
    value=True
)

# ============================================================================
# FILTRO DATAFRAME
# ============================================================================

df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["Equipo"].isin(equipos_sel)) &
    (df["Formato"].isin(formatos_sel)) &
    (df["Turno"].isin(turnos_sel)) &
    (df["Operador"].isin(operadores_sel)) &
    (df["Mantención"].isin(mantenciones_sel)) &
    (df["Cabezal"].isin(cabezales_sel)) &
    (df["Tulipa"].isin(tulipas_sel))
].copy()

# ============================================================================
# KPIS
# ============================================================================

st.markdown("### KPIs generales")

ultimo_fecha, ultimo_operador = obtener_ultimo_registro(df_f)
tulipa_critica, intervenciones_criticas = obtener_tulipa_mas_critica(df_f)
promedio_goma = calcular_promedio_cambio_goma(df_f)

operador_menos_registros, cantidad_menos_registros = obtener_operador_menos_registros(
    df_f,
    operadores_sel
)

total_registros = f"{len(df_f):,}"
dias_activos = df_f["Fecha"].nunique()
operadores_unicos = df_f["Operador"].nunique()
equipos_unicos = df_f["Equipo"].nunique()
promedio_registros_dia = len(df_f) / max(df_f["Fecha"].nunique(), 1)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    tarjeta_kpi("Total registros", total_registros)

with k2:
    tarjeta_kpi("Días activos", dias_activos)

with k3:
    tarjeta_kpi("Operadores", operadores_unicos)

with k4:
    tarjeta_kpi("Equipos", equipos_unicos)

with k5:
    tarjeta_kpi("Registros por día", f"{promedio_registros_dia:.1f}")

k6, k7 = st.columns(2)

with k6:
    tarjeta_kpi(
        "Último registro",
        ultimo_fecha,
        f"Operador: {ultimo_operador}"
    )

with k7:
    tarjeta_kpi(
        "Tulipa más crítica",
        tulipa_critica,
        f"{intervenciones_criticas} intervenciones",
        alerta=True
    )

k8, k9 = st.columns(2)

with k8:
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

with k9:
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

# ============================================================================
# GRÁFICOS
# ============================================================================

if len(df_f) == 0:
    st.warning("Sin datos para los filtros seleccionados.")

else:
    if mostrar_heatmap:
        st.markdown("## Análisis específico por ubicación física")
        st.caption(
            "Cada celda representa la frecuencia de intervenciones para una combinación Cabezal × Tulipa, separada por equipo y formato."
        )

        st.plotly_chart(
            crear_heatmaps(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_top_tulipas:
        st.plotly_chart(
            grafico_top_tulipas(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_tendencia:
        st.markdown("## Tendencia temporal")

        st.plotly_chart(
            grafico_tendencia(df_f),
            use_container_width=True
        )

        st.markdown("---")

    graficos_generales = [
        mostrar_formatos,
        mostrar_turno,
        mostrar_mantencion,
        mostrar_operador
    ]

    if any(graficos_generales):
        st.markdown("## Análisis general")

        if mostrar_formatos:
            st.plotly_chart(
                grafico_formatos(df_f),
                use_container_width=True
            )

        if mostrar_turno:
            st.plotly_chart(
                grafico_turno(df_f),
                use_container_width=True
            )

        if mostrar_mantencion:
            st.plotly_chart(
                grafico_mantencion(df_f),
                use_container_width=True
            )

        if mostrar_operador:
            st.plotly_chart(
                grafico_operador(df_f),
                use_container_width=True
            )

        st.markdown("---")

# ============================================================================
# TABLA Y DESCARGA
# ============================================================================

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

    df_dl = df_f.copy()
    df_dl["Fecha"] = df_dl["Fecha"].dt.strftime("%d-%m-%Y")

    if "Fecha registro" in df_dl.columns:
        df_dl["Fecha registro"] = pd.to_datetime(
            df_dl["Fecha registro"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

    st.download_button(
        "Descargar datos filtrados",
        df_dl.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"tulipas_linea11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ============================================================================
# SIDEBAR INFO
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### Fuente de datos")

fmt_min = df["Fecha"].min().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].min()) else "N/A"
fmt_max = df["Fecha"].max().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].max()) else "N/A"

st.sidebar.info(
    f"Google Sheets\n\n"
    f"- {len(df):,} registros totales\n"
    f"- Período: {fmt_min} → {fmt_max}\n"
    f"- Formatos: 237, 350, 1.000, 1.250 CC\n"
    f"- Cabezales: según formato\n"
    f"- Tulipas: hasta 30 por cabezal"
)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    f"""
    <div style='text-align:center; opacity:0.6; font-size:0.8rem;'>
        Dashboard conectado a Google Sheets · Streamlit + Plotly · Línea 11 ·
        {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)
