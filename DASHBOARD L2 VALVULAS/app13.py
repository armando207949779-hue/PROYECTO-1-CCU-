"""
Dashboard de Mantenimiento de Válvulas Krones - Línea 2
Conectado al formulario Streamlit y Google Sheets.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Dashboard Válvulas Krones Línea 2",
    layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_ID = "12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

VALVULAS_TODAS = list(range(1, 113))

TIPOS_MANTENCION = [
    "BLOQUE",
    "O-RINGS",
    "RESORTE",
    "ON/OFF",
    "OTRO"
]

COLORS_REPUESTO = {
    "BLOQUE": "#3498db",
    "O-RINGS": "#e74c3c",
    "RESORTE": "#2ecc71",
    "ON/OFF": "#f39c12",
    "OTRO": "#9b59b6"
}

GRID = "rgba(128,128,128,0.15)"
LINE = "rgba(128,128,128,0.30)"


# =====================================================
# ESTILO
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }

    h1 {
        text-align: center;
        margin-bottom: 0.2rem;
        color: #0E4C92;
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


@st.cache_data(ttl=10)
def cargar_datos():
    df = pd.read_csv(CSV_URL)

    rename_cols = {
        "Número Válvula": "Válvula",
        "Repuesto": "Mantención",
        "Repuesto / Mantención": "Mantención",
        "Fecha Registro": "Fecha registro"
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

    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
    df["Válvula"] = pd.to_numeric(df["Válvula"], errors="coerce")

    df["Turno"] = df["Turno"].astype(str).str.strip().str.upper()
    df["Operador"] = df["Operador"].astype(str).str.strip().str.upper()
    df["Mantención"] = df["Mantención"].astype(str).str.strip().str.upper()
    df["Observaciones"] = df["Observaciones"].fillna("").astype(str)

    df = df.dropna(subset=["Fecha", "Válvula"])
    df["Válvula"] = df["Válvula"].astype(int)

    df = df[df["Válvula"].between(1, 112)]

    columnas_finales = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Observaciones"
    ]

    return df[columnas_finales].copy()


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

    aplicar_estilo_figura(fig, "Tendencia temporal de registros", 350)
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
    op = df["Operador"].value_counts().head(10).reset_index()
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

    aplicar_estilo_figura(fig, "Top operadores", 320)
    fig.update_layout(
        xaxis_title="Cantidad",
        showlegend=False
    )

    return fig


def grafico_por_mantencion(df):
    mt = df["Mantención"].value_counts().reset_index()
    mt.columns = ["Mantención", "Cantidad"]

    colores = [
        COLORS_REPUESTO.get(m, "#95a5a6")
        for m in mt["Mantención"]
    ]

    fig = go.Figure(data=[go.Pie(
        labels=mt["Mantención"],
        values=mt["Cantidad"],
        marker=dict(colors=colores),
        textposition="inside",
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Distribución por tipo de mantención", 350)

    return fig


def grafico_turno_operador(df):
    pivot = df.pivot_table(
        index="Turno",
        columns="Operador",
        aggfunc="size",
        fill_value=0
    )

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale="Blues",
        hovertemplate="<b>Turno %{y}</b><br><b>%{x}</b><br>Registros: %{z}<extra></extra>"
    ))

    aplicar_estilo_figura(fig, "Heatmap: turno × operador", 350)

    return fig


def grafico_heatmap_valvula_mantencion(df):
    pivot = df.pivot_table(
        index="Válvula",
        columns="Mantención",
        aggfunc="size",
        fill_value=0
    )

    for tipo in TIPOS_MANTENCION:
        if tipo not in pivot.columns:
            pivot[tipo] = 0

    for valvula in VALVULAS_TODAS:
        if valvula not in pivot.index:
            pivot.loc[valvula] = 0

    pivot = pivot.sort_index()[TIPOS_MANTENCION]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale="YlOrRd",
        colorbar=dict(title="Cantidad"),
        hovertemplate="<b>Válvula %{y}</b><br><b>%{x}</b><br>Registros: %{z}<extra></extra>"
    ))

    aplicar_estilo_figura(fig, "Válvulas 1-112 × tipo de mantención", 800, l=80)
    fig.update_layout(
        xaxis_title="Tipo de mantención",
        yaxis_title="Número de válvula"
    )

    return fig


def grafico_estado_valvulas(df):
    conteos = (
        df["Válvula"]
        .value_counts()
        .reindex(VALVULAS_TODAS, fill_value=0)
        .sort_index()
    )

    colores = [
        "#27ae60" if c == 0 else "#f39c12" if c <= 2 else "#e74c3c"
        for c in conteos.values
    ]

    fig = go.Figure(data=[go.Bar(
        x=conteos.index,
        y=conteos.values,
        marker=dict(color=colores),
        hovertemplate="<b>Válvula %{x}</b><br>Mantenciones: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Estado global de las 112 válvulas", 350)
    fig.update_layout(
        xaxis_title="Número de válvula",
        yaxis_title="Cantidad de mantenciones",
        showlegend=False
    )

    return fig


def grafico_valvula_mantencion_burbujas(df):
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

    aplicar_estilo_figura(fig, "Distribución válvula × tipo de mantención", 350)
    fig.update_layout(
        xaxis_title="Número de válvula",
        yaxis_title="Tipo de mantención"
    )

    return fig


def crear_tabla_resumen_valvulas(df):
    resumen = []

    for valvula in VALVULAS_TODAS:
        df_valvula = df[df["Válvula"] == valvula]

        if df_valvula.empty:
            resumen.append({
                "Válvula": valvula,
                "Total": 0,
                "Tipos": "SIN REGISTRO",
                "Último registro": "-",
                "Último operador": "-"
            })

        else:
            df_valvula = df_valvula.sort_values("Fecha")
            tipos = ", ".join(sorted(df_valvula["Mantención"].dropna().unique()))
            ultimo = df_valvula.iloc[-1]

            resumen.append({
                "Válvula": valvula,
                "Total": len(df_valvula),
                "Tipos": tipos,
                "Último registro": ultimo["Fecha"].strftime("%d-%m-%Y"),
                "Último operador": ultimo["Operador"]
            })

    return pd.DataFrame(resumen)


# =====================================================
# CARGA DE DATOS
# =====================================================
try:
    df = cargar_datos()
except Exception as e:
    st.error(f"No se pudieron cargar los datos desde Google Sheets: {e}")
    st.stop()


# =====================================================
# ENCABEZADO
# =====================================================
st.markdown(
    """
    <div style='text-align:center; margin-bottom:1.2rem;'>
        <h1>Dashboard Válvulas Krones · Línea 2</h1>
        <p style='color:#5D6D7E;'>
            Llenadora CCU · Monitoreo de mantenimiento de 112 válvulas
        </p>
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

turnos_sel = st.sidebar.multiselect(
    "Turnos",
    sorted(df["Turno"].dropna().unique()),
    default=sorted(df["Turno"].dropna().unique())
)

operadores_sel = st.sidebar.multiselect(
    "Operadores",
    sorted(df["Operador"].dropna().unique()),
    default=sorted(df["Operador"].dropna().unique())
)

mantencion_sel = st.sidebar.multiselect(
    "Tipos de mantención",
    sorted(df["Mantención"].dropna().unique()),
    default=sorted(df["Mantención"].dropna().unique())
)

valvulas_sel = st.sidebar.multiselect(
    "Válvulas",
    VALVULAS_TODAS,
    default=VALVULAS_TODAS
)


# =====================================================
# FILTRO DATAFRAME
# =====================================================
df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["Turno"].isin(turnos_sel)) &
    (df["Operador"].isin(operadores_sel)) &
    (df["Mantención"].isin(mantencion_sel)) &
    (df["Válvula"].isin(valvulas_sel))
].copy()


# =====================================================
# KPIS
# =====================================================
st.markdown("### KPIs generales")

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Total registros", f"{len(df_f):,}")

with m2:
    st.metric("Días con registros", df_f["Fecha"].nunique())

with m3:
    st.metric("Operadores", df_f["Operador"].nunique())

with m4:
    st.metric("Válvulas intervenidas", df_f["Válvula"].nunique())

with m5:
    promedio = len(df_f) / max(df_f["Fecha"].nunique(), 1)
    st.metric("Registros por día", f"{promedio:.1f}")


st.markdown("---")


# =====================================================
# CONTENIDO PRINCIPAL
# =====================================================
if df_f.empty:
    st.warning("Sin datos para los filtros seleccionados.")

else:
    st.markdown("## Nivel 1: Análisis general")

    st.plotly_chart(
        grafico_tendencia_temporal(df_f),
        use_container_width=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(
            grafico_por_turno(df_f),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            grafico_por_operador(df_f),
            use_container_width=True
        )

    with col3:
        st.plotly_chart(
            grafico_por_mantencion(df_f),
            use_container_width=True
        )

    st.markdown("---")

    st.markdown("## Nivel 2: Análisis intermedio")

    st.plotly_chart(
        grafico_turno_operador(df_f),
        use_container_width=True
    )

    st.markdown("---")

    st.markdown("## Nivel 3: Análisis específico de válvulas")

    st.plotly_chart(
        grafico_heatmap_valvula_mantencion(df_f),
        use_container_width=True
    )

    st.caption(
        "Criterio visual: verde = sin registros, naranjo = 1 a 2 registros, rojo = 3 o más registros."
    )

    st.plotly_chart(
        grafico_estado_valvulas(df_f),
        use_container_width=True
    )

    st.plotly_chart(
        grafico_valvula_mantencion_burbujas(df_f),
        use_container_width=True
    )

    st.markdown("### Tabla resumen por válvula")

    df_resumen = crear_tabla_resumen_valvulas(df_f)

    st.dataframe(
        df_resumen,
        use_container_width=True,
        height=400
    )

    st.markdown("---")

    st.markdown("## Datos detallados")

    mostrar_tabla = st.checkbox("Mostrar tabla completa de registros")

    if mostrar_tabla:
        df_show = df_f.copy()
        df_show["Fecha"] = df_show["Fecha"].dt.strftime("%d-%m-%Y")

        st.dataframe(
            df_show,
            use_container_width=True,
            height=500
        )

    st.markdown("### Descargas")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.download_button(
            "Descargar resumen de válvulas",
            df_resumen.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"resumen_valvulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col_d2:
        st.download_button(
            "Descargar datos filtrados",
            df_f.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"datos_valvulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
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
