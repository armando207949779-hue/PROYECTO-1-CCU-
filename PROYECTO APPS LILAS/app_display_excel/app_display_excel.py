import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(page_title="Visor Excel L2", layout="wide")

st.title("Visor y análisis de archivos Excel")

archivo = st.file_uploader(
    "Sube tu archivo Excel",
    type=["xlsx", "xls"]
)


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


def filtro_checkboxes_vertical(
    titulo,
    valores,
    key_prefix,
    activar_por_defecto=True,
    max_valores=300
):
    st.markdown(f"**{titulo}**")

    valores = [str(v) for v in valores if pd.notna(v)]
    valores = sorted(list(set(valores)))

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

    col_a, col_b = st.columns(2)

    with col_a:
        seleccionar_todos = st.checkbox(
            "Seleccionar todos",
            value=activar_por_defecto,
            key=f"todos_{key_prefix}"
        )

    with col_b:
        limpiar_todos = st.checkbox(
            "Limpiar todos",
            value=False,
            key=f"limpiar_{key_prefix}"
        )

    seleccionados = []

    for valor in valores_mostrar:
        valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)

        checked_default = seleccionar_todos and not limpiar_todos

        marcado = st.checkbox(
            valor,
            value=checked_default,
            key=f"chk_{key_prefix}_{valor_key}"
        )

        if marcado:
            seleccionados.append(valor)

    return seleccionados


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

        st.write(
            f"Filas originales: **{df.shape[0]}** | "
            f"Columnas originales: **{df.shape[1]}**"
        )

        st.sidebar.header("Opciones de visualización")

        with st.sidebar.expander("Columnas a mostrar", expanded=False):
            columnas_visibles = []

            marcar_todas_columnas = st.checkbox(
                "Mostrar todas las columnas",
                value=True,
                key="mostrar_todas_columnas"
            )

            for columna in df.columns:
                mostrar = st.checkbox(
                    columna,
                    value=marcar_todas_columnas,
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
                maquinas_l2 = (
                    df_filtrado["Maquina"]
                    .dropna()
                    .astype(str)
                    .sort_values()
                    .unique()
                    .tolist()
                )

                maquinas_seleccionadas = filtro_checkboxes_vertical(
                    titulo="Máquinas disponibles",
                    valores=maquinas_l2,
                    key_prefix="maquinas_l2",
                    activar_por_defecto=True
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

                    valores = (
                        df_filtrado[columna]
                        .dropna()
                        .astype(str)
                        .sort_values()
                        .unique()
                        .tolist()
                    )

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
                            activar_por_defecto=True
                        )

                        if seleccion:
                            df_filtrado = df_filtrado[
                                df_filtrado[columna]
                                .astype(str)
                                .isin(seleccion)
                            ]
                        else:
                            df_filtrado = df_filtrado.iloc[0:0]

        tab_display, tab_analisis = st.tabs(
            [
                "Display filtrado",
                "Análisis de data filtrada"
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
                st.dataframe(
                    df_filtrado[columnas_visibles],
                    use_container_width=True,
                    height=700
                )

                csv = df_filtrado[columnas_visibles].to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    label="Descargar datos filtrados en CSV",
                    data=csv,
                    file_name="datos_filtrados_L2.csv",
                    mime="text/csv"
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

    except ImportError:
        st.error("Falta instalar alguna librería necesaria.")
        st.code("pip install streamlit pandas openpyxl plotly")

    except Exception as e:
        st.error("No se pudo cargar el archivo Excel.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para mostrar el display.")
