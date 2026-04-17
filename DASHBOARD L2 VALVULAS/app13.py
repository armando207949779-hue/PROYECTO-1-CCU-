"""
Dashboard de Mantenimiento de Válvulas Krones - Llenadora CCU Línea 2
VERSIÓN 6.0 - FILTRO POR VÁLVULAS + ORDEN GENERAL A ESPECÍFICO + TABLA DE DATOS
Análisis: General → Específico
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Válvulas Krones Línea 2",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    h1 { text-align: center; margin-bottom: 0.3rem; }
    h2 { border-bottom: 2px solid #3498db; padding-bottom: 0.4rem; }
    </style>
""", unsafe_allow_html=True)

COLORS_REPUESTO = {
    'BLOQUE': '#3498db', 'O-RINGS': '#e74c3c', 'RESORTE': '#2ecc71',
    'ON/OFF': '#f39c12', 'OTRO': '#9b59b6',
}

_GRID, _LINE = 'rgba(128,128,128,0.15)', 'rgba(128,128,128,0.30)'
_HOVER = dict(bgcolor='rgba(255,255,255,0.98)', bordercolor='#1f2937', font=dict(color='#111827', size=12))

def _base(fig, title, height, l=70, r=65, t=65, b=55):
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', font=dict(size=13, color='#1a237e'), x=0.01),
        height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=l, r=r, t=t, b=b), font=dict(family='Arial, sans-serif', size=10), hoverlabel=_HOVER
    )
    fig.update_xaxes(showgrid=True, gridcolor=_GRID, zeroline=False, showline=True, linecolor=_LINE)
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, zeroline=False, showline=True, linecolor=_LINE)
    return fig

# ============================================================================
# CARGAR DATOS
# ============================================================================

@st.cache_data(ttl=1)
def load_data_from_sheets():
    sheet_id = "12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(csv_url)
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        if 'Número Válvula' in df.columns:
            df = df.rename(columns={'Número Válvula': 'Válvula'})
        if 'Repuesto' in df.columns:
            df = df.rename(columns={'Repuesto': 'Mantención'})
        df['Válvula'] = pd.to_numeric(df['Válvula'], errors='coerce').astype('Int64')
        df = df.drop(columns=[col for col in ['Fotografía', 'Fecha registro'] if col in df.columns])
        df = df.dropna(subset=['Fecha', 'Válvula'])
        st.sidebar.success(f"✅ {len(df):,} registros cargados")
        return df
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
        return load_data_example()

@st.cache_data
def load_data_example():
    np.random.seed(42)
    fechas = pd.date_range('2025-01-15', '2026-04-10', freq='D')
    n = 500
    data = {
        'Fecha': np.random.choice(fechas, n),
        'Turno': np.random.choice(['A', 'B', 'C'], n),
        'Operador': np.random.choice(['Didimo Valero', 'Jorge González', 'Richard Ruz'], n),
        'Válvula': np.random.choice(range(1, 113), n),
        'Mantención': np.random.choice(['O-RINGS', 'BLOQUE', 'RESORTE', 'ON/OFF', 'OTRO'], n),
        'Observaciones': np.random.choice(['Fuga', 'Normal', 'Ruido', ''], n),
    }
    df = pd.DataFrame(data)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

# ============================================================================
# GRÁFICOS
# ============================================================================

def grafico_tendencia_temporal(df):
    """GENERAL: Tendencia temporal"""
    if len(df) == 0:
        return go.Figure()
    df_tmp = df.copy()
    df_tmp['Fecha_dia'] = df_tmp['Fecha'].dt.date
    tend = df_tmp.groupby('Fecha_dia').size().reset_index(name='Registros')
    tend['Fecha_dia'] = pd.to_datetime(tend['Fecha_dia'])
    tend = tend.sort_values('Fecha_dia')
    tend['MA7'] = tend['Registros'].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tend['Fecha_dia'], y=tend['Registros'], mode='lines+markers',
        name='Registros diarios', line=dict(color='#1e88e5', width=1.5),
        fill='tozeroy', fillcolor='rgba(30,136,229,0.10)',
        hovertemplate='<b>%{x|%d-%m-%Y}</b><br>Registros: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=tend['Fecha_dia'], y=tend['MA7'].round(1), mode='lines',
        name='MA 7 días', line=dict(color='#e53935', width=2, dash='dot'),
        hovertemplate='<b>%{x|%d-%m-%Y}</b><br>MA7: %{y:.1f}<extra></extra>'
    ))
    _base(fig, '📈 Tendencia Temporal de Registros', 350)
    fig.update_layout(
        xaxis_title='Fecha', yaxis_title='Registros',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig

def grafico_por_turno(df):
    """GENERAL: Por turno"""
    if len(df) == 0:
        return go.Figure()
    vc = df['Turno'].value_counts().reset_index()
    vc.columns = ['Turno', 'Cantidad']
    vc = vc.sort_values('Turno')
    fig = go.Figure(data=[go.Bar(
        x=vc['Turno'], y=vc['Cantidad'],
        marker=dict(color=['#3498db', '#e74c3c', '#2ecc71'][:len(vc)]),
        text=vc['Cantidad'], textposition='outside',
        hovertemplate='<b>Turno %{x}</b><br>Registros: %{y}<extra></extra>'
    )])
    _base(fig, '⏰ Registros por Turno', 320)
    fig.update_layout(xaxis_title='Turno', yaxis_title='Cantidad', showlegend=False)
    return fig

def grafico_por_operador(df):
    """GENERAL: Top operadores"""
    if len(df) == 0:
        return go.Figure()
    op = df['Operador'].value_counts().head(10).reset_index()
    op.columns = ['Operador', 'Cantidad']
    op = op.sort_values('Cantidad')
    fig = go.Figure(data=[go.Bar(
        y=op['Operador'], x=op['Cantidad'], orientation='h',
        marker=dict(color='#2ecc71'), text=op['Cantidad'], textposition='outside',
        hovertemplate='<b>%{y}</b><br>Registros: %{x}<extra></extra>'
    )])
    _base(fig, '👥 Top 10 Operadores', 320)
    fig.update_layout(xaxis_title='Cantidad', showlegend=False)
    return fig

def grafico_por_tipo(df):
    """GENERAL: Por tipo de repuesto"""
    if len(df) == 0:
        return go.Figure()
    mt = df['Mantención'].value_counts().reset_index()
    mt.columns = ['Mantención', 'Cantidad']
    colores = [COLORS_REPUESTO.get(m, '#95a5a6') for m in mt['Mantención']]
    fig = go.Figure(data=[go.Pie(
        labels=mt['Mantención'], values=mt['Cantidad'], marker=dict(colors=colores),
        textposition='inside', textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<extra></extra>'
    )])
    _base(fig, '🔧 Distribución por Tipo de Repuesto', 350)
    return fig

def grafico_turnos_operadores(df):
    """INTERMEDIO: Heatmap Turno × Operador"""
    if len(df) == 0:
        return go.Figure()
    pivot = df.pivot_table(index='Turno', columns='Operador', aggfunc='size', fill_value=0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index, colorscale='Blues',
        hovertemplate='<b>Turno %{y}</b><br><b>%{x}</b><br>Registros: %{z}<extra></extra>'
    ))
    _base(fig, '🔥 Heatmap: Turno × Operador', 350)
    return fig

def grafico_heatmap_valvulas_x_tipo(df):
    """ESPECÍFICO: Heatmap Válvulas × Tipo"""
    if len(df) == 0:
        return go.Figure()
    valvulas_todas = list(range(1, 113))
    tipos_todos = ['BLOQUE', 'O-RINGS', 'RESORTE', 'ON/OFF', 'OTRO']
    
    pivot = df.pivot_table(index='Válvula', columns='Mantención', aggfunc='size', fill_value=0)
    for tipo in tipos_todos:
        if tipo not in pivot.columns:
            pivot[tipo] = 0
    for valvula in valvulas_todas:
        if valvula not in pivot.index:
            pivot.loc[valvula] = 0
    pivot = pivot.sort_index()[tipos_todos]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index, colorscale='YlOrRd',
        colorbar=dict(title="Cantidad"),
        hovertemplate='<b>Válvula %{y}</b><br><b>%{x}</b><br>Registros: %{z}<extra></extra>'
    ))
    _base(fig, '🔴 Válvulas (1-112) × Tipo de Repuesto', 800, l=80)
    fig.update_layout(xaxis_title='Tipo de Repuesto', yaxis_title='N° de Válvula', height=800)
    return fig

def grafico_estado_global_valvulas(df):
    """ESPECÍFICO: Estado global de 112 válvulas"""
    valvulas_todas = list(range(1, 113))
    conteos = df['Válvula'].value_counts().reindex(valvulas_todas, fill_value=0).sort_index()
    colores = ['#27ae60' if c == 0 else '#f39c12' if c <= 2 else '#e74c3c' for c in conteos.values]

    fig = go.Figure(data=[go.Bar(
        x=conteos.index, y=conteos.values, marker=dict(color=colores),
        hovertemplate='<b>Válvula %{x}</b><br>Mantenciones: %{y}<extra></extra>',
        showlegend=False
    )])
    _base(fig, '📊 Estado Global: Todas las 112 Válvulas', 350)
    fig.update_layout(xaxis_title='N° de Válvula', yaxis_title='Cantidad de Mantenciones')
    return fig

def grafico_valvula_vs_tipo(df):
    """MUY ESPECÍFICO: Scatter Válvula × Tipo"""
    if len(df) == 0:
        return go.Figure()
    bubble = df.groupby(['Válvula', 'Mantención']).size().reset_index(name='Cantidad')
    colores_map = {tipo: COLORS_REPUESTO.get(tipo, '#95a5a6') for tipo in bubble['Mantención'].unique()}
    
    fig = go.Figure()
    for tipo in sorted(bubble['Mantención'].unique()):
        subset = bubble[bubble['Mantención'] == tipo]
        fig.add_trace(go.Scatter(
            x=subset['Válvula'], y=[tipo]*len(subset), mode='markers',
            marker=dict(size=subset['Cantidad']*4, color=colores_map[tipo], opacity=0.7),
            name=tipo, hovertemplate=f'<b>Válvula %{{x}}</b><br>{tipo}<br>Registros: %{{marker.size}}<extra></extra>'
        ))
    _base(fig, '🟢 Distribución Espacial: Válvula × Tipo de Repuesto', 350)
    fig.update_layout(xaxis_title='N° de Válvula', yaxis_title='Tipo de Repuesto')
    return fig

def crear_tabla_resumen_valvulas(df):
    """MUY ESPECÍFICO: Tabla de 112 válvulas"""
    valvulas_todas = list(range(1, 113))
    resumen_data = []
    
    for valvula in valvulas_todas:
        df_valvula = df[df['Válvula'] == valvula]
        if len(df_valvula) == 0:
            resumen_data.append({'Válvula': valvula, 'Total': 0, 'Tipos': 'SIN REGISTRO', 'Último': '-', 'Operador': '-'})
        else:
            tipos = ', '.join(df_valvula['Mantención'].unique())
            ultimo = df_valvula['Fecha'].max().strftime('%d-%m-%Y')
            resumen_data.append({'Válvula': valvula, 'Total': len(df_valvula), 'Tipos': tipos, 'Último': ultimo, 'Operador': df_valvula.iloc[-1]['Operador']})
    return pd.DataFrame(resumen_data)

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

df = load_data_from_sheets()

st.markdown("""
<div style='text-align:center; margin-bottom:1.2rem;'>
  <h1>🏭 Dashboard Válvulas Krones · Línea 2</h1>
  <p>Llenadora CCU · Monitoreo de 112 Válvulas</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR — FILTROS
# ============================================================================

st.sidebar.markdown("## 🔍 FILTROS")
fecha_min, fecha_max = df['Fecha'].min(), df['Fecha'].max()

col_f1, col_f2 = st.sidebar.columns(2)
with col_f1:
    fecha_inicio = st.date_input("Desde", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
with col_f2:
    fecha_fin = st.date_input("Hasta", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())

turnos_sel = st.sidebar.multiselect("Turnos", sorted(df['Turno'].dropna().unique()), default=sorted(df['Turno'].dropna().unique()))
operadores_sel = st.sidebar.multiselect("Operadores", sorted(df['Operador'].dropna().unique()), default=sorted(df['Operador'].dropna().unique()))
mantencion_sel = st.sidebar.multiselect("Tipos de Repuesto", sorted(df['Mantención'].dropna().unique()), default=sorted(df['Mantención'].dropna().unique()))
valvulas_sel = st.sidebar.multiselect("Válvulas", list(range(1, 113)), default=list(range(1, 113)))

# Aplicar filtros
df_f = df[
    (df['Fecha'].dt.date >= fecha_inicio) &
    (df['Fecha'].dt.date <= fecha_fin) &
    (df['Turno'].isin(turnos_sel)) &
    (df['Operador'].isin(operadores_sel)) &
    (df['Mantención'].isin(mantencion_sel)) &
    (df['Válvula'].isin(valvulas_sel))
].copy()

# ============================================================================
# MÉTRICAS
# ============================================================================

st.markdown("### 📊 KPIs")
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("📝 Total Registros", f"{len(df_f):,}")
with m2:
    st.metric("📅 Días", df_f['Fecha'].nunique())
with m3:
    st.metric("👥 Operadores", df_f['Operador'].nunique())
with m4:
    st.metric("🔧 Válvulas", df_f['Válvula'].nunique())
with m5:
    prom = len(df_f) / max(df_f['Fecha'].nunique(), 1)
    st.metric("📊 Reg/Día", f"{prom:.1f}")

st.markdown("---")

if len(df_f) == 0:
    st.warning("⚠️ Sin datos para los filtros seleccionados.")
else:

    # ════════════════════════════════════════════════════════════════════
    # NIVEL 1: GENERAL
    # ════════════════════════════════════════════════════════════════════
    st.markdown("## 📈 NIVEL 1: ANÁLISIS GENERAL")
    
    st.markdown("### 1.1 Tendencia Temporal")
    st.plotly_chart(grafico_tendencia_temporal(df_f), use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1.2 Registros por Turno")
        st.plotly_chart(grafico_por_turno(df_f), use_container_width=True)
    with col2:
        st.markdown("### 1.3 Top Operadores")
        st.plotly_chart(grafico_por_operador(df_f), use_container_width=True)
    with col3:
        st.markdown("### 1.4 Distribución por Tipo")
        st.plotly_chart(grafico_por_tipo(df_f), use_container_width=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # NIVEL 2: INTERMEDIO
    # ════════════════════════════════════════════════════════════════════
    st.markdown("## 🔥 NIVEL 2: ANÁLISIS INTERMEDIO")

    st.markdown("### 2.1 Heatmap: Turno × Operador")
    st.plotly_chart(grafico_turnos_operadores(df_f), use_container_width=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # NIVEL 3: ESPECÍFICO
    # ════════════════════════════════════════════════════════════════════
    st.markdown("## 🔴 NIVEL 3: ANÁLISIS ESPECÍFICO (112 VÁLVULAS)")

    st.markdown("### 3.1 Heatmap: Válvulas × Tipo de Repuesto")
    st.caption("Matriz de todas las 112 válvulas. El color indica cantidad de registros.")
    st.plotly_chart(grafico_heatmap_valvulas_x_tipo(df_f), use_container_width=True)

    st.markdown("### 3.2 Estado Global de Válvulas")
    st.caption("🟢 Verde=Sin mantenimiento | 🟡 Naranja=1-2 mantenciones | 🔴 Rojo=3+ mantenciones")
    st.plotly_chart(grafico_estado_global_valvulas(df_f), use_container_width=True)

    st.markdown("### 3.3 Distribución Espacial: Válvula × Tipo")
    st.plotly_chart(grafico_valvula_vs_tipo(df_f), use_container_width=True)

    st.markdown("### 3.4 Tabla Resumen: Estado de 112 Válvulas")
    df_resumen = crear_tabla_resumen_valvulas(df_f)
    st.dataframe(df_resumen, use_container_width=True, height=400)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # NIVEL 4: DATOS DETALLADOS
    # ════════════════════════════════════════════════════════════════════
    st.markdown("## 📋 NIVEL 4: DATOS DETALLADOS COMPLETOS")

    if st.checkbox("✅ Mostrar tabla completa de registros"):
        df_show = df_f.copy()
        df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d-%m-%Y')
        st.dataframe(df_show, use_container_width=True, height=500)

    st.markdown("### Descargas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📊 Resumen Válvulas", df_resumen.to_csv(index=False).encode('utf-8'),
            file_name=f"resumen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv"
        )
    with col2:
        st.download_button(
            "📋 Datos Completos", df_f.to_csv(index=False).encode('utf-8'),
            file_name=f"datos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv"
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(f"<div style='text-align:center;opacity:0.6;font-size:0.8rem;'><b>Dashboard v6.0</b> · Streamlit + Plotly · {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</div>", unsafe_allow_html=True)
