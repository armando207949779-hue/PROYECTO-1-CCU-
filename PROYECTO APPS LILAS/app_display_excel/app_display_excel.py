import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Visor Excel L2", layout="wide")

st.title("Visor y filtro de archivos Excel")

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

        columnas_visibles = st.sidebar.multiselect(
            "Columnas a mostrar",
            options=list(df.columns),
            default=list(df.columns)
        )

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

        st.sidebar.header("Filtrar máquinas dentro de L2")

        maquinas_l2 = (
            df_filtrado["Maquina"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )

        usar_filtro_maquinas = st.sidebar.checkbox(
            "Filtrar por máquinas específicas",
            value=False
        )

        if usar_filtro_maquinas:
            maquinas_seleccionadas = st.sidebar.multiselect(
                "Máquinas L2 disponibles",
                options=maquinas_l2,
                default=maquinas_l2
            )

            if maquinas_seleccionadas:
                df_filtrado = df_filtrado[
                    df_filtrado["Maquina"].astype(str).isin(maquinas_seleccionadas)
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

        columnas_para_filtrar = st.sidebar.multiselect(
            "Columnas adicionales a filtrar",
            options=list(df.columns),
            default=[]
        )

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
                        "Tipo de filtro",
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

                    if len(valores) <= 500:
                        seleccion = st.multiselect(
                            "Valores",
                            options=valores,
                            default=valores,
                            key=f"valores_adicional_{columna}"
                        )

                        if seleccion:
                            df_filtrado = df_filtrado[
                                df_filtrado[columna].astype(str).isin(seleccion)
                            ]
                        else:
                            df_filtrado = df_filtrado.iloc[0:0]
                    else:
                        st.caption(
                            "Esta columna tiene más de 500 valores únicos. "
                            "Usa el filtro de texto."
                        )

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

    except ImportError:
        st.error("Falta instalar openpyxl.")
        st.code("pip install openpyxl")

    except Exception as e:
        st.error("No se pudo cargar el archivo Excel.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para mostrar el display.")
