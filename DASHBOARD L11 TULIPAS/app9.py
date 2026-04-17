"""
Dashboard de Mantenimiento de Tulipas - Embotelladora CCU
Streamlit App para GitHub + Streamlit Cloud
Conectado a Google Sheets
VERSIÓN 9.0: caché 1 segundo y fuente de datos corregida
LÍNEA 11
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
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
# ESTILOS CSS PERSONALIZADOS
# ============================================================================

st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    h1 { text-align: center; margin-bottom: 0.3rem; }
    h2 { border-bottom: 2px solid #3498db; padding-bottom: 0.4rem; }
    .stMetric { border-radius: 0.5rem; padding: 0.5rem; border: 1px solid rgba(128,128,128,0.2); }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# NORMALIZACIÓN
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

# ============================================================================
# CARGA DE DATOS
# ============================================================================

@st.cache_data(ttl=1)
def load_data_from_sheets():
    sheet_id = "1PmDo4EjBxXZx0fPMGPMJKzBztyAq8AipxqCsJTFI0e0"
    urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=0",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
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
                df["Fecha registro"] = pd.to_datetime(df["Fecha registro"], errors="coerce")

            df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

            if "Fecha registro" in df.columns:
                df["Fecha"] = df["Fecha"].fillna(df["Fecha registro"])

            df["Equipo"] = limpiar_texto_serie(df["Equipo"], "Sin equipo")
            df["Formato"] = df["Formato"].apply(normalizar_formato)
            df["Turno"] = limpiar_texto_serie(df["Turno"], "Sin turno")
            df["Operador"] = limpiar_texto_serie(df["Operador"], "Sin operador")
            df["Mantención"] = limpiar_texto_serie(df["Mantención"], "Sin mantención")
            df["Comentarios"] = limpiar_texto_serie(df["Comentarios"], "")

            df["Cabezal"] = pd.to_numeric(df["Cabezal"], errors="coerce").astype("Int64")
            df["Tulipa"] = pd.to_numeric(df["Tulipa"], errors="coerce").astype("Int64")

            df = df.dropna(subset=["Fecha", "Cabezal", "Tulipa"]).copy()
            df = df.sort_values(["Fecha", "Cabezal", "Tulipa"]).reset_index(drop=True)

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
        "Operador": np.random.choice(["Sin operador", "Luis Soto", "María Rojas", "Carlos Pérez"], n),
        "Equipo": np.random.choice(["Encajonadora", "Desencajonadora"], n),
        "Formato": np.random.choice(["237 CC", "350 CC", "1.000 CC", "1.250 CC"], n),
        "Cabezal": np.random.choice(range(1, 10), n),
        "Tulipa": np.random.choice(range(1, 31), n),
        "Mantención": np.random.choice([
            "CAMBIO DE GOMA TULIPA",
            "CAMBIO DE VÁSTAGO",
            "CAMBIO DE RESORTE",
            "AJUSTE",
            "LIMPIEZA"
        ], n),
        "Comentarios": np.random.choice(["", "Sin novedad", "Urgente", "Revisar"], n),
    }
    df = pd.DataFrame(data)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

# ============================================================================
# GEOMETRÍA
# ============================================================================

GEOMETRIA = {
    "237 CC": {"n_cabezales": 9, "total_tulipas": 30},
    "350 CC": {"n_cabezales": 9, "total_tulipas": 30},
    "1.000 CC": {"n_cabezales": 9, "total_tulipas": 30},
    "1.250 CC": {"n_cabezales": 9, "total_tulipas": 30},
}

# ============================================================================
# HEATMAPS
# ============================================================================

def crear_heatmaps(df_filtrado):
    formatos_list = ["237 CC", "350 CC", "1.000 CC", "1.250 CC"]
    equipos_list = ["Desencajonadora", "Encajonadora"]

    configs = [(fmt, eq) for fmt in formatos_list for eq in equipos_list]
    subtitles = [f"<b>{eq} {fmt}</b>" for fmt, eq in configs]

    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=subtitles,
        horizontal_spacing=0.15,
        vertical_spacing=0.18,
        specs=[[{"type": "heatmap"}, {"type": "heatmap"}],
               [{"type": "heatmap"}, {"type": "heatmap"}],
               [{"type": "heatmap"}, {"type": "heatmap"}],
               [{"type": "heatmap"}, {"type": "heatmap"}]]
    )

    global_max = 0
    matrices_all = []

    for fmt, eq in configs:
        subset = df_filtrado[
            (df_filtrado["Equipo"] == eq) &
            (df_filtrado["Formato"] == fmt)
        ]
        if len(subset) > 0:
            max_val = subset.groupby(["Cabezal", "Tulipa"]).size().max()
            global_max = max(global_max, int(max_val))

    for fmt, eq in configs:
        geo = GEOMETRIA[fmt]
        n_cabezales = geo["n_cabezales"]
        n_tulipas = geo["total_tulipas"]

        matriz = np.zeros((n_cabezales, n_tulipas), dtype=int)

        subset = df_filtrado[
            (df_filtrado["Equipo"] == eq) &
            (df_filtrado["Formato"] == fmt)
        ]

        if len(subset) > 0:
            conteos = subset.groupby(["Cabezal", "Tulipa"]).size()
            for (cab, tul), cnt in conteos.items():
                ci = int(cab) - 1
                ti = int(tul) - 1
                if 0 <= ci < n_cabezales and 0 <= ti < n_tulipas:
                    matriz[ci, ti] = cnt

        matrices_all.append((matriz, fmt, eq, subset.copy()))

    positions = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 2)]
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

                mask = (subset["Cabezal"] == cab_num) & (subset["Tulipa"] == tul_num)
                mant_list = subset.loc[mask, "Mantención"].dropna().astype(str).unique().tolist()
                comentarios_list = subset.loc[mask, "Comentarios"].dropna().astype(str).unique().tolist()

                mant_block = ""
                if mant_list:
                    mant_str = "<br>".join(f"• {m}" for m in mant_list[:5])
                    if len(mant_list) > 5:
                        mant_str += f"<br><i>…y {len(mant_list)-5} más</i>"
                    mant_block = f"<br><b>Mantención:</b><br>{mant_str}"

                comentarios_validos = [c for c in comentarios_list if str(c).strip()]
                comentarios_block = ""
                if comentarios_validos:
                    com_str = "<br>".join(f"• {c}" for c in comentarios_validos[:3])
                    if len(comentarios_validos) > 3:
                        com_str += f"<br><i>…y {len(comentarios_validos)-3} más</i>"
                    comentarios_block = f"<br><b>Comentarios:</b><br>{com_str}"

                fila_hover.append(
                    f"<b>Cabezal {cab_num} · Tulipa {tul_num}</b><br>"
                    f"Registros: <b>{cnt}</b>{mant_block}{comentarios_block}"
                )
            hover_text.append(fila_hover)

        text_display = matriz.astype(str)
        text_display[matriz == 0] = ""
        show_colorbar = (idx == 1)

        hm = go.Heatmap(
            z=matriz,
            x=[f"T{i+1}" for i in range(n_tulipas)],
            y=[f"C{i+1}" for i in range(n_cabezales)],
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
            textfont=dict(size=9),
            name=""
        )

        fig.add_trace(hm, row=row, col=col)
        fig.update_xaxes(title_text="Tulipa", tickfont=dict(size=8), row=row, col=col)
        fig.update_yaxes(tickfont=dict(size=8), autorange="reversed", row=row, col=col)

    fig.update_layout(
        title=dict(
            text="<b>Mapa de calor por cabezal y tulipa</b>",
            font=dict(size=14),
            x=0.5,
            xanchor="center"
        ),
        height=1400,
        showlegend=False,
        font=dict(family="Arial, sans-serif", size=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=80, t=90, b=50),
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(size=11))

    return fig

# ============================================================================
# GRÁFICOS
# ============================================================================

def fig_sin_datos():
    fig = go.Figure()
    fig.add_annotation(text="Sin datos", showarrow=False)
    fig.update_layout(height=300)
    return fig

def grafico_tendencia(df):
    if len(df) == 0:
        return fig_sin_datos()

    tend = df.groupby(df["Fecha"].dt.date).size().reset_index(name="Registros")
    tend.columns = ["Fecha", "Registros"]
    tend["Fecha"] = pd.to_datetime(tend["Fecha"])
    tend = tend.sort_values("Fecha")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tend["Fecha"], y=tend["Registros"],
        name="Registros", marker_color="#4a90d9", opacity=0.75,
        hovertemplate="<b>%{x|%d-%m-%Y}</b><br>%{y} registros<extra></extra>"
    ))

    if len(tend) >= 5:
        tend["MA7"] = tend["Registros"].rolling(7, min_periods=1, center=True).mean()
        fig.add_trace(go.Scatter(
            x=tend["Fecha"], y=tend["MA7"],
            name="Promedio 7 días",
            mode="lines",
            line=dict(color="#e74c3c", width=2.5),
            hovertemplate="<b>%{x|%d-%m-%Y}</b><br>Promedio: %{y:.1f}<extra></extra>"
        ))

    fig.update_layout(
        title=dict(text="<b>Tendencia temporal de mantenimientos</b>", font=dict(size=13)),
        xaxis_title="Fecha", yaxis_title="Registros",
        height=400, hovermode="x unified",
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=55, r=20, t=55, b=45),
    )
    return fig

def grafico_formatos(df):
    if len(df) == 0:
        return fig_sin_datos()

    dist = df.groupby(["Equipo", "Formato"]).size().reset_index(name="Cantidad")
    fig = px.bar(
        dist, x="Equipo", y="Cantidad", color="Formato",
        barmode="group",
        title="<b>Registros por equipo y formato</b>",
        height=380,
        labels={"Cantidad": "Registros"}
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        title_font_size=13,
        legend_title_text="Formato",
        margin=dict(l=55, r=20, t=55, b=45),
    )
    return fig

def grafico_turno(df):
    if len(df) == 0:
        return fig_sin_datos()

    dist = df["Turno"].value_counts().reset_index()
    dist.columns = ["Turno", "Cantidad"]
    colores = {"A": "#3498db", "B": "#2ecc71", "C": "#e74c3c", "Sin turno": "#95a5a6"}

    fig = go.Figure(go.Pie(
        labels=["Turno " + str(t) for t in dist["Turno"]],
        values=dist["Cantidad"],
        marker=dict(colors=[colores.get(t, "#95a5a6") for t in dist["Turno"]]),
        textposition="inside",
        textinfo="label+percent+value",
        hole=0.35,
        hovertemplate="<b>%{label}</b><br>%{value} registros (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Distribución por turno</b>", font=dict(size=13)),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig

def grafico_mantencion(df):
    if len(df) == 0:
        return fig_sin_datos()

    mant = df["Mantención"].value_counts().head(12).reset_index()
    mant.columns = ["Mantención", "Cantidad"]
    mant = mant.sort_values("Cantidad", ascending=True)

    fig = go.Figure(go.Bar(
        y=mant["Mantención"], x=mant["Cantidad"],
        orientation="h",
        marker=dict(color=mant["Cantidad"], colorscale="Viridis", showscale=False),
        text=mant["Cantidad"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x} registros<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Tipos de mantención más frecuentes</b>", font=dict(size=13)),
        xaxis_title="Registros",
        height=max(350, 40 * len(mant)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=250, r=60, t=55, b=45),
        yaxis=dict(tickfont=dict(size=10)),
    )
    return fig

def grafico_operador(df):
    if len(df) == 0:
        return fig_sin_datos()

    vc = df["Operador"].value_counts()
    dist = pd.DataFrame({"Operador": vc.index, "Cantidad": vc.values}).sort_values("Cantidad", ascending=True)

    fig = go.Figure(go.Bar(
        y=dist["Operador"], x=dist["Cantidad"],
        orientation="h",
        marker=dict(color=dist["Cantidad"], colorscale="Blues", showscale=False),
        text=dist["Cantidad"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x} registros<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Registros por operador</b>", font=dict(size=13)),
        xaxis_title="Registros",
        height=max(350, 60 * len(dist)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=160, r=60, t=55, b=45),
        yaxis=dict(tickfont=dict(size=11)),
    )
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
        top["Equipo"].str[:4] + " " +
        top["Formato"] + " | C" +
        top["Cabezal"].astype(str) + "-T" +
        top["Tulipa"].astype(str)
    )

    fig = go.Figure(go.Bar(
        x=top["Frecuencia"],
        y=top["Etiqueta"],
        orientation="h",
        marker=dict(color=top["Frecuencia"], colorscale="YlOrRd", showscale=False),
        text=top["Frecuencia"],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=f"<b>Top {top_n} tulipas más afectadas</b>", font=dict(size=13)),
        xaxis_title="Registros",
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=180, r=60, t=55, b=45),
        yaxis=dict(categoryorder="total ascending", tickfont=dict(size=10)),
    )
    return fig

# ============================================================================
# INTERFAZ
# ============================================================================

df, error_carga = load_data_from_sheets()

if df is None:
    st.error(f"No se pudo cargar Google Sheets: {error_carga}")
    st.info("Se usarán datos de ejemplo para que el dashboard siga funcionando.")
    df = load_data_example()

st.markdown("""
<div style='text-align:center; margin-bottom:1.2rem;'>
  <h1 style='margin-bottom:0.2rem;'>Dashboard Mantenimiento Tulipas · Línea 11</h1>
  <p style='font-size:1.05rem; margin:0.1rem 0;'>Embotelladora CCU</p>
  <p style='font-size:0.9rem; opacity:0.7; margin:0;'>
    Elaborado por: <b>Enrique Brun</b> &nbsp;|&nbsp; Jefe de Operaciones: <b>Gastón Flores</b>
  </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# FILTROS
# ============================================================================

st.sidebar.markdown("## 🔍 Filtros")

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
equipos_sel = st.sidebar.multiselect("Equipos", equipos_opciones, default=equipos_opciones)

formatos_opciones = sorted(df["Formato"].dropna().unique())
formatos_sel = st.sidebar.multiselect("Formatos", formatos_opciones, default=formatos_opciones)

turnos_opciones = sorted(df["Turno"].dropna().unique())
turnos_sel = st.sidebar.multiselect("Turnos", turnos_opciones, default=turnos_opciones)

operadores_opciones = sorted(df["Operador"].dropna().unique())
operadores_sel = st.sidebar.multiselect("Operadores", operadores_opciones, default=operadores_opciones)

df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["Equipo"].isin(equipos_sel)) &
    (df["Formato"].isin(formatos_sel)) &
    (df["Turno"].isin(turnos_sel)) &
    (df["Operador"].isin(operadores_sel))
].copy()

# ============================================================================
# KPIS
# ============================================================================

st.markdown("### 📊 KPIs")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("📝 Total Registros", f"{len(df_f):,}")
with m2:
    st.metric("📅 Días Activos", df_f["Fecha"].nunique())
with m3:
    st.metric("👥 Operadores", df_f["Operador"].nunique())
with m4:
    st.metric("🏭 Equipos", df_f["Equipo"].nunique())
with m5:
    prom = len(df_f) / max(df_f["Fecha"].nunique(), 1)
    st.metric("📊 Reg/Día Prom.", f"{prom:.1f}")

# ============================================================================
# GRÁFICOS
# ============================================================================

st.markdown("---")

if len(df_f) == 0:
    st.warning("⚠️ Sin datos para los filtros seleccionados.")
else:
    st.caption("Ordenado desde la visión general hasta el detalle específico por cabezal y tulipa.")

    st.markdown("### Visión general")
    st.plotly_chart(grafico_tendencia(df_f), use_container_width=True)

    st.markdown("---")
    st.markdown("### Detalle específico por ubicación física")
    st.info(
        "Cada celda muestra la cantidad de eventos para la combinación Cabezal × Tulipa, "
        "separada por equipo y formato."
    )
    st.plotly_chart(crear_heatmaps(df_f), use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_formatos(df_f), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_turno(df_f), use_container_width=True)

    st.markdown("---")
    st.markdown("### Distribución operativa")
    st.plotly_chart(grafico_mantencion(df_f), use_container_width=True)

    st.markdown("---")
    st.markdown("### Foco por personas y componentes críticos")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_operador(df_f), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_top_tulipas(df_f), use_container_width=True)

# ============================================================================
# TABLA Y DESCARGA
# ============================================================================

st.markdown("---")
st.markdown("### 📋 Datos detallados")

if st.checkbox("Mostrar tabla completa"):
    df_show = df_f.copy()
    df_show["Fecha"] = df_show["Fecha"].dt.strftime("%d-%m-%Y")
    if "Fecha registro" in df_show.columns:
        df_show["Fecha registro"] = pd.to_datetime(df_show["Fecha registro"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(df_show, use_container_width=True, height=400)

col1, col2 = st.columns(2)
with col1:
    df_dl = df_f.copy()
    df_dl["Fecha"] = df_dl["Fecha"].dt.strftime("%d-%m-%Y")
    if "Fecha registro" in df_dl.columns:
        df_dl["Fecha registro"] = pd.to_datetime(df_dl["Fecha registro"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    st.download_button(
        "⬇️ Descargar CSV",
        df_dl.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"tulipas_linea11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ============================================================================
# SIDEBAR INFO
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Fuente de Datos")
fmt_min = df["Fecha"].min().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].min()) else "N/A"
fmt_max = df["Fecha"].max().strftime("%d-%m-%Y") if pd.notna(df["Fecha"].max()) else "N/A"

st.sidebar.info(
    f"**Google Sheets** (caché 1 s)\n\n"
    f"- {len(df):,} registros totales\n"
    f"- Período: {fmt_min} → {fmt_max}\n"
    f"- Formatos: 237, 350, 1.000, 1.250 CC\n"
    f"- Cabezales: hasta 9\n"
    f"- Tulipas: hasta 30 por cabezal"
)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.82rem;'>"
    "<b>Dashboard Mantenimiento de Tulipas</b> · Embotelladora CCU · Línea 11<br>"
    "Streamlit + Plotly · v9.0"
    "</div>",
    unsafe_allow_html=True
)
