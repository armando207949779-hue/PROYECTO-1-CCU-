import streamlit as st
import pandas as pd

st.set_page_config(page_title="Visor de Excel", layout="wide")

st.title("Visor y filtro de archivos Excel")

archivo = st.file_uploader(
    "Sube tu archivo Excel",
    type=["xlsx", "xls"]
)

if archivo is not None:
    # Leer hojas disponibles
    excel = pd.ExcelFile(archivo)
    hoja = st.selectbox("Selecciona una hoja", excel.sheet_names)

    df = pd.read_excel(archivo, sheet_name=hoja)

    st.subheader("Datos originales")
    st.write(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}")

    # Filtros
    st.sidebar.header("Filtros")

    df_filtrado = df.copy()

    for columna in df.columns:
        valores_unicos = df[columna].dropna().unique()

        # Solo crear filtro si la columna tiene pocos valores distintos
        if len(valores_unicos) > 0 and len(valores_unicos) <= 50:
            seleccion = st.sidebar.multiselect(
                f"Filtrar por {columna}",
                options=valores_unicos,
                default=valores_unicos
            )

            df_filtrado = df_filtrado[df_filtrado[columna].isin(seleccion)]

    # Buscador general
    busqueda = st.text_input("Buscar texto en toda la tabla")

    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado.astype(str)
            .apply(lambda fila: fila.str.contains(busqueda, case=False, na=False).any(), axis=1)
        ]

    st.subheader("Datos filtrados")
    st.write(f"Filas filtradas: {df_filtrado.shape[0]}")

    st.dataframe(df_filtrado, use_container_width=True)

    # Descargar resultado filtrado
    csv = df_filtrado.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Descargar resultado filtrado en CSV",
        data=csv,
        file_name="datos_filtrados.csv",
        mime="text/csv"
    )

else:
    st.info("Sube un archivo Excel para empezar.")