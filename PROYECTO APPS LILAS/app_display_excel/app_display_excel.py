import streamlit as st
import pandas as pd

st.set_page_config(page_title="Visor y filtro de Excel", layout="wide")

st.title("Visor y filtro de archivos Excel")

archivo = st.file_uploader(
    "Sube tu archivo Excel",
    type=["xlsx", "xls"]
)

if archivo is not None:
    try:
        excel = pd.ExcelFile(archivo, engine="openpyxl")
        hoja = st.selectbox("Selecciona una hoja", excel.sheet_names)

        df = pd.read_excel(archivo, sheet_name=hoja, engine="openpyxl")

        # Mantener todas las columnas, incluso si tienen nombres vacíos
        df.columns = [str(col) if str(col) != "nan" else f"Columna_{i+1}" for i, col in enumerate(df.columns)]

        st.write(f"Filas originales: **{df.shape[0]}** | Columnas: **{df.shape[1]}**")

        st.sidebar.header("Opciones de visualización")

        columnas_visibles = st.sidebar.multiselect(
            "Columnas a mostrar",
            options=list(df.columns),
            default=list(df.columns)
        )

        st.sidebar.header("Filtros")

        df_filtrado = df.copy()

        # Buscador general
        busqueda_general = st.sidebar.text_input("Buscar en toda la tabla")

        if busqueda_general:
            df_filtrado = df_filtrado[
                df_filtrado.astype(str).apply(
                    lambda fila: fila.str.contains(busqueda_general, case=False, na=False).any(),
                    axis=1
                )
            ]

        # Filtros por columna
        columnas_para_filtrar = st.sidebar.multiselect(
            "Selecciona columnas para filtrar",
            options=list(df.columns)
        )

        for columna in columnas_para_filtrar:
            st.sidebar.markdown(f"**{columna}**")

            serie = df_filtrado[columna]

            # Intentar detectar fechas
            serie_fecha = pd.to_datetime(serie, errors="coerce")
            es_fecha = serie_fecha.notna().sum() > 0 and serie_fecha.notna().sum() >= len(serie.dropna()) * 0.7

            # Filtro para columnas numéricas
            if pd.api.types.is_numeric_dtype(serie):
                minimo = float(serie.min()) if pd.notna(serie.min()) else 0.0
                maximo = float(serie.max()) if pd.notna(serie.max()) else 0.0

                if minimo != maximo:
                    rango = st.sidebar.slider(
                        f"Rango de {columna}",
                        min_value=minimo,
                        max_value=maximo,
                        value=(minimo, maximo)
                    )

                    df_filtrado = df_filtrado[
                        (df_filtrado[columna] >= rango[0]) &
                        (df_filtrado[columna] <= rango[1])
                    ]

            # Filtro para columnas tipo fecha
            elif es_fecha:
                fechas_validas = serie_fecha.dropna()

                fecha_min = fechas_validas.min().date()
                fecha_max = fechas_validas.max().date()

                rango_fechas = st.sidebar.date_input(
                    f"Rango de fechas de {columna}",
                    value=(fecha_min, fecha_max),
                    min_value=fecha_min,
                    max_value=fecha_max
                )

                if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                    inicio, fin = rango_fechas

                    fechas_columna = pd.to_datetime(df_filtrado[columna], errors="coerce")

                    df_filtrado = df_filtrado[
                        (fechas_columna.dt.date >= inicio) &
                        (fechas_columna.dt.date <= fin)
                    ]

            # Filtro para texto / categorías
            else:
                valores = (
                    df_filtrado[columna]
                    .dropna()
                    .astype(str)
                    .sort_values()
                    .unique()
                    .tolist()
                )

                usar_busqueda = st.sidebar.text_input(
                    f"Contiene texto en {columna}",
                    key=f"texto_{columna}"
                )

                if usar_busqueda:
                    df_filtrado = df_filtrado[
                        df_filtrado[columna]
                        .astype(str)
                        .str.contains(usar_busqueda, case=False, na=False)
                    ]

                if len(valores) <= 500:
                    seleccion = st.sidebar.multiselect(
                        f"Valores de {columna}",
                        options=valores,
                        default=valores,
                        key=f"valores_{columna}"
                    )

                    df_filtrado = df_filtrado[
                        df_filtrado[columna].astype(str).isin(seleccion)
                    ]
                else:
                    st.sidebar.caption(
                        f"{columna} tiene más de 500 valores únicos. Usa el filtro de texto."
                    )

        st.subheader("Datos filtrados")
        st.write(f"Filas filtradas: **{df_filtrado.shape[0]}**")

        if columnas_visibles:
            st.dataframe(
                df_filtrado[columnas_visibles],
                use_container_width=True,
                height=650
            )
        else:
            st.warning("Selecciona al menos una columna para mostrar.")

        # Descargar resultado filtrado
        csv = df_filtrado[columnas_visibles].to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Descargar resultado filtrado en CSV",
            data=csv,
            file_name="datos_filtrados.csv",
            mime="text/csv"
        )

    except ImportError:
        st.error("Falta instalar openpyxl. Agrega openpyxl en requirements.txt.")
    except Exception as e:
        st.error("No se pudo leer el archivo Excel.")
        st.exception(e)
else:
    st.info("Sube un archivo Excel para empezar.")
