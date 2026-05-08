import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Visor Excel L2", layout="wide")

st.title("Visor y filtro de archivos Excel")

archivo = st.file_uploader(
    "Sube tu archivo Excel",
    type=["xlsx", "xls"]
)

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

        # Normalizar nombres de columnas
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

        st.sidebar.header("Filtros")

        filtro_maquina = st.sidebar.text_input(
            "Filtrar columna Maquina",
            value="L2"
        )

        tipo_filtro = st.sidebar.selectbox(
            "Tipo de filtro Maquina",
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

        if filtro_maquina:
            serie_maquina = df_filtrado["Maquina"].astype(str).str.strip()
            texto = filtro_maquina.strip()

            if tipo_filtro == "Contiene palabra exacta":
                patron = (
                    rf"(?<![A-Za-z0-9])"
                    rf"{re.escape(texto)}"
                    rf"(?![A-Za-z0-9])"
                )

                df_filtrado = df_filtrado[
                    serie_maquina.str.contains(
                        patron,
                        case=False,
                        na=False,
                        regex=True
                    )
                ]

            elif tipo_filtro == "Contiene":
                patron = re.escape(texto)

                df_filtrado = df_filtrado[
                    serie_maquina.str.contains(
                        patron,
                        case=False,
                        na=False,
                        regex=True
                    )
                ]

            elif tipo_filtro == "Igual a":
                df_filtrado = df_filtrado[
                    serie_maquina.str.lower() == texto.lower()
                ]

            elif tipo_filtro == "Empieza con":
                df_filtrado = df_filtrado[
                    serie_maquina.str.lower().str.startswith(texto.lower())
                ]

            elif tipo_filtro == "Termina con":
                df_filtrado = df_filtrado[
                    serie_maquina.str.lower().str.endswith(texto.lower())
                ]

        st.subheader("Datos filtrados")

        st.write(
            f"Filas filtradas: **{df_filtrado.shape[0]}** | "
            f"Columnas mostradas: **{df_filtrado.shape[1]}**"
        )

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            height=700
        )

        csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Descargar datos filtrados en CSV",
            data=csv,
            file_name="datos_filtrados_L2.csv",
            mime="text/csv"
        )

    except ImportError:
        st.error("Falta instalar openpyxl.")
        st.code("pip install openpyxl")

    except Exception as e:
        st.error("No se pudo cargar el archivo Excel.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para mostrar el display.")
