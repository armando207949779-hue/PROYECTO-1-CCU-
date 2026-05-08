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
    serie_texto = df_base[columna].astype(str).str.strip()
    texto_limpio = texto.strip()

    if not texto_limpio:
        return df_base

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

        st.write(
            f"Filas originales: **{df.shape[0]}** | "
            f"Columnas: **{df.shape[1]}**"
        )

        if "Maquina" not in df.columns:
            st.error("No existe la columna 'Maquina' en el archivo Excel.")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
            st.stop()

        st.sidebar.header("Opciones de visualización")

        columnas_visibles = st.sidebar.multiselect(
            "Columnas a mostrar",
            options=list(df.columns),
            default=list(df.columns)
        )

        st.sidebar.header("Filtro predeterminado")

        activar_l2 = st.sidebar.checkbox(
            "Aplicar filtro Maquina contiene L2",
            value=True
        )

        texto_l2 = st.sidebar.text_input(
            "Texto predeterminado en Maquina",
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

        if activar_l2 and texto_l2:
            df_filtrado = filtrar_texto(
                df_filtrado,
                "Maquina",
                texto_l2,
                tipo_l2
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

        maquinas_seleccionadas = st.sidebar.multiselect(
            "Máquinas disponibles",
            options=maquinas_l2,
            default=maquinas_l2
        )

        if maquinas_seleccionadas:
            df_filtrado = df_filtrado[
                df_filtrado["Maquina"].astype(str).isin(maquinas_seleccionadas)
            ]
        else:
            df_filtrado = df_filtrado.iloc[0:0]

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

        st.sidebar.header("Filtros por todas las columnas")

        opciones_texto = [
            "Contiene",
            "Contiene palabra exacta",
            "Igual a",
            "Empieza con",
            "Termina con"
        ]

        for columna in df.columns:
            if columna == "Maquina":
                titulo_expander = "Filtro adicional: Maquina"
            else:
                titulo_expander = f"Filtrar: {columna}"

            with st.sidebar.expander(titulo_expander, expanded=False):
                serie_original = df[columna]

                serie_fecha = pd.to_datetime(
                    serie_original,
                    errors="coerce"
                )

                total_no_nulos = len(serie_original.dropna())

                es_fecha = (
                    total_no_nulos > 0
                    and serie_fecha.notna().sum() >= total_no_nulos * 0.7
                )

                if pd.api.types.is_numeric_dtype(serie_original):
                    minimo = df_filtrado[columna].min()
                    maximo = df_filtrado[columna].max()

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
                        st.caption("Sin fechas disponibles.")

                else:
                    tipo_filtro_texto = st.selectbox(
                        "Tipo de filtro",
                        options=opciones_texto,
                        index=0,
                        key=f"tipo_texto_{columna}"
                    )

                    texto = st.text_input(
                        "Texto a filtrar",
                        key=f"texto_{columna}"
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
                            key=f"valores_{columna}"
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
            f"Filas filtradas: **{df_filtrado.shape[0]}** | "
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
