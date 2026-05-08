import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Display Excel L2", layout="wide")

st.title("Display de archivo Excel - Filtro Maquina L2")

# Ruta local del archivo Excel
ruta_excel = r"C:\Users\arman\Downloads\Listado_LILA_ESTANDAR (3).xlsx"

try:
    # Leer archivo Excel
    excel = pd.ExcelFile(ruta_excel, engine="openpyxl")

    hoja = st.selectbox(
        "Selecciona una hoja",
        excel.sheet_names
    )

    df = pd.read_excel(
        ruta_excel,
        sheet_name=hoja,
        engine="openpyxl"
    )

    # Normalizar nombres de columnas
    df.columns = [
        str(col).strip() if str(col) != "nan" else f"Columna_{i + 1}"
        for i, col in enumerate(df.columns)
    ]

    # Verificar que exista la columna Maquina
    if "Maquina" not in df.columns:
        st.error("No existe la columna 'Maquina' en el archivo Excel.")
        st.write("Columnas encontradas:")
        st.write(list(df.columns))
        st.stop()

    st.write(f"Archivo cargado: `{ruta_excel}`")
    st.write(f"Filas originales: **{df.shape[0]}** | Columnas: **{df.shape[1]}**")

    st.sidebar.header("Filtros")

    # Valor por defecto del filtro
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
    st.write(f"Filas filtradas: **{df_filtrado.shape[0]}**")

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

except FileNotFoundError:
    st.error("No se encontró el archivo. Revisa que la ruta sea correcta.")
    st.write(f"Ruta usada: `{ruta_excel}`")

except ImportError:
    st.error("Falta instalar openpyxl.")
    st.code("pip install openpyxl")

except Exception as e:
    st.error("No se pudo cargar el archivo Excel.")
    st.exception(e)
