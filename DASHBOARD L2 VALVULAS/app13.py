"""
Dashboard de Mantenimiento de Válvulas Krones - Línea 2
Conectado al formulario Streamlit y Google Sheets.
Dashboard Área de Operaciones - Análisis de válvulas Krones.
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
    page_title="Dashboard Válvulas Krones Línea 2",
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

    if pd.notna(fecha):
        fecha_txt = fecha.strftime("%d-%m-%Y %H:%M")
    else:
        fecha_txt = "-"

    return fecha_txt, operador


def obtener_valvula_mas_critica(df):
    if df.empty:
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


# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data(ttl=1)
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

    if "Fecha registro" in df.columns:
        df["Fecha registro"] = pd.to_datetime(df["Fecha registro"], errors="coerce")

    df["Turno"] = df["Turno"].astype(str).str.strip().str.upper()
    df["Operador"] = df["Operador"].fillna("").astype(str).str.strip().str.upper()
    df["Mantención"] = df["Mantención"].fillna("").astype(str).str.strip().str.upper()
    df["Observaciones"] = df["Observaciones"].fillna("").astype(str).str.strip()

    df = df.dropna(subset=["Fecha", "Válvula"])
    df["Válvula"] = df["Válvula"].astype(int)

    df = df[df["Válvula"].between(1, 112)].copy()

    columnas_finales = [
        "Fecha",
        "Turno",
        "Operador",
        "Válvula",
        "Mantención",
        "Observaciones"
    ]

    if "Fecha registro" in df.columns:
        columnas_finales.append("Fecha registro")

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

    aplicar_estilo_figura(fig, "Tendencia temporal de registros", 380)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Registros",
        margin=dict(l=70, r=80, t=85, b=75),
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

    detalle_operadores = (
        df.assign(Operador=df["Operador"].replace("", "SIN OPERADOR"))
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

    aplicar_estilo_figura(fig, "Registros por turno", 360, t=85, b=75)
    fig.update_layout(
        xaxis_title="Turno",
        yaxis_title="Cantidad",
        showlegend=False,
        margin=dict(l=70, r=80, t=85, b=75)
    )

    max_y = vc["Cantidad"].max() if not vc.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_por_operador(df):
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

    aplicar_estilo_figura(fig, "Top operadores", 420, t=85, b=150)
    fig.update_layout(
        xaxis_title="Operador",
        yaxis_title="Cantidad",
        showlegend=False,
        margin=dict(l=70, r=80, t=85, b=155)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = op["Cantidad"].max() if not op.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

    return fig


def grafico_por_mantencion(df):
    mt = df["Mantención"].value_counts().reset_index()
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

    aplicar_estilo_figura(fig, "Tipos de mantención", 430, t=85, b=160)
    fig.update_layout(
        xaxis_title="Tipo de mantención",
        yaxis_title="Cantidad",
        showlegend=False,
        margin=dict(l=70, r=80, t=85, b=165)
    )

    fig.update_xaxes(tickangle=-35)

    max_y = mt["Cantidad"].max() if not mt.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25])

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

    aplicar_estilo_figura(fig, "Heatmap: turno × operador", 390)
    fig.update_layout(
        xaxis_title="Operador",
        yaxis_title="Turno",
        margin=dict(l=70, r=80, t=85, b=120)
    )

    fig.update_xaxes(tickangle=-35)

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
        yaxis_title="Número de válvula",
        margin=dict(l=80, r=90, t=85, b=75)
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
        text=conteos.values,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>Válvula %{x}</b><br>Mantenciones: %{y}<extra></extra>"
    )])

    aplicar_estilo_figura(fig, "Estado global de las 112 válvulas", 430, t=85, b=90)
    fig.update_layout(
        xaxis_title="Número de válvula",
        yaxis_title="Cantidad de mantenciones",
        showlegend=False,
        margin=dict(l=70, r=80, t=85, b=95)
    )

    max_y = conteos.max() if not conteos.empty else 1
    fig.update_yaxes(range=[0, max_y * 1.25 if max_y > 0 else 1])

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

    aplicar_estilo_figura(fig, "Distribución válvula × tipo de mantención", 390)
    fig.update_layout(
        xaxis_title="Número de válvula",
        yaxis_title="Tipo de mantención",
        margin=dict(l=70, r=80, t=85, b=75)
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

operadores_base = df["Operador"].replace("", "SIN OPERADOR")

operadores_sel = st.sidebar.multiselect(
    "Operadores",
    sorted(operadores_base.dropna().unique()),
    default=sorted(operadores_base.dropna().unique())
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

mostrar_turno_operador = st.sidebar.checkbox(
    "Turno × operador",
    value=False
)

mostrar_heatmap_valvula = st.sidebar.checkbox(
    "Válvula × tipo de mantención",
    value=True
)

mostrar_burbujas = st.sidebar.checkbox(
    "Distribución válvula × mantención",
    value=True
)

mostrar_tabla_resumen = st.sidebar.checkbox(
    "Tabla resumen por válvula",
    value=False
)

mostrar_datos_detallados = st.sidebar.checkbox(
    "Mostrar datos detallados",
    value=True
)

# =====================================================
# FILTRO DATAFRAME
# =====================================================
df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["Turno"].isin(turnos_sel)) &
    (operadores_base.isin(operadores_sel)) &
    (df["Mantención"].isin(mantencion_sel)) &
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
dias_con_registros = df_f["Fecha"].nunique()
operadores_unicos = df_f["Operador"].replace("", "SIN OPERADOR").nunique()
valvulas_intervenidas = df_f["Válvula"].nunique()
promedio_registros_dia = len(df_f) / max(df_f["Fecha"].nunique(), 1)

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

kpi6, kpi7 = st.columns(2)

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

kpi8, kpi9 = st.columns(2)

with kpi8:
    valvulas_sin_registro = 112 - df_f["Válvula"].nunique()

    tarjeta_kpi(
        "Válvulas sin registro",
        valvulas_sin_registro,
        "Dentro del rango filtrado"
    )

with kpi9:
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
    if mostrar_estado_global:
        st.markdown("## Estado global de válvulas")
        st.caption(
            "Criterio visual: verde = sin registros, naranjo = 1 a 2 registros, rojo = 3 o más registros."
        )

        st.plotly_chart(
            grafico_estado_valvulas(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_tendencia:
        st.markdown("## Análisis temporal")

        st.plotly_chart(
            grafico_tendencia_temporal(df_f),
            use_container_width=True
        )

        st.markdown("---")

    graficos_generales = [
        mostrar_turno,
        mostrar_operador,
        mostrar_mantencion
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

        st.markdown("---")

    if mostrar_turno_operador:
        st.markdown("## Análisis turno × operador")

        st.plotly_chart(
            grafico_turno_operador(df_f),
            use_container_width=True
        )

        st.markdown("---")

    if mostrar_heatmap_valvula:
        st.markdown("## Análisis por válvula y tipo de mantención")

        st.plotly_chart(
            grafico_heatmap_valvula_mantencion(df_f),
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

    if mostrar_tabla_resumen:
        st.markdown("## Tabla resumen por válvula")

        df_resumen = crear_tabla_resumen_valvulas(df_f)

        st.dataframe(
            df_resumen,
            use_container_width=True,
            height=420
        )

        st.markdown("### Descarga resumen")

        st.download_button(
            "Descargar resumen de válvulas",
            df_resumen.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"resumen_valvulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
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
            file_name=f"datos_valvulas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
