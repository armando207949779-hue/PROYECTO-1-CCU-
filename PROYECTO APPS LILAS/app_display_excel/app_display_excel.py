import streamlit as st
import pandas as pd
import re

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
        df.columns = [
            str(col) if str(col) != "nan" else f"Columna_{i + 1}"
            for i, col in enumerate(df.columns)
        ]

        st.write(
            f"Filas originales: **{df.shape[0]}** | "
            f"Columnas: **{df.shape[1]}**"
        )

        st.sidebar.header("Opciones de visualización")

        columnas_visibles = st.sidebar.multiselect(
            "Columnas a mostrar",
            options=list(df.columns),
            default=list(df.columns)
        )

        st.sidebar.header("Filtros")

        df_filtrado = df.copy()

        busqueda_general = st.sidebar.text_input("Buscar en toda la tabla")

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

        # Crear filtros para TODAS las columnas por defecto
        columnas_para_filtrar = list(df.columns)

        for columna in columnas_para_filtrar:
            with st.sidebar.expander(f"Filtrar: {columna}", expanded=False):
                serie_original = df[columna]

                # Intentar detectar fechas
                serie_fecha = pd.to_datetime(serie_original, errors="coerce")
                total_no_nulos = len(serie_original.dropna())

                es_fecha = (
                    total_no_nulos > 0
                    and serie_fecha.notna().sum() >= total_no_nulos * 0.7
                )

                # Filtro numérico
                if pd.api.types.is_numeric_dtype(serie_original):
                    minimo = serie_original.min()
                    maximo = serie_original.max()

                    if pd.notna(minimo) and pd.notna(maximo):
                        minimo = float(minimo)
                        maximo = float(maximo)

                        if minimo != maximo:
                            rango = st.slider(
                                "Rango",
                                min_value=minimo,
                                max_value=maximo,
                                value=(minimo, maximo),
                                key=f"rango_{columna}"
                            )

                            df_filtrado = df_filtrado[
                                (df_filtrado[columna] >= rango[0])
                                & (df_filtrado[columna] <= rango[1])
                            ]
                        else:
                            st.caption(f"Valor único: {minimo}")
                    else:
                        st.caption("Columna numérica sin valores válidos.")

                # Filtro fecha
                elif es_fecha:
                    fechas_validas = serie_fecha.dropna()

                    if not fechas_validas.empty:
                        fecha_min = fechas_validas.min().date()
                        fecha_max = fechas_validas.max().date()

                        rango_fechas = st.date_input(
                            "Rango de fechas",
                            value=(fecha_min, fecha_max),
                            min_value=fecha_min,
                            max_value=fecha_max,
                            key=f"fecha_{columna}"
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
                        st.caption("Columna de fecha sin valores válidos.")

                # Filtro texto / categoría
                else:
                    tipo_filtro_texto = st.selectbox(
                        "Tipo de filtro",
                        options=[
                            "Contiene",
                            "Contiene palabra exacta",
                            "Igual a",
                            "Empieza con",
                            "Termina con"
                        ],
                        key=f"tipo_texto_{columna}"
                    )

                    texto = st.text_input(
                        "Texto a filtrar",
                        key=f"texto_{columna}"
                    )

                    if texto:
                        serie_texto = df_filtrado[columna].astype(str).str.strip()
                        texto_limpio = texto.strip()

                        if tipo_filtro_texto == "Contiene":
                            patron = re.escape(texto_limpio)

                            df_filtrado = df_filtrado[
                                serie_texto.str.contains(
                                    patron,
                                    case=False,
                                    na=False,
                                    regex=True
                                )
                            ]

                        elif tipo_filtro_texto == "Contiene palabra exacta":
                            patron = (
                                rf"(?<![A-Za-z0-9])"
                                rf"{re.escape(texto_limpio)}"
                                rf"(?![A-Za-z0-9])"
                            )

                            df_filtrado = df_filtrado[
                                serie_texto.str.contains(
                                    patron,
                                    case=False,
                                    na=False,
                                    regex=True
                                )
                            ]

                        elif tipo_filtro_texto == "Igual a":
                            df_filtrado = df_filtrado[
                                serie_texto.str.lower() == texto_limpio.lower()
                            ]

                        elif tipo_filtro_texto == "Empieza con":
                            df_filtrado = df_filtrado[
                                serie_texto.str.lower().str.startswith(
                                    texto_limpio.lower()
                                )
                            ]

                        elif tipo_filtro_texto == "Termina con":
                            df_filtrado = df_filtrado[
                                serie_texto.str.lower().str.endswith(
                                    texto_limpio.lower()
                                )
                            ]

                    valores = (
                        df[columna]
                        .dropna()
                        .astype(str)
                        .sort_values()
                        .unique()
                        .tolist()
                    )

                    if len(valores) <= 500:
                        seleccion = st.multiselect(
                            "Valores",
                            options=valores,
                            default=valores,
                            key=f"valores_{columna}"
                        )

                        df_filtrado = df_filtrado[
                            df_filtrado[columna].astype(str).isin(seleccion)
                        ]
                    else:
                        st.caption(
                            "Esta columna tiene más de 500 valores únicos. "
                            "Usa el filtro de texto."
                        )

        st.subheader("Datos filtrados")
        st.write(f"Filas filtradas: **{df_filtrado.shape[0]}**")

        if columnas_visibles:
            st.dataframe(
                df_filtrado[columnas_visibles],
                use_container_width=True,
                height=650
            )

            csv = df_filtrado[columnas_visibles].to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                label="Descargar resultado filtrado en CSV",
                data=csv,
                file_name="datos_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.warning("Selecciona al menos una columna para mostrar.")

    except ImportError:
        st.error(
            "Falta instalar openpyxl. "
            "Agrega openpyxl en requirements.txt."
        )

    except Exception as e:
        st.error("No se pudo leer el archivo Excel.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para empezar.")
