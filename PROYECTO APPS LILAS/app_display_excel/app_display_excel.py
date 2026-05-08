import streamlit as st
import pandas as pd
import re
import plotly.express as px
from io import BytesIO
import zipfile
import os
from pathlib import Path
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Visor Excel L2",
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
# ENCABEZADO CON LOGO
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
            margin-top: 1.6rem;
            margin-bottom: 1.1rem;
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
            Visor, análisis, fotos e IDs agrupados<br>
            Estándares Visuales LILA
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

archivo = st.file_uploader(
    "Sube tu archivo Excel",
    type=["xlsx", "xls"]
)


# =====================================================
# FUNCIONES
# =====================================================
def filtrar_texto(df_base, columna, texto, tipo_filtro):
    if texto is None or str(texto).strip() == "":
        return df_base

    serie_texto = df_base[columna].astype(str).str.strip()
    texto_limpio = str(texto).strip()

    if tipo_filtro == "Contiene":
        patron = re.escape(texto_limpio)
        return df_base[
            serie_texto.str.contains(
                patron,
                case=False,
                na=False,
                regex=True
            )
        ]

    if tipo_filtro == "Contiene palabra exacta":
        patron = (
            rf"(?<![A-Za-z0-9])"
            rf"{re.escape(texto_limpio)}"
            rf"(?![A-Za-z0-9])"
        )
        return df_base[
            serie_texto.str.contains(
                patron,
                case=False,
                na=False,
                regex=True
            )
        ]

    if tipo_filtro == "Igual a":
        return df_base[
            serie_texto.str.lower() == texto_limpio.lower()
        ]

    if tipo_filtro == "Empieza con":
        return df_base[
            serie_texto.str.lower().str.startswith(texto_limpio.lower())
        ]

    if tipo_filtro == "Termina con":
        return df_base[
            serie_texto.str.lower().str.endswith(texto_limpio.lower())
        ]

    return df_base


def limpiar_nombre_archivo(texto):
    texto = str(texto).strip()
    texto = re.sub(r'[\\/*?:"<>|]', "_", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:100]


def dataframe_a_excel_bytes(df_descarga, nombre_hoja="Datos"):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        nombre_hoja = nombre_hoja[:31]

        df_descarga.to_excel(
            writer,
            index=False,
            sheet_name=nombre_hoja
        )

        worksheet = writer.sheets[nombre_hoja]

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                valor = str(cell.value) if cell.value is not None else ""
                max_length = max(max_length, len(valor))

            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 45)

    output.seek(0)
    return output.getvalue()


def crear_zip_por_maquina(df_descarga):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        maquinas = (
            df_descarga["Maquina"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
        )

        for maquina in maquinas:
            df_maquina = df_descarga[
                df_descarga["Maquina"].astype(str) == str(maquina)
            ]

            nombre_limpio = limpiar_nombre_archivo(maquina)
            nombre_excel = f"{nombre_limpio}.xlsx"

            excel_bytes = dataframe_a_excel_bytes(
                df_maquina,
                nombre_hoja="Datos"
            )

            zip_file.writestr(nombre_excel, excel_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def filtro_checkboxes_vertical(
    titulo,
    valores,
    key_prefix,
    activar_por_defecto=True,
    max_valores=300,
    conteos=None
):
    st.markdown(f"**{titulo}**")

    valores = [str(v) for v in valores if pd.notna(v)]

    texto_buscar = st.text_input(
        "Buscar en listado",
        key=f"buscar_{key_prefix}"
    )

    if texto_buscar:
        valores_mostrar = [
            v for v in valores
            if texto_buscar.lower() in v.lower()
        ]
    else:
        valores_mostrar = valores

    if len(valores_mostrar) > max_valores:
        st.warning(
            f"Hay {len(valores_mostrar)} valores. "
            f"Se muestran solo los primeros {max_valores}. "
            "Usa el buscador para reducir el listado."
        )
        valores_mostrar = valores_mostrar[:max_valores]

    seleccionar_todos = st.checkbox(
        "Seleccionar todos",
        value=activar_por_defecto,
        key=f"todos_{key_prefix}"
    )

    seleccionados = []

    for valor in valores_mostrar:
        valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)

        if conteos is not None:
            etiqueta = f"{valor} ({conteos.get(valor, 0)})"
        else:
            etiqueta = valor

        marcado = st.checkbox(
            etiqueta,
            value=seleccionar_todos,
            key=f"chk_{key_prefix}_{valor_key}"
        )

        if marcado:
            seleccionados.append(valor)

    return seleccionados


def crear_nombre_foto(id_estandar, maquina, nombre_original):
    extension = os.path.splitext(nombre_original)[1].lower()

    id_limpio = limpiar_nombre_archivo(id_estandar)
    maquina_limpia = limpiar_nombre_archivo(maquina)

    nombre = f"{id_limpio}_{maquina_limpia}{extension}"

    return nombre


def crear_zip_fotos_por_maquina(fotos_configuradas):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in fotos_configuradas:
            archivo_foto = item["archivo"]
            id_estandar = item["id_estandar"]
            maquina = item["maquina"]

            carpeta_maquina = limpiar_nombre_archivo(maquina)

            nombre_foto = crear_nombre_foto(
                id_estandar=id_estandar,
                maquina=maquina,
                nombre_original=archivo_foto.name
            )

            ruta_dentro_zip = f"{carpeta_maquina}/{nombre_foto}"

            zip_file.writestr(
                ruta_dentro_zip,
                archivo_foto.getvalue()
            )

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def tabla_valores_originales(df_base, columna):
    if columna == "Id Estándar":
        tabla = df_base[["Id Estándar", "Maquina"]].copy()
        tabla = tabla.rename(columns={"Id Estándar": "Valor original"})
    elif columna == "Maquina":
        tabla = df_base[["Id Estándar", "Maquina"]].copy()
        tabla = tabla.rename(columns={"Maquina": "Valor original"})
    else:
        tabla = df_base[["Id Estándar", "Maquina", columna]].copy()
        tabla = tabla.rename(columns={columna: "Valor original"})

    tabla = tabla.loc[:, ~tabla.columns.duplicated()]
    return tabla


def tabla_valores_originales_simple(df_base, columna):
    if columna == "Id Estándar":
        tabla = df_base[["Id Estándar"]].copy()
        tabla = tabla.rename(columns={"Id Estándar": "Valor original"})
    else:
        tabla = df_base[["Id Estándar", columna]].copy()
        tabla = tabla.rename(columns={columna: "Valor original"})

    tabla = tabla.loc[:, ~tabla.columns.duplicated()]
    return tabla


# =====================================================
# APP PRINCIPAL
# =====================================================
if archivo is not None:
    try:
        excel = pd.ExcelFile(archivo, engine="openpyxl")

        hoja = st.selectbox(
            "Selecciona una hoja",
            excel.sheet_names
        )

        df = pd.read_excel(
            archivo,
            sheet_name=hoja,
            engine="openpyxl"
        )

        df.columns = [
            str(col).strip() if str(col) != "nan" else f"Columna_{i + 1}"
            for i, col in enumerate(df.columns)
        ]

        if "Maquina" not in df.columns:
            st.error("No existe la columna 'Maquina' en el archivo Excel.")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
            st.stop()

        if "Id Estándar" not in df.columns:
            st.error("No existe la columna 'Id Estándar' en el archivo Excel.")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
            st.stop()

        st.write(
            f"Filas originales: **{df.shape[0]}** | "
            f"Columnas originales: **{df.shape[1]}**"
        )

        st.sidebar.header("Opciones de visualización")

        with st.sidebar.expander("Columnas a mostrar", expanded=False):
            columnas_visibles = []

            mostrar_todas_columnas = st.checkbox(
                "Mostrar todas las columnas",
                value=True,
                key="mostrar_todas_columnas"
            )

            for columna in df.columns:
                mostrar = st.checkbox(
                    columna,
                    value=mostrar_todas_columnas,
                    key=f"mostrar_columna_{columna}"
                )

                if mostrar:
                    columnas_visibles.append(columna)

        st.sidebar.header("Filtro predeterminado L2")

        aplicar_filtro_l2 = st.sidebar.checkbox(
            "Aplicar filtro predeterminado: Maquina contiene L2",
            value=True
        )

        texto_l2 = st.sidebar.text_input(
            "Texto predeterminado",
            value="L2"
        )

        tipo_l2 = st.sidebar.selectbox(
            "Tipo de filtro predeterminado",
            options=[
                "Contiene palabra exacta",
                "Contiene",
                "Igual a",
                "Empieza con",
                "Termina con"
            ],
            index=0
        )

        df_filtrado = df.copy()

        if aplicar_filtro_l2:
            df_filtrado = filtrar_texto(
                df_filtrado,
                "Maquina",
                texto_l2,
                tipo_l2
            )

        filas_solo_l2 = df_filtrado.shape[0]

        st.sidebar.info(
            f"Filas después del filtro L2: {filas_solo_l2}"
        )

        st.sidebar.header("Máquinas dentro de L2")

        usar_filtro_maquinas = st.sidebar.checkbox(
            "Filtrar por máquinas específicas",
            value=False
        )

        if usar_filtro_maquinas:
            with st.sidebar.expander("Listado de máquinas L2", expanded=True):
                conteo_maquinas_l2 = (
                    df_filtrado["Maquina"]
                    .dropna()
                    .astype(str)
                    .value_counts()
                )

                maquinas_l2 = conteo_maquinas_l2.index.tolist()

                maquinas_seleccionadas = filtro_checkboxes_vertical(
                    titulo="Máquinas disponibles",
                    valores=maquinas_l2,
                    key_prefix="maquinas_l2",
                    activar_por_defecto=True,
                    conteos=conteo_maquinas_l2
                )

            if maquinas_seleccionadas:
                df_filtrado = df_filtrado[
                    df_filtrado["Maquina"]
                    .astype(str)
                    .isin(maquinas_seleccionadas)
                ]
            else:
                df_filtrado = df_filtrado.iloc[0:0]
        else:
            st.sidebar.caption(
                "No se está aplicando filtro por máquinas específicas."
            )

        st.sidebar.header("Buscador general")

        busqueda_general = st.sidebar.text_input(
            "Buscar en toda la tabla"
        )

        if busqueda_general:
            patron_general = re.escape(busqueda_general.strip())

            df_filtrado = df_filtrado[
                df_filtrado.astype(str).apply(
                    lambda fila: fila.str.contains(
                        patron_general,
                        case=False,
                        na=False,
                        regex=True
                    ).any(),
                    axis=1
                )
            ]

        st.sidebar.header("Filtros adicionales")

        with st.sidebar.expander("Seleccionar columnas para filtrar", expanded=False):
            columnas_para_filtrar = []

            for columna in df.columns:
                usar_columna = st.checkbox(
                    columna,
                    value=False,
                    key=f"usar_filtro_columna_{columna}"
                )

                if usar_columna:
                    columnas_para_filtrar.append(columna)

        opciones_texto = [
            "Contiene",
            "Contiene palabra exacta",
            "Igual a",
            "Empieza con",
            "Termina con"
        ]

        for columna in columnas_para_filtrar:
            with st.sidebar.expander(f"Filtrar: {columna}", expanded=True):
                serie_actual = df_filtrado[columna]

                serie_fecha = pd.to_datetime(
                    serie_actual,
                    errors="coerce"
                )

                total_no_nulos = len(serie_actual.dropna())

                es_fecha = (
                    total_no_nulos > 0
                    and serie_fecha.notna().sum() >= total_no_nulos * 0.7
                )

                if pd.api.types.is_numeric_dtype(serie_actual):
                    minimo = serie_actual.min()
                    maximo = serie_actual.max()

                    if pd.notna(minimo) and pd.notna(maximo):
                        minimo = float(minimo)
                        maximo = float(maximo)

                        if minimo != maximo:
                            rango = st.slider(
                                "Rango",
                                min_value=minimo,
                                max_value=maximo,
                                value=(minimo, maximo),
                                key=f"rango_adicional_{columna}"
                            )

                            df_filtrado = df_filtrado[
                                (df_filtrado[columna] >= rango[0])
                                & (df_filtrado[columna] <= rango[1])
                            ]
                        else:
                            st.caption(f"Valor único: {minimo}")
                    else:
                        st.caption("Sin valores numéricos disponibles.")

                elif es_fecha:
                    fechas_validas = pd.to_datetime(
                        df_filtrado[columna],
                        errors="coerce"
                    ).dropna()

                    if not fechas_validas.empty:
                        fecha_min = fechas_validas.min().date()
                        fecha_max = fechas_validas.max().date()

                        rango_fechas = st.date_input(
                            "Rango de fechas",
                            value=(fecha_min, fecha_max),
                            min_value=fecha_min,
                            max_value=fecha_max,
                            key=f"fecha_adicional_{columna}"
                        )

                        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                            inicio, fin = rango_fechas

                            fechas_columna = pd.to_datetime(
                                df_filtrado[columna],
                                errors="coerce"
                            )

                            df_filtrado = df_filtrado[
                                (fechas_columna.dt.date >= inicio)
                                & (fechas_columna.dt.date <= fin)
                            ]
                    else:
                        st.caption("Sin fechas disponibles.")

                else:
                    tipo_filtro_texto = st.selectbox(
                        "Tipo de filtro de texto",
                        options=opciones_texto,
                        index=0,
                        key=f"tipo_texto_adicional_{columna}"
                    )

                    texto = st.text_input(
                        "Texto a filtrar",
                        key=f"texto_adicional_{columna}"
                    )

                    if texto:
                        df_filtrado = filtrar_texto(
                            df_filtrado,
                            columna,
                            texto,
                            tipo_filtro_texto
                        )

                    valores_con_conteo = (
                        df_filtrado[columna]
                        .dropna()
                        .astype(str)
                        .value_counts()
                    )

                    valores = valores_con_conteo.index.tolist()

                    aplicar_listado = st.checkbox(
                        "Aplicar filtro por listado con checkboxes",
                        value=False,
                        key=f"aplicar_listado_{columna}"
                    )

                    if aplicar_listado:
                        seleccion = filtro_checkboxes_vertical(
                            titulo=f"Valores de {columna}",
                            valores=valores,
                            key_prefix=f"valores_{columna}",
                            activar_por_defecto=True,
                            conteos=valores_con_conteo
                        )

                        if seleccion:
                            df_filtrado = df_filtrado[
                                df_filtrado[columna]
                                .astype(str)
                                .isin(seleccion)
                            ]
                        else:
                            df_filtrado = df_filtrado.iloc[0:0]

        tab_display, tab_analisis, tab_fotos, tab_id_agrupado = st.tabs(
            [
                "Display filtrado",
                "Análisis de data filtrada",
                "Fotos por ID / Máquina",
                "Crear ID agrupado"
            ]
        )

        with tab_display:
            st.subheader("Datos filtrados")

            st.write(
                f"Filas con solo filtro L2: **{filas_solo_l2}**"
            )

            st.write(
                f"Filas filtradas finales: **{df_filtrado.shape[0]}** | "
                f"Columnas mostradas: **{len(columnas_visibles)}**"
            )

            if columnas_visibles:
                df_descarga = df_filtrado[columnas_visibles].copy()

                st.dataframe(
                    df_descarga,
                    use_container_width=True,
                    height=700
                )

                st.subheader("Descargas")

                col_descarga_1, col_descarga_2 = st.columns(2)

                with col_descarga_1:
                    excel_completo = dataframe_a_excel_bytes(
                        df_descarga,
                        nombre_hoja="Datos filtrados"
                    )

                    st.download_button(
                        label="Descargar data filtrada completa en Excel",
                        data=excel_completo,
                        file_name="datos_filtrados_completo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col_descarga_2:
                    if "Maquina" in df_descarga.columns:
                        zip_maquinas = crear_zip_por_maquina(df_descarga)

                        st.download_button(
                            label="Descargar Excels separados por máquina",
                            data=zip_maquinas,
                            file_name="datos_filtrados_por_maquina.zip",
                            mime="application/zip"
                        )
                    else:
                        st.warning(
                            "Para descargar por máquina, la columna 'Maquina' debe estar visible."
                        )

            else:
                st.warning("Selecciona al menos una columna para mostrar.")

        with tab_analisis:
            st.subheader("Análisis de la data filtrada")

            if df_filtrado.empty:
                st.warning("No hay datos para analizar con los filtros actuales.")
            else:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Filas filtradas", df_filtrado.shape[0])

                with col2:
                    st.metric("Columnas", df_filtrado.shape[1])

                with col3:
                    porcentaje = (df_filtrado.shape[0] / df.shape[0]) * 100
                    st.metric("% del total original", f"{porcentaje:.2f}%")

                st.divider()

                st.subheader("Histograma")

                columnas_numericas = df_filtrado.select_dtypes(
                    include=["number"]
                ).columns.tolist()

                if columnas_numericas:
                    columna_histograma = st.selectbox(
                        "Selecciona columna numérica para histograma",
                        options=columnas_numericas,
                        index=0
                    )

                    bins = st.slider(
                        "Cantidad de intervalos",
                        min_value=5,
                        max_value=50,
                        value=15
                    )

                    fig_hist = px.histogram(
                        df_filtrado,
                        x=columna_histograma,
                        nbins=bins,
                        title=f"Histograma de {columna_histograma}"
                    )

                    fig_hist.update_layout(
                        xaxis_title=columna_histograma,
                        yaxis_title="Cantidad",
                        bargap=0.05
                    )

                    st.plotly_chart(
                        fig_hist,
                        use_container_width=True
                    )
                else:
                    st.info("No hay columnas numéricas disponibles para histograma.")

                st.divider()

                st.subheader("Gráfico de barras verticales porcentuales")

                columnas_categoricas = [
                    col for col in df_filtrado.columns
                    if col not in columnas_numericas
                ]

                if columnas_categoricas:
                    columna_barra = st.selectbox(
                        "Selecciona columna categórica",
                        options=columnas_categoricas,
                        index=columnas_categoricas.index("Maquina")
                        if "Maquina" in columnas_categoricas
                        else 0
                    )

                    top_n = st.slider(
                        "Mostrar Top N categorías",
                        min_value=3,
                        max_value=30,
                        value=10
                    )

                    conteo = (
                        df_filtrado[columna_barra]
                        .fillna("Sin dato")
                        .astype(str)
                        .value_counts()
                        .reset_index()
                    )

                    conteo.columns = [columna_barra, "Cantidad"]

                    conteo["Porcentaje"] = (
                        conteo["Cantidad"] / conteo["Cantidad"].sum()
                    ) * 100

                    conteo_top = conteo.head(top_n)

                    fig_barra = px.bar(
                        conteo_top,
                        x=columna_barra,
                        y="Porcentaje",
                        text=conteo_top["Porcentaje"].map(lambda x: f"{x:.1f}%"),
                        title=f"Distribución porcentual por {columna_barra}"
                    )

                    fig_barra.update_layout(
                        xaxis_title=columna_barra,
                        yaxis_title="Porcentaje (%)",
                        xaxis_tickangle=-45
                    )

                    fig_barra.update_traces(
                        textposition="outside"
                    )

                    st.plotly_chart(
                        fig_barra,
                        use_container_width=True
                    )

                    st.subheader("Tabla de frecuencias")

                    st.dataframe(
                        conteo,
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.info("No hay columnas categóricas disponibles.")

                st.divider()

                st.subheader("Resumen de columnas numéricas")

                if columnas_numericas:
                    resumen_numerico = df_filtrado[columnas_numericas].describe().T

                    st.dataframe(
                        resumen_numerico,
                        use_container_width=True
                    )
                else:
                    st.info("No hay columnas numéricas para resumir.")

        with tab_fotos:
            st.subheader("Subir fotos y asociarlas con ID / Máquina")

            st.write(
                "Cada foto se renombra automáticamente con el formato "
                "**ID_Maquina.extensión** y se descarga en un ZIP con carpetas por máquina."
            )

            if df_filtrado.empty:
                st.warning("No hay datos filtrados disponibles para asociar fotos.")
            else:
                df_ids = df_filtrado.copy()

                df_ids["Id Estándar"] = df_ids["Id Estándar"].astype(str)
                df_ids["Maquina"] = df_ids["Maquina"].astype(str)

                columnas_info = ["Id Estándar", "Maquina"]

                if "Detalle Maquina" in df_ids.columns:
                    columnas_info.append("Detalle Maquina")

                if "Descripción Estándar Visual" in df_ids.columns:
                    columnas_info.append("Descripción Estándar Visual")

                if "Descripción Actividad" in df_ids.columns:
                    columnas_info.append("Descripción Actividad")

                df_opciones = (
                    df_ids[columnas_info]
                    .drop_duplicates()
                    .sort_values(["Maquina", "Id Estándar"])
                    .reset_index(drop=True)
                )

                st.write(
                    f"IDs disponibles según filtros actuales: "
                    f"**{df_opciones.shape[0]}**"
                )

                with st.expander("Ver IDs disponibles", expanded=False):
                    st.dataframe(
                        df_opciones,
                        use_container_width=True,
                        height=350
                    )

                fotos_subidas = st.file_uploader(
                    "Sube una o varias fotos",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True
                )

                if fotos_subidas:
                    st.subheader("Asociar cada foto")

                    maquinas_disponibles = (
                        df_opciones["Maquina"]
                        .dropna()
                        .astype(str)
                        .value_counts()
                        .index
                        .tolist()
                    )

                    fotos_configuradas = []

                    for idx, foto in enumerate(fotos_subidas):
                        st.divider()

                        col_foto, col_config = st.columns([1, 2])

                        with col_foto:
                            st.image(
                                foto,
                                caption=foto.name,
                                use_container_width=True
                            )

                        with col_config:
                            maquina_seleccionada = st.selectbox(
                                f"Selecciona máquina para: {foto.name}",
                                options=maquinas_disponibles,
                                key=f"maquina_foto_{idx}_{foto.name}"
                            )

                            df_ids_maquina = df_opciones[
                                df_opciones["Maquina"].astype(str)
                                == str(maquina_seleccionada)
                            ].copy()

                            ids_disponibles = (
                                df_ids_maquina["Id Estándar"]
                                .astype(str)
                                .sort_values()
                                .unique()
                                .tolist()
                            )

                            id_seleccionado = st.selectbox(
                                f"Selecciona ID para: {foto.name}",
                                options=ids_disponibles,
                                key=f"id_foto_{idx}_{foto.name}"
                            )

                            fila_id = df_ids_maquina[
                                df_ids_maquina["Id Estándar"].astype(str)
                                == str(id_seleccionado)
                            ].iloc[0]

                            nombre_final = crear_nombre_foto(
                                id_estandar=id_seleccionado,
                                maquina=maquina_seleccionada,
                                nombre_original=foto.name
                            )

                            carpeta_final = limpiar_nombre_archivo(
                                maquina_seleccionada
                            )

                            st.write(f"**ID seleccionado:** {id_seleccionado}")
                            st.write(f"**Máquina seleccionada:** {maquina_seleccionada}")
                            st.write(f"**Carpeta:** `{carpeta_final}/`")
                            st.write(f"**Nombre final:** `{nombre_final}`")

                            if "Detalle Maquina" in df_ids_maquina.columns:
                                st.write(
                                    f"**Detalle Máquina:** "
                                    f"{fila_id.get('Detalle Maquina', '')}"
                                )

                            if "Descripción Estándar Visual" in df_ids_maquina.columns:
                                st.write(
                                    f"**Descripción Estándar Visual:** "
                                    f"{fila_id.get('Descripción Estándar Visual', '')}"
                                )

                            if "Descripción Actividad" in df_ids_maquina.columns:
                                st.write(
                                    f"**Descripción Actividad:** "
                                    f"{fila_id.get('Descripción Actividad', '')}"
                                )

                            fotos_configuradas.append(
                                {
                                    "archivo": foto,
                                    "id_estandar": id_seleccionado,
                                    "maquina": maquina_seleccionada,
                                    "nombre_final": nombre_final,
                                    "carpeta": carpeta_final
                                }
                            )

                    st.subheader("Resumen de fotos configuradas")

                    resumen_fotos = pd.DataFrame(
                        [
                            {
                                "Foto original": item["archivo"].name,
                                "Id Estándar": item["id_estandar"],
                                "Maquina": item["maquina"],
                                "Carpeta": item["carpeta"],
                                "Nombre final": item["nombre_final"]
                            }
                            for item in fotos_configuradas
                        ]
                    )

                    st.dataframe(
                        resumen_fotos,
                        use_container_width=True
                    )

                    zip_fotos = crear_zip_fotos_por_maquina(fotos_configuradas)

                    st.download_button(
                        label="Descargar fotos renombradas por máquina en ZIP",
                        data=zip_fotos,
                        file_name="fotos_por_maquina.zip",
                        mime="application/zip"
                    )

                else:
                    st.info("Sube fotos para asociarlas con una máquina y un ID.")

        with tab_id_agrupado:
            st.subheader("Crear ID agrupado desde varios IDs existentes")

            st.write(
                "Selecciona una máquina y uno o más IDs. "
                "La app mostrará la información original de cada ID por columna. "
                "El usuario debe completar manualmente el valor final agrupado. "
                "En tiempo estimado se muestra la suma como ayuda."
            )

            if df_filtrado.empty:
                st.warning("No hay datos filtrados disponibles para crear un ID agrupado.")
            else:
                df_base_agrupado = df_filtrado.copy()

                df_base_agrupado["Id Estándar"] = df_base_agrupado["Id Estándar"].astype(str)
                df_base_agrupado["Maquina"] = df_base_agrupado["Maquina"].astype(str)

                maquinas_disponibles_agrupado = (
                    df_base_agrupado["Maquina"]
                    .dropna()
                    .astype(str)
                    .value_counts()
                    .index
                    .tolist()
                )

                maquina_agrupada = st.selectbox(
                    "Selecciona la máquina",
                    options=maquinas_disponibles_agrupado,
                    key="maquina_id_agrupado"
                )

                df_maquina_agrupada = df_base_agrupado[
                    df_base_agrupado["Maquina"].astype(str) == str(maquina_agrupada)
                ].copy()

                ids_disponibles_agrupado = (
                    df_maquina_agrupada["Id Estándar"]
                    .dropna()
                    .astype(str)
                    .sort_values()
                    .unique()
                    .tolist()
                )

                ids_seleccionados = st.multiselect(
                    "Selecciona los IDs que quieres agrupar",
                    options=ids_disponibles_agrupado,
                    default=[]
                )

                if ids_seleccionados:
                    df_ids_seleccionados = df_maquina_agrupada[
                        df_maquina_agrupada["Id Estándar"].astype(str).isin(ids_seleccionados)
                    ].copy()

                    st.write(
                        f"IDs seleccionados: **{len(ids_seleccionados)}** | "
                        f"Registros encontrados: **{df_ids_seleccionados.shape[0]}**"
                    )

                    with st.expander("Ver registros originales seleccionados", expanded=True):
                        st.dataframe(
                            df_ids_seleccionados,
                            use_container_width=True,
                            height=350
                        )

                    st.divider()

                    st.subheader("Comparación por columna")

                    for columna in df_ids_seleccionados.columns:
                        with st.expander(f"Columna: {columna}", expanded=False):
                            tabla_columna = tabla_valores_originales(
                                df_ids_seleccionados,
                                columna
                            )

                            st.dataframe(
                                tabla_columna,
                                use_container_width=True
                            )

                    st.divider()

                    st.subheader("Completar información final del ID agrupado")

                    st.write(
                        "Escribe el valor final que tendrá el nuevo ID agrupado. "
                        "Los campos aparecen vacíos para que el usuario decida el contenido final, "
                        "excepto el tiempo estimado, donde se muestra la suma como ayuda."
                    )

                    valores_finales = {}

                    ids_unidos = "_".join(ids_seleccionados)

                    valores_finales["Id Estándar"] = st.text_input(
                        "Id Estándar final",
                        value=f"AGRUPADO_{ids_unidos}",
                        key="final_id_estandar"
                    )

                    valores_finales["Maquina"] = st.text_input(
                        "Maquina final",
                        value=maquina_agrupada,
                        key="final_maquina"
                    )

                    columnas_editables = [
                        col for col in df_ids_seleccionados.columns
                        if col not in ["Id Estándar", "Maquina"]
                    ]

                    columnas_text_area = [
                        "Descripción Estándar Visual",
                        "Descripción Actividad",
                        "Epp",
                        "Materiales/Herramientas"
                    ]

                    for columna in columnas_editables:
                        st.markdown(f"### {columna}")

                        with st.expander(f"Ver valores originales de {columna}", expanded=False):
                            tabla_columna = tabla_valores_originales_simple(
                                df_ids_seleccionados,
                                columna
                            )

                            st.dataframe(
                                tabla_columna,
                                use_container_width=True
                            )

                        if columna == "Tiempo Estimado (en Minutos)":
                            tiempos = pd.to_numeric(
                                df_ids_seleccionados[columna],
                                errors="coerce"
                            ).dropna()

                            suma_tiempos = float(tiempos.sum()) if not tiempos.empty else 0.0

                            st.info(
                                f"Suma sugerida de tiempos seleccionados: {suma_tiempos:.2f} minutos"
                            )

                            valores_finales[columna] = st.number_input(
                                f"Valor final para {columna}",
                                min_value=0.0,
                                value=suma_tiempos,
                                step=1.0,
                                key=f"final_{columna}"
                            )

                        elif columna in columnas_text_area:
                            valores_finales[columna] = st.text_area(
                                f"Valor final para {columna}",
                                value="",
                                height=120,
                                key=f"final_{columna}"
                            )

                        else:
                            valores_finales[columna] = st.text_input(
                                f"Valor final para {columna}",
                                value="",
                                key=f"final_{columna}"
                            )

                    st.divider()

                    st.subheader("Vista previa del nuevo ID agrupado")

                    df_id_agrupado = pd.DataFrame([valores_finales])

                    columnas_ordenadas = [
                        col for col in df_filtrado.columns
                        if col in df_id_agrupado.columns
                    ]

                    df_id_agrupado = df_id_agrupado[columnas_ordenadas]

                    st.dataframe(
                        df_id_agrupado,
                        use_container_width=True
                    )

                    st.subheader("Descargar nuevo ID agrupado")

                    excel_id_agrupado = dataframe_a_excel_bytes(
                        df_id_agrupado,
                        nombre_hoja="ID agrupado"
                    )

                    nombre_archivo_agrupado = limpiar_nombre_archivo(
                        f"{valores_finales['Id Estándar']}_{valores_finales['Maquina']}"
                    )

                    st.download_button(
                        label="Descargar solo el nuevo ID agrupado",
                        data=excel_id_agrupado,
                        file_name=f"{nombre_archivo_agrupado}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    st.divider()

                    st.subheader("Descargar data filtrada con el ID agrupado")

                    incluir_originales = st.checkbox(
                        "Mantener también los IDs originales seleccionados",
                        value=False
                    )

                    if incluir_originales:
                        df_final_con_agrupado = pd.concat(
                            [df_filtrado, df_id_agrupado],
                            ignore_index=True
                        )
                    else:
                        df_sin_ids_originales = df_filtrado[
                            ~(
                                (df_filtrado["Maquina"].astype(str) == str(maquina_agrupada))
                                &
                                (df_filtrado["Id Estándar"].astype(str).isin(ids_seleccionados))
                            )
                        ].copy()

                        df_final_con_agrupado = pd.concat(
                            [df_sin_ids_originales, df_id_agrupado],
                            ignore_index=True
                        )

                    st.write(
                        f"Filas finales con ID agrupado: **{df_final_con_agrupado.shape[0]}**"
                    )

                    with st.expander("Ver data final con ID agrupado", expanded=False):
                        st.dataframe(
                            df_final_con_agrupado,
                            use_container_width=True,
                            height=400
                        )

                    excel_final_agrupado = dataframe_a_excel_bytes(
                        df_final_con_agrupado,
                        nombre_hoja="Data final"
                    )

                    st.download_button(
                        label="Descargar data filtrada con ID agrupado",
                        data=excel_final_agrupado,
                        file_name="data_filtrada_con_id_agrupado.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                else:
                    st.info("Selecciona uno o más IDs para crear un ID agrupado.")

    except ImportError:
        st.error("Falta instalar alguna librería necesaria.")
        st.code("pip install streamlit pandas openpyxl plotly")

    except Exception as e:
        st.error("No se pudo cargar el archivo Excel.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para mostrar el display.")
