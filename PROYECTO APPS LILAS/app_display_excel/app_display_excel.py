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
    page_title="Visor Excel / Parquet L2",
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
    BASE_DIR.parent.parent / "assets" / "CCU_logo_(2018).svg.png",
    BASE_DIR.parent.parent.parent / "assets" / "CCU_logo_(2018).svg.png",
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
            margin-top: 3.8rem;
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
    st.warning("Logo no encontrado. Rutas revisadas:")
    for path in LOGO_CANDIDATES:
        st.write(str(path))

st.markdown(
    """
    <div style='text-align:center; margin-bottom:1.6rem;'>
        <h1 style='margin-top:0;'>
            Visor, análisis e IDs agrupados<br>
            Estándares Visuales LILA
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

archivo = st.file_uploader(
    "Sube tu archivo Excel o Parquet",
    type=["xlsx", "xls", "parquet"]
)

# =====================================================
# REPOSITORIOS DE OPCIONES
# =====================================================
REPOSITORIOS = {
    "Lila": [
        "LIMPIEZA",
        "INSPECCIÓN",
        "LUBRICACIÓN",
        "AJUSTE"
    ],
    "Criticidad": [
        "BAJA",
        "MEDIA",
        "ALTA"
    ],
    "Punto Q": [
        "SI",
        "NO"
    ],
    "Estado Equipo": [
        "ENCENDIDO",
        "APAGADO"
    ],
    "Frecuencia": [
        "POR TURNO",
        "DIARIA",
        "SEMANAL",
        "QUINCENAL",
        "MENSUAL",
        "BIMESTRAL",
        "TRIMESTRAL",
        "SEMESTRAL",
        "ANUAL"
    ],
    "Turno": [
        "A",
        "B",
        "C"
    ],
    "Dias De La Semana": [
        "LUNES",
        "MARTES",
        "MIÉRCOLES",
        "JUEVES",
        "VIERNES",
        "SÁBADO",
        "DOMINGO"
    ],
    "Epp": [
        "DELANTAL DESECHABLE",
        "GUANTE MECANICO",
        "LENTES DE SEGURIDAD",
        "ZAPATOS DE SEGURIDAD"
    ],
    "Materiales/Herramientas": [
        "PAÑO",
        "ESCOBILLA",
        "LLAVE",
        "DESTORNILLADOR",
        "LUBRICANTE",
        "ALCOHOL",
        "ATOMIZADOR",
        "BROCHA",
        "ESPÁTULA",
        "HERRAMIENTA MANUAL"
    ]
}

# =====================================================
# FUNCIONES GENERALES
# =====================================================
def normalizar_texto(texto):
    return (
        str(texto)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
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

    for valor in valores_mostrar:
        valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)
        checkbox_key = f"chk_{key_prefix}_{valor_key}"

        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = activar_por_defecto

    col_btn_1, col_btn_2 = st.columns(2)

    with col_btn_1:
        if st.button(
            "Seleccionar todas",
            key=f"btn_seleccionar_todas_{key_prefix}"
        ):
            for valor in valores_mostrar:
                valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)
                checkbox_key = f"chk_{key_prefix}_{valor_key}"
                st.session_state[checkbox_key] = True

    with col_btn_2:
        if st.button(
            "Deseleccionar todas",
            key=f"btn_deseleccionar_todas_{key_prefix}"
        ):
            for valor in valores_mostrar:
                valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)
                checkbox_key = f"chk_{key_prefix}_{valor_key}"
                st.session_state[checkbox_key] = False

    seleccionados = []

    for valor in valores_mostrar:
        valor_key = re.sub(r"[^A-Za-z0-9_]", "_", valor)
        checkbox_key = f"chk_{key_prefix}_{valor_key}"

        if conteos is not None:
            etiqueta = f"{valor} ({conteos.get(valor, 0)})"
        else:
            etiqueta = valor

        marcado = st.checkbox(
            etiqueta,
            key=checkbox_key
        )

        if marcado:
            seleccionados.append(valor)

    return seleccionados


def crear_nombre_foto_id_agrupado(id_estandar, nombre_original, indice_foto):
    extension = os.path.splitext(nombre_original)[1].lower()
    id_limpio = limpiar_nombre_archivo(str(id_estandar).upper())
    nombre = f"{id_limpio}_FOTO_{indice_foto:02d}{extension}"
    return nombre


def crear_zip_fotos_id_agrupado(fotos_subidas, id_estandar_final):
    zip_buffer = BytesIO()
    id_limpio = limpiar_nombre_archivo(str(id_estandar_final).upper())

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, archivo_foto in enumerate(fotos_subidas, start=1):
            nombre_foto = crear_nombre_foto_id_agrupado(
                id_estandar=id_estandar_final,
                nombre_original=archivo_foto.name,
                indice_foto=idx
            )

            ruta_dentro_zip = f"{id_limpio}/{nombre_foto}"

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


def cargar_archivo(archivo_subido):
    nombre_archivo = archivo_subido.name.lower()

    if nombre_archivo.endswith(".parquet"):
        df_cargado = pd.read_parquet(archivo_subido, engine="pyarrow")
        nombre_origen = "Archivo Parquet"
        return df_cargado, nombre_origen

    if nombre_archivo.endswith(".xlsx") or nombre_archivo.endswith(".xls"):
        excel = pd.ExcelFile(archivo_subido, engine="openpyxl")

        hoja = st.selectbox(
            "Selecciona una hoja",
            excel.sheet_names
        )

        df_cargado = pd.read_excel(
            archivo_subido,
            sheet_name=hoja,
            engine="openpyxl"
        )

        return df_cargado, hoja

    raise ValueError("Formato no soportado. Usa Excel o Parquet.")


def limpiar_valores_serie(serie):
    valores = (
        serie
        .dropna()
        .astype(str)
        .str.strip()
    )

    valores = valores[
        (valores != "")
        & (valores.str.lower() != "nan")
        & (valores.str.lower() != "none")
        & (valores.str.lower() != "nat")
    ]

    return valores


def valor_mas_repetido(serie):
    valores = limpiar_valores_serie(serie)

    if valores.empty:
        return ""

    return valores.value_counts().index[0]


def indice_opcion_sugerida(opciones, sugerido):
    sugerido_norm = normalizar_texto(sugerido)

    for i, opcion in enumerate(opciones):
        if normalizar_texto(opcion) == sugerido_norm:
            return i

    return 0


def obtener_tipo_columna_repositorio(columna):
    col = normalizar_texto(columna)

    if col == "lila":
        return "Lila"

    if "criticidad" in col:
        return "Criticidad"

    if "punto q" in col or col == "puntoq":
        return "Punto Q"

    if "estado equipo" in col or "estado del equipo" in col:
        return "Estado Equipo"

    if "frecuencia" in col:
        return "Frecuencia"

    if col == "turno":
        return "Turno"

    if (
        "dia de la semana" in col
        or "dias de la semana" in col
        or col == "dia"
        or col == "dias"
    ):
        return "Dias De La Semana"

    if col == "epp" or col == "e.p.p.":
        return "Epp"

    if "materiales" in col and "herramientas" in col:
        return "Materiales/Herramientas"

    if "descripcion actividad" in col:
        return "Descripción Actividad"

    return None


def selector_con_repositorio(columna, serie, key_base):
    tipo = obtener_tipo_columna_repositorio(columna)

    if tipo not in REPOSITORIOS:
        return None

    opciones = REPOSITORIOS[tipo]
    sugerido = valor_mas_repetido(serie)
    index_sugerido = indice_opcion_sugerida(opciones, sugerido)

    return st.selectbox(
        f"Valor final para {columna}",
        options=opciones,
        index=index_sugerido,
        key=key_base
    )


def descripcion_original_a_pasos(serie):
    valores = limpiar_valores_serie(serie)
    valores_unicos = list(dict.fromkeys(valores.tolist()))

    if not valores_unicos:
        return ["", "", ""]

    return valores_unicos


def editor_descripcion_pasos(columna, serie, key_prefix):
    pasos_sugeridos = descripcion_original_a_pasos(serie)

    key_cantidad = f"{key_prefix}_cantidad_pasos"

    if key_cantidad not in st.session_state:
        st.session_state[key_cantidad] = max(len(pasos_sugeridos), 3)

    col_btn_1, col_btn_2 = st.columns(2)

    with col_btn_1:
        if st.button("Agregar paso", key=f"{key_prefix}_agregar_paso"):
            st.session_state[key_cantidad] += 1

    with col_btn_2:
        if st.button("Quitar paso", key=f"{key_prefix}_quitar_paso"):
            if st.session_state[key_cantidad] > 1:
                st.session_state[key_cantidad] -= 1

    pasos_finales = []

    for i in range(st.session_state[key_cantidad]):
        valor_default = pasos_sugeridos[i] if i < len(pasos_sugeridos) else ""

        paso = st.text_area(
            f"Paso {i + 1}",
            value=valor_default,
            height=90,
            key=f"{key_prefix}_paso_{i + 1}"
        )

        pasos_finales.append(f"PASO {i + 1}: {paso.strip()}")

    return "\n".join(pasos_finales)


def editor_lista_textbox(columna, serie, key_prefix):
    valores_originales = limpiar_valores_serie(serie)
    valores_unicos = list(dict.fromkeys(valores_originales.tolist()))

    key_cantidad = f"{key_prefix}_cantidad"

    if key_cantidad not in st.session_state:
        st.session_state[key_cantidad] = max(len(valores_unicos), 3)

    st.write(f"¿Cuántos elementos colocar en **{columna}**?")

    col_btn_1, col_btn_2 = st.columns(2)

    with col_btn_1:
        if st.button("Agregar", key=f"{key_prefix}_agregar"):
            st.session_state[key_cantidad] += 1

    with col_btn_2:
        if st.button("Quitar", key=f"{key_prefix}_quitar"):
            if st.session_state[key_cantidad] > 1:
                st.session_state[key_cantidad] -= 1

    seleccionados = []

    for i in range(st.session_state[key_cantidad]):
        valor_default = valores_unicos[i] if i < len(valores_unicos) else ""

        valor = st.text_input(
            f"{columna} {i + 1}",
            value=valor_default,
            key=f"{key_prefix}_{i + 1}"
        )

        valor = valor.strip()

        if valor:
            seleccionados.append(valor)

    seleccionados = list(dict.fromkeys(seleccionados))

    return "\n".join([f"- {valor}" for valor in seleccionados])


def convertir_dataframe_a_mayusculas(df_base):
    df_mayusculas = df_base.copy()

    for columna in df_mayusculas.columns:
        df_mayusculas[columna] = df_mayusculas[columna].apply(
            lambda valor: valor.upper() if isinstance(valor, str) else valor
        )

    return df_mayusculas


def selector_ids_con_checkboxes(ids_disponibles, key_prefix, columnas=4):
    st.markdown("**Selecciona los IDs que quieres agrupar**")

    buscar_id = st.text_input(
        "Buscar ID",
        key=f"{key_prefix}_buscar"
    )

    if buscar_id:
        ids_mostrar = [
            id_valor for id_valor in ids_disponibles
            if buscar_id.lower() in str(id_valor).lower()
        ]
    else:
        ids_mostrar = ids_disponibles

    col_btn_1, col_btn_2 = st.columns(2)

    with col_btn_1:
        if st.button("Seleccionar todos los IDs visibles", key=f"{key_prefix}_todos"):
            for id_valor in ids_mostrar:
                id_key = re.sub(r"[^A-Za-z0-9_]", "_", str(id_valor))
                st.session_state[f"{key_prefix}_id_{id_key}"] = True

    with col_btn_2:
        if st.button("Deseleccionar todos los IDs visibles", key=f"{key_prefix}_ninguno"):
            for id_valor in ids_mostrar:
                id_key = re.sub(r"[^A-Za-z0-9_]", "_", str(id_valor))
                st.session_state[f"{key_prefix}_id_{id_key}"] = False

    ids_seleccionados = []
    columnas_checkbox = st.columns(columnas)

    for idx, id_valor in enumerate(ids_mostrar):
        id_key = re.sub(r"[^A-Za-z0-9_]", "_", str(id_valor))
        checkbox_key = f"{key_prefix}_id_{id_key}"

        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False

        with columnas_checkbox[idx % columnas]:
            marcado = st.checkbox(
                str(id_valor),
                key=checkbox_key
            )

        if marcado:
            ids_seleccionados.append(str(id_valor))

    return ids_seleccionados


# =====================================================
# APP PRINCIPAL
# =====================================================
if archivo is not None:
    try:
        df, hoja = cargar_archivo(archivo)

        if archivo.name.lower().endswith(".parquet"):
            st.success("Archivo Parquet cargado correctamente.")
        else:
            st.success(f"Archivo Excel cargado correctamente. Hoja: {hoja}")

        df.columns = [
            str(col).strip() if str(col) != "nan" else f"Columna_{i + 1}"
            for i, col in enumerate(df.columns)
        ]

        if "Maquina" not in df.columns:
            st.error("No existe la columna 'Maquina' en el archivo.")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
            st.stop()

        if "Id Estándar" not in df.columns:
            st.error("No existe la columna 'Id Estándar' en el archivo.")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
            st.stop()

        st.write(
            f"Origen: **{hoja}** | "
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
            value=True
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

        tab_display, tab_analisis, tab_id_agrupado = st.tabs(
            [
                "Display filtrado",
                "Análisis de data filtrada",
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

                with st.expander("Histograma", expanded=False):
                    columnas_numericas = df_filtrado.select_dtypes(
                        include=["number"]
                    ).columns.tolist()

                    if columnas_numericas:
                        columna_histograma_default = (
                            columnas_numericas.index("Tiempo Estimado (en Minutos)")
                            if "Tiempo Estimado (en Minutos)" in columnas_numericas
                            else 0
                        )

                        columna_histograma = st.selectbox(
                            "Selecciona columna numérica para histograma",
                            options=columnas_numericas,
                            index=columna_histograma_default
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

        with tab_id_agrupado:
            st.subheader("Crear ID agrupado desde varios IDs existentes")

            st.write(
                "Selecciona una máquina y uno o más IDs. "
                "La app mostrará la información original de cada ID por columna. "
                "Luego se completará una propuesta usando repositorios de opciones."
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

                with st.expander("Seleccionar IDs con checkboxes", expanded=True):
                    ids_seleccionados = selector_ids_con_checkboxes(
                        ids_disponibles=ids_disponibles_agrupado,
                        key_prefix="ids_agrupado",
                        columnas=4
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

                    st.subheader("Completar información final del ID agrupado")

                    st.write(
                        "Los campos se completan usando repositorios de opciones para evitar errores. "
                        "Lila, criticidad, punto Q, estado equipo, frecuencia, turno y días de la semana usan dropdown. "
                        "Descripción actividad muestra 3 pasos por defecto y permite agregar o quitar pasos. "
                        "EPP y materiales/herramientas muestran 3 cajas de texto por defecto y permiten agregar más. "
                        "En tiempo estimado se muestra la suma como ayuda."
                    )

                    valores_finales = {}

                    ids_unidos = "_".join([
                        limpiar_nombre_archivo(str(id_valor)).upper()
                        for id_valor in ids_seleccionados
                    ])

                    id_estandar_sugerido = f"ID_{ids_unidos}"

                    valores_finales["Id Estándar"] = st.text_input(
                        "Id Estándar final",
                        value=id_estandar_sugerido,
                        key=f"final_id_estandar_{ids_unidos}"
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

                    for columna in columnas_editables:
                        st.markdown(f"### {columna}")

                        with st.expander(f"Ver valores originales de {columna}", expanded=True):
                            tabla_columna = tabla_valores_originales_simple(
                                df_ids_seleccionados,
                                columna
                            )

                            st.dataframe(
                                tabla_columna,
                                use_container_width=True
                            )

                        tipo_columna = obtener_tipo_columna_repositorio(columna)

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

                        elif tipo_columna == "Descripción Actividad":
                            st.caption(
                                "Por defecto se muestran 3 pasos. Puedes agregar o quitar pasos."
                            )

                            valores_finales[columna] = editor_descripcion_pasos(
                                columna=columna,
                                serie=df_ids_seleccionados[columna],
                                key_prefix=f"final_{columna}"
                            )

                        elif tipo_columna == "Epp":
                            st.caption(
                                "Por defecto se muestran 3 cajas de texto para EPP. Puedes agregar más."
                            )

                            valores_finales[columna] = editor_lista_textbox(
                                columna=columna,
                                serie=df_ids_seleccionados[columna],
                                key_prefix=f"final_{columna}"
                            )

                        elif tipo_columna == "Materiales/Herramientas":
                            st.caption(
                                "Por defecto se muestran 3 cajas de texto para materiales o herramientas. Puedes agregar más."
                            )

                            valores_finales[columna] = editor_lista_textbox(
                                columna=columna,
                                serie=df_ids_seleccionados[columna],
                                key_prefix=f"final_{columna}"
                            )

                        elif tipo_columna in [
                            "Lila",
                            "Criticidad",
                            "Punto Q",
                            "Estado Equipo",
                            "Frecuencia",
                            "Turno",
                            "Dias De La Semana"
                        ]:
                            st.caption(
                                "Selecciona el valor desde el repositorio de opciones."
                            )

                            valores_finales[columna] = selector_con_repositorio(
                                columna=columna,
                                serie=df_ids_seleccionados[columna],
                                key_base=f"final_{columna}"
                            )

                            if tipo_columna == "Lila" and valores_finales[columna] == "LUBRICACIÓN":
                                st.markdown("#### Datos de lubricación")

                                tipo_lubricante_sugerido = ""
                                cantidad_lubricante_sugerida = ""

                                if "Tipo de Lubricante" in df_ids_seleccionados.columns:
                                    tipo_lubricante_sugerido = valor_mas_repetido(
                                        df_ids_seleccionados["Tipo de Lubricante"]
                                    )

                                if "Cantidad de Lubricante" in df_ids_seleccionados.columns:
                                    cantidad_lubricante_sugerida = valor_mas_repetido(
                                        df_ids_seleccionados["Cantidad de Lubricante"]
                                    )

                                valores_finales["Tipo de Lubricante"] = st.text_input(
                                    "Tipo de lubricante",
                                    value=tipo_lubricante_sugerido,
                                    key="final_tipo_lubricante"
                                )

                                valores_finales["Cantidad de Lubricante"] = st.text_input(
                                    "Cantidad de lubricante",
                                    value=cantidad_lubricante_sugerida,
                                    key="final_cantidad_lubricante"
                                )

                        else:
                            valor_sugerido = valor_mas_repetido(
                                df_ids_seleccionados[columna]
                            )

                            st.caption(
                                "Campo sin repositorio definido. Se autocompleta con el valor más repetido."
                            )

                            valores_finales[columna] = st.text_input(
                                f"Valor final para {columna}",
                                value=valor_sugerido,
                                key=f"final_{columna}"
                            )

                    st.divider()

                    st.subheader("Vista previa del nuevo ID agrupado")

                    df_id_agrupado = pd.DataFrame([valores_finales])

                    columnas_ordenadas = [
                        col for col in df_filtrado.columns
                        if col in df_id_agrupado.columns
                    ]

                    columnas_extra_agrupado = [
                        col for col in df_id_agrupado.columns
                        if col not in columnas_ordenadas
                    ]

                    df_id_agrupado = df_id_agrupado[
                        columnas_ordenadas + columnas_extra_agrupado
                    ]
                    df_id_agrupado = convertir_dataframe_a_mayusculas(df_id_agrupado)

                    st.dataframe(
                        df_id_agrupado,
                        use_container_width=True
                    )

                    st.subheader("Descargar nuevo ID agrupado")

                    excel_id_agrupado = dataframe_a_excel_bytes(
                        df_id_agrupado,
                        nombre_hoja="ID agrupado"
                    )

                    id_estandar_final_mayuscula = str(
                        df_id_agrupado.iloc[0]["Id Estándar"]
                    ).upper()

                    maquina_final_mayuscula = str(
                        df_id_agrupado.iloc[0]["Maquina"]
                    ).upper()

                    nombre_archivo_agrupado = limpiar_nombre_archivo(
                        f"{id_estandar_final_mayuscula}_{maquina_final_mayuscula}"
                    )

                    st.download_button(
                        label="Descargar solo el nuevo ID agrupado",
                        data=excel_id_agrupado,
                        file_name=f"{nombre_archivo_agrupado}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    st.divider()

                    st.subheader("Fotos opcionales del ID agrupado")

                    st.write(
                        "Puedes subir una o más fotos. "
                        "Las fotos quedarán asociadas automáticamente al Id Estándar final "
                        "y se renombrarán usando ese ID."
                    )

                    fotos_id_agrupado = st.file_uploader(
                        "Sube una o más fotos para este ID agrupado",
                        type=["jpg", "jpeg", "png", "webp"],
                        accept_multiple_files=True,
                        key="fotos_id_agrupado"
                    )

                    if fotos_id_agrupado:
                        resumen_fotos_agrupado = []

                        st.write(
                            f"**ID asociado automáticamente:** "
                            f"`{id_estandar_final_mayuscula}`"
                        )

                        for idx, foto in enumerate(fotos_id_agrupado, start=1):
                            nombre_final_foto = crear_nombre_foto_id_agrupado(
                                id_estandar=id_estandar_final_mayuscula,
                                nombre_original=foto.name,
                                indice_foto=idx
                            )

                            resumen_fotos_agrupado.append(
                                {
                                    "Foto original": foto.name,
                                    "Id Estándar asociado": id_estandar_final_mayuscula,
                                    "Nombre final": nombre_final_foto
                                }
                            )

                        st.dataframe(
                            pd.DataFrame(resumen_fotos_agrupado),
                            use_container_width=True
                        )

                        with st.expander("Vista previa de fotos cargadas", expanded=False):
                            for foto in fotos_id_agrupado:
                                st.image(
                                    foto,
                                    caption=foto.name,
                                    use_container_width=True
                                )

                        zip_fotos_id_agrupado = crear_zip_fotos_id_agrupado(
                            fotos_subidas=fotos_id_agrupado,
                            id_estandar_final=id_estandar_final_mayuscula
                        )

                        st.download_button(
                            label="Descargar fotos del ID agrupado en ZIP",
                            data=zip_fotos_id_agrupado,
                            file_name=f"fotos_{id_estandar_final_mayuscula}.zip",
                            mime="application/zip"
                        )
                    else:
                        st.info("La carga de fotos es opcional.")

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
        st.code("pip install streamlit pandas openpyxl plotly pyarrow")

    except Exception as e:
        st.error("No se pudo cargar el archivo.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel o Parquet para mostrar el display.")
