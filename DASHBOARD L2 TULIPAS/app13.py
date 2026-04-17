"""
Dashboard de Mantenimiento de Tulipas - Embotelladora CCU
Streamlit App para GitHub + Streamlit Cloud
Conectado a Google Sheets
VERSIÓN 4.4: Reordenado con mapa físico en la parte superior y título sin emoji
LÍNEA 2
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
    page_title="Dashboard Tulipas CCU",
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
# NORMALIZACIÓN DE FORMATOS
# ============================================================================

def normalizar_formato(val):
    """Normaliza variantes de formato al valor canónico: '2.000 CC' o '2.500 CC'"""
    if pd.isna(val):
        return val
    s = str(val).replace(" ", "").replace(".", "").replace(",", "").upper()
    digits = re.sub(r"[^0-9]", "", s)
    if digits == "2000":
        return "2.000 CC"
    elif digits == "2500":
        return "2.500 CC"
    return str(val).strip()

# ============================================================================
# 1. CARGAR DATOS DESDE GOOGLE SHEETS
# ============================================================================

@st.cache_data(ttl=1)
def load_data_from_sheets():
    sheet_id = "1EjrHHNJXjjBOObeAfIBxQjDfcyCS-o_j4FLaDxOPjRI"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    try:
        df = pd.read_csv(csv_url)

        # Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]

        columnas_requeridas = [
            'Fecha', 'Turno', 'Operador', 'Equipo', 'Formato',
            'Cabezal', 'Tulipa', 'Mantención', 'Comentarios'
        ]

        if not all(col in df.columns for col in columnas_requeridas):
            st.sidebar.warning("⚠️ Columnas faltantes. Usando datos de ejemplo.")
            return load_data_example()

        # Parseo de fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        if 'Fecha registro' in df.columns:
            df['Fecha registro'] = pd.to_datetime(df['Fecha registro'], errors='coerce')

        # Normalización de formatos y tipos
        df['Formato'] = df['Formato'].apply(normalizar_formato)
        df['Equipo'] = df['Equipo'].astype(str).str.strip()
        df['Turno'] = df['Turno'].astype(str).str.strip()
        df['Operador'] = df['Operador'].fillna('').astype(str).str.strip()
        df['Mantención'] = df['Mantención'].fillna('').astype(str).str.strip()
        df['Comentarios'] = df['Comentarios'].fillna('').astype(str).str.strip()

        df['Cabezal'] = pd.to_numeric(df['Cabezal'], errors='coerce').astype('Int64')
        df['Tulipa'] = pd.to_numeric(df['Tulipa'], errors='coerce').astype('Int64')

        df = df.dropna(subset=['Fecha', 'Cabezal', 'Tulipa'])

        n = len(df)
        st.sidebar.success(f"✅ {n:,} registros cargados desde Google Sheets")
        return df

    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
        st.sidebar.info("Usando datos de ejemplo...")
        return load_data_example()


@st.cache_data
def load_data_example():
    np.random.seed(42)
    fechas = pd.date_range('2025-01-01', '2026-04-14', freq='D')
    n = 2000
    data = {
        'Fecha': np.random.choice(fechas, n),
        'Turno': np.random.choice(['A', 'B', 'C'], n),
        'Operador': np.random.choice(['Roberto Silva', 'Mariana López', 'Carlos Reyes', 'Patricia Muñoz', ''], n),
        'Equipo': np.random.choice(['Encajonadora', 'Desencajonadora'], n),
        'Formato': np.random.choice(['2.000 CC', '2.500 CC'], n),
        'Cabezal': np.random.choice(range(1, 8), n),
        'Tulipa': np.random.choice(range(1, 10), n),
        'Mantención': np.random.choice([
            'CAMBIO DE GOMA TULIPA', 'CAMBIO DE VÁSTAGO', 'AJUSTE DE PRESIÓN',
            'REEMPLAZO DE SELLO', 'LIMPIEZA', 'OTRO'
        ], n),
        'Comentarios': np.random.choice([
            '', 'Sin novedad', 'Requiere seguimiento', 'Urgente'
        ], n),
        'Fecha registro': np.random.choice(pd.date_range('2026-04-01', '2026-04-14', freq='h'), n)
    }
    df = pd.DataFrame(data)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Fecha registro'] = pd.to_datetime(df['Fecha registro'])
    return df


# ============================================================================
# 2. GEOMETRÍA DE TULIPAS - LÍNEA 2
# ============================================================================

GEOMETRIA = {
    "2.000 CC": {
        'filas': 3, 'columnas': 3,
        'layout': [[7, 8, 9], [4, 5, 6], [1, 2, 3]],
        'n_tulipas': 9,
        'n_cabezales': 7,
    },
    "2.500 CC": {
        'filas': 3, 'columnas': 2,
        'layout': [[5, 6], [3, 4], [1, 2]],
        'n_tulipas': 6,
        'n_cabezales': 7,
    }
}

# ============================================================================
# 3. CREAR HEATMAP
# ============================================================================

def crear_heatmaps(df_filtrado):
    configs = [
        ('Desencajonadora', '2.000 CC'),
        ('Encajonadora', '2.000 CC'),
        ('Desencajonadora', '2.500 CC'),
        ('Encajonadora', '2.500 CC'),
    ]

    subtitles = [f"<b>{eq} {fmt}</b>" for eq, fmt in configs]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=subtitles,
        horizontal_spacing=0.18,
        vertical_spacing=0.22,
        specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}],
               [{'type': 'heatmap'}, {'type': 'heatmap'}]]
    )

    global_max = 0
    matrices_all = []

    for equipo, formato in configs:
        geo = GEOMETRIA[formato]
        n_cabezal = geo['n_cabezales']
        n_tulipas = geo['n_tulipas']
        matriz = np.zeros((n_cabezal, n_tulipas), dtype=int)

        subset = df_filtrado[
            (df_filtrado['Equipo'] == equipo) &
            (df_filtrado['Formato'] == formato)
        ].copy()

        if len(subset) > 0:
            conteos = subset.groupby(['Cabezal', 'Tulipa']).size()
            for (cab, tul), cnt in conteos.items():
                ci = int(cab) - 1
                ti = int(tul) - 1
                if 0 <= ci < n_cabezal and 0 <= ti < n_tulipas:
                    matriz[ci, ti] = cnt

        global_max = max(global_max, int(matriz.max()) if matriz.size else 0)
        matrices_all.append((matriz, formato, equipo, subset.copy()))

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    zmax = max(global_max, 1)

    for idx, ((matriz, formato, equipo, subset), (row, col)) in enumerate(zip(matrices_all, positions)):
        geo = GEOMETRIA[formato]
        n_tulipas = geo['n_tulipas']
        n_cabezal = geo['n_cabezales']

        hover_text = []
        for ci in range(n_cabezal):
            fila_hover = []
            for ti in range(n_tulipas):
                cab_num = ci + 1
                tul_num = ti + 1
                cnt = int(matriz[ci, ti])
                mask = (subset['Cabezal'] == cab_num) & (subset['Tulipa'] == tul_num)
                mant_list = subset.loc[mask, 'Mantención'].dropna().astype(str).unique().tolist()
                comentarios_list = subset.loc[mask, 'Comentarios'].dropna().astype(str).unique().tolist()

                mant_block = ""
                if mant_list:
                    mant_str = "<br>".join(f"• {m}" for m in mant_list[:5])
                    if len(mant_list) > 5:
                        mant_str += f"<br><i>…y {len(mant_list)-5} más</i>"
                    mant_block = f"<br><b>Mantención:</b><br>{mant_str}"

                comentarios_block = ""
                comentarios_validos = [c for c in comentarios_list if c.strip()]
                if comentarios_validos:
                    com_str = "<br>".join(f"• {c}" for c in comentarios_validos[:3])
                    if len(comentarios_validos) > 3:
                        com_str += f"<br><i>…y {len(comentarios_validos)-3} más</i>"
                    comentarios_block = f"<br><b>Comentarios:</b><br>{com_str}"

                fila_hover.append(
                    f"<b>Cabezal {cab_num} · Tulipa {tul_num}</b><br>"
                    f"Registros: <b>{cnt}</b>"
                    f"{mant_block}{comentarios_block}"
                )
            hover_text.append(fila_hover)

        text_display = matriz.astype(str)
        text_display[matriz == 0] = ""
        show_colorbar = (idx == 1)

        hm = go.Heatmap(
            z=matriz,
            x=[f"T{i+1}" for i in range(n_tulipas)],
            y=[f"Cab {i+1}" for i in range(n_cabezal)],
            zmin=0,
            zmax=zmax,
            colorscale=[
                [0.0,  "#f7fbff"],
                [0.15, "#c6dbef"],
                [0.35, "#fdae6b"],
                [0.6,  "#f16913"],
                [0.8,  "#d94801"],
                [1.0,  "#7f2704"],
            ],
            showscale=show_colorbar,
            colorbar=dict(
                title=dict(text="Registros", font=dict(size=11)),
                thickness=14,
                len=0.42,
                y=0.78,
                x=1.01,
                tickfont=dict(size=10),
            ) if show_colorbar else None,
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text,
            text=text_display,
            texttemplate='%{text}',
            textfont=dict(size=11),
            name='',
        )

        fig.add_trace(hm, row=row, col=col)
        fig.update_xaxes(title_text='Tulipa', tickfont=dict(size=9), row=row, col=col)
        fig.update_yaxes(tickfont=dict(size=9), autorange='reversed', row=row, col=col)

    fig.update_layout(
        title=dict(
            text='<b>Mapa de calor de frecuencia por cabezal y tulipa</b>',
            font=dict(size=15),
            x=0.5,
            xanchor='center'
        ),
        height=850,
        showlegend=False,
        font=dict(family="Arial, sans-serif", size=11),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=70, r=90, t=100, b=60),
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(size=13))

    return fig

# ============================================================================
# 4. OTROS GRÁFICOS
# ============================================================================

def grafico_top_tulipas(df, top_n=15):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    top = (df.groupby(['Equipo', 'Formato', 'Cabezal', 'Tulipa'])
             .size()
             .reset_index(name='Frecuencia')
             .sort_values('Frecuencia', ascending=False)
             .head(top_n))

    top['Etiqueta'] = (
        top['Equipo'].str[:4] + ' ' +
        top['Formato'] + ' | C' +
        top['Cabezal'].astype(str) + '-T' +
        top['Tulipa'].astype(str)
    )

    fig = go.Figure(go.Bar(
        x=top['Frecuencia'],
        y=top['Etiqueta'],
        orientation='h',
        marker=dict(color=top['Frecuencia'], colorscale='YlOrRd', showscale=False),
        text=top['Frecuencia'],
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=f'<b>Top {top_n} tulipas más afectadas</b>', font=dict(size=13)),
        xaxis_title='Registros',
        height=480,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=180, r=60, t=55, b=45),
        yaxis=dict(categoryorder='total ascending', tickfont=dict(size=10)),
    )
    return fig


def grafico_tendencia(df):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    tend = (df.groupby(df['Fecha'].dt.date)
              .size()
              .reset_index(name='Registros'))
    tend.columns = ['Fecha', 'Registros']
    tend['Fecha'] = pd.to_datetime(tend['Fecha'])
    tend = tend.sort_values('Fecha')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tend['Fecha'], y=tend['Registros'],
        name='Registros', marker_color='#4a90d9', opacity=0.75,
        hovertemplate='<b>%{x|%d-%m-%Y}</b><br>%{y} registros<extra></extra>'
    ))

    if len(tend) >= 5:
        tend['MA7'] = tend['Registros'].rolling(7, min_periods=1, center=True).mean()
        fig.add_trace(go.Scatter(
            x=tend['Fecha'], y=tend['MA7'],
            name='Promedio 7 días',
            mode='lines',
            line=dict(color='#e74c3c', width=2.5),
            hovertemplate='<b>%{x|%d-%m-%Y}</b><br>Promedio: %{y:.1f}<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text='<b>Tendencia temporal de mantenimientos</b>', font=dict(size=13)),
        xaxis_title='Fecha', yaxis_title='Registros',
        height=400, hovermode='x unified',
        legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=55, r=20, t=55, b=45),
    )
    return fig


def grafico_turno(df):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    dist = df['Turno'].value_counts().reset_index()
    dist.columns = ['Turno', 'Cantidad']
    colores = {'A': '#3498db', 'B': '#2ecc71', 'C': '#e74c3c'}

    fig = go.Figure(go.Pie(
        labels=['Turno ' + str(t) for t in dist['Turno']],
        values=dist['Cantidad'],
        marker=dict(colors=[colores.get(t, '#95a5a6') for t in dist['Turno']]),
        textposition='inside',
        textinfo='label+percent+value',
        hole=0.35,
        hovertemplate='<b>%{label}</b><br>%{value} registros (%{percent})<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text='<b>Distribución por turno</b>', font=dict(size=13)),
        height=380,
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig


def grafico_equipos(df):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    dist = df.groupby(['Equipo', 'Formato']).size().reset_index(name='Cantidad')
    fig = px.bar(
        dist, x='Equipo', y='Cantidad', color='Formato',
        barmode='group',
        title='<b>Registros por equipo y formato</b>',
        color_discrete_map={'2.000 CC': '#3498db', '2.500 CC': '#e74c3c'},
        height=380,
        labels={'Cantidad': 'Registros'}
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        title_font_size=13,
        legend_title_text='Formato',
        margin=dict(l=55, r=20, t=55, b=45),
    )
    return fig


def grafico_operador(df):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    _vc = df['Operador'].replace('', 'Sin operador').value_counts()
    dist = pd.DataFrame({'Operador': _vc.index, 'Cantidad': _vc.values})
    dist = dist.sort_values('Cantidad', ascending=True)

    fig = go.Figure(go.Bar(
        y=dist['Operador'], x=dist['Cantidad'],
        orientation='h',
        marker=dict(color=dist['Cantidad'], colorscale='Blues', showscale=False),
        text=dist['Cantidad'], textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x} registros<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text='<b>Registros por operador</b>', font=dict(size=13)),
        xaxis_title='Registros',
        height=max(350, 60 * len(dist)),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=160, r=60, t=55, b=45),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


def grafico_mantencion(df):
    if len(df) == 0:
        return go.Figure().add_annotation(text="Sin datos", showarrow=False)

    mant = df['Mantención'].replace('', 'Sin mantención').value_counts().head(12).reset_index()
    mant.columns = ['Mantención', 'Cantidad']
    mant = mant.sort_values('Cantidad', ascending=True)

    fig = go.Figure(go.Bar(
        y=mant['Mantención'], x=mant['Cantidad'],
        orientation='h',
        marker=dict(color=mant['Cantidad'], colorscale='Viridis', showscale=False),
        text=mant['Cantidad'], textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x} registros<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text='<b>Tipos de mantención más frecuentes</b>', font=dict(size=13)),
        xaxis_title='Registros',
        height=max(350, 40 * len(mant)),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=250, r=60, t=55, b=45),
        yaxis=dict(tickfont=dict(size=10)),
    )
    return fig

# ============================================================================
# 5. INTERFAZ STREAMLIT
# ============================================================================

df = load_data_from_sheets()

st.markdown("""
<div style='text-align:center; margin-bottom:1.2rem;'>
  <h1 style='margin-bottom:0.2rem;'>Dashboard Mantenimiento Tulipas · Línea 2</h1>
  <p style='font-size:1.05rem; margin:0.1rem 0;'>Embotelladora CCU</p>
  <p style='font-size:0.9rem; opacity:0.7; margin:0;'>
    Elaborado por: <b>Enrique Brun</b> &nbsp;|&nbsp; Jefe de Operaciones: <b>Gastón Flores</b>
  </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🔍 Filtros")

fecha_min = df['Fecha'].min()
fecha_max = df['Fecha'].max()

col_f1, col_f2 = st.sidebar.columns(2)
with col_f1:
    fecha_inicio = st.date_input(
        "Desde", value=fecha_min.date(),
        min_value=fecha_min.date(), max_value=fecha_max.date()
    )
with col_f2:
    fecha_fin = st.date_input(
        "Hasta", value=fecha_max.date(),
        min_value=fecha_min.date(), max_value=fecha_max.date()
    )

equipos_opciones = sorted(df['Equipo'].dropna().unique())
equipos_sel = st.sidebar.multiselect("Equipos", equipos_opciones, default=equipos_opciones)

formatos_opciones = sorted(df['Formato'].dropna().unique())
formatos_sel = st.sidebar.multiselect("Formatos", formatos_opciones, default=formatos_opciones)

turnos_opciones = sorted(df['Turno'].dropna().unique())
turnos_sel = st.sidebar.multiselect("Turnos", turnos_opciones, default=turnos_opciones)

operadores_opciones = sorted(df['Operador'].fillna('').replace('', 'Sin operador').unique())
operadores_sel = st.sidebar.multiselect("Operadores", operadores_opciones, default=operadores_opciones)

operador_filtrado = df['Operador'].fillna('').replace('', 'Sin operador')

df_f = df[
    (df['Fecha'].dt.date >= fecha_inicio) &
    (df['Fecha'].dt.date <= fecha_fin) &
    (df['Equipo'].isin(equipos_sel)) &
    (df['Formato'].isin(formatos_sel)) &
    (df['Turno'].isin(turnos_sel)) &
    (operador_filtrado.isin(operadores_sel))
].copy()

st.markdown("### 📊 KPIs")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("📝 Total Registros", f"{len(df_f):,}")
with m2:
    st.metric("📅 Días Activos", df_f['Fecha'].nunique())
with m3:
    st.metric("👥 Operadores", operador_filtrado.loc[df_f.index].replace('', 'Sin operador').nunique())
with m4:
    st.metric("🏭 Equipos", df_f['Equipo'].nunique())
with m5:
    prom = len(df_f) / max(df_f['Fecha'].nunique(), 1)
    st.metric("📊 Reg/Día Prom.", f"{prom:.1f}")

st.markdown("---")

if len(df_f) == 0:
    st.warning("⚠️ Sin datos para los filtros seleccionados.")
else:
    st.caption("Ordenado desde una vista general del comportamiento temporal y distribución global, hasta el detalle específico por cabezal y tulipa.")

    st.markdown("### Visión general")
    st.plotly_chart(grafico_tendencia(df_f), use_container_width=True)

    st.markdown("---")
    st.markdown("### Detalle específico por ubicación física")
    st.info(
        "Cada celda muestra la cantidad de eventos de mantenimiento registrados "
        "para esa combinación Cabezal × Tulipa. "
        "El color escala de blanco (0) a rojo oscuro (máximo)."
    )
    st.plotly_chart(crear_heatmaps(df_f), use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_equipos(df_f), use_container_width=True)
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


st.markdown("---")
st.markdown("### 📋 Datos Detallados")

if st.checkbox("Mostrar tabla completa"):
    df_show = df_f.copy()
    df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d-%m-%Y')
    if 'Fecha registro' in df_show.columns:
        df_show['Fecha registro'] = pd.to_datetime(df_show['Fecha registro'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    st.dataframe(df_show, use_container_width=True, height=400)

col1, col2 = st.columns(2)
with col1:
    df_dl = df_f.copy()
    df_dl['Fecha'] = df_dl['Fecha'].dt.strftime('%d-%m-%Y')
    if 'Fecha registro' in df_dl.columns:
        df_dl['Fecha registro'] = pd.to_datetime(df_dl['Fecha registro'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    st.download_button(
        "⬇️ Descargar CSV",
        df_dl.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"tulipas_linea2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Fuente de Datos")
fmt_min = df['Fecha'].min().strftime('%d-%m-%Y') if pd.notna(df['Fecha'].min()) else 'N/A'
fmt_max = df['Fecha'].max().strftime('%d-%m-%Y') if pd.notna(df['Fecha'].max()) else 'N/A'
st.sidebar.info(
    f"**Google Sheets** (caché 1 s)\n\n"
    f"- {len(df):,} registros totales\n"
    f"- Período: {fmt_min} → {fmt_max}"
)

st.markdown("---")
st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.82rem;'>"
    "<b>Dashboard Mantenimiento de Tulipas</b> · Embotelladora CCU · Línea 2<br>"
    "Streamlit + Plotly · v4.4"
    "</div>",
    unsafe_allow_html=True
)
