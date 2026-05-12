# =====================================================
# PÁGINA ALERTAS SIMPLE
# =====================================================

def pagina_alertas():
    mostrar_logo_centrado()

    st.markdown(
        """
        <div class='portal-header'>
            <h1>Alertas de registros pendientes</h1>
            <p>Detalle por dashboard con estado de actualización de registros.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown("## Configuración de alertas")

    umbral_global = st.sidebar.number_input(
        "Días máximos sin registro",
        min_value=1,
        max_value=90,
        value=3,
        step=1
    )

    if st.sidebar.button("Actualizar alertas"):
        st.cache_data.clear()
        st.rerun()

    resultados = []

    for nombre, config in DASHBOARDS_MONITOREADOS.items():
        estado = calcular_estado_dashboard(
            nombre=nombre,
            config=config,
            umbral_dias=umbral_global
        )
        resultados.append(estado)

    df_alertas = pd.DataFrame(resultados)

    if df_alertas.empty:
        st.warning("No hay dashboards configurados para monitorear.")
        return

    df_alertas["Días sin registro"] = pd.to_numeric(
        df_alertas["Días sin registro"],
        errors="coerce"
    )

    total_alertas = int((df_alertas["Estado"] == "ALERTA").sum())
    total_errores = int((df_alertas["Estado"] == "ERROR").sum())
    total_problemas = total_alertas + total_errores
    total_ok = int((df_alertas["Estado"] == "OK").sum())

    col_ok, col_alerta = st.columns(2)

    with col_ok:
        tarjeta_estado("Dashboards OK", total_ok, alerta=False)

    with col_alerta:
        tarjeta_estado(
            "Dashboards con alerta/error",
            total_problemas,
            alerta=total_problemas > 0
        )

    if total_problemas > 0:
        st.markdown(
            f"""
            <div class="estado-alerta">
                <div class="estado-alerta-title">
                    Alerta activa
                </div>
                <div class="estado-alerta-text">
                    Hay {total_problemas} dashboard(s) con alerta o error.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="estado-ok">
                <div class="estado-ok-title">
                    Estado operacional OK
                </div>
                <div class="estado-ok-text">
                    Todos los dashboards monitoreados están dentro del umbral configurado.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("## Detalle por dashboard")

    with st.expander("Ver detalle por dashboard", expanded=True):
        df_detalle = df_alertas.copy()

        df_detalle["Días sin registro"] = df_detalle["Días sin registro"].apply(
            lambda x: "N/A" if pd.isna(x) else max(int(x), 0)
        )

        columnas_detalle = [
            "Línea",
            "Tipo",
            "Estado",
            "Último registro",
            "Último operador",
            "Días sin registro",
            "Umbral",
            "Registros",
            "Detalle alerta insumo crítico",
            "Detalle",
        ]

        st.dataframe(
            df_detalle[columnas_detalle].style.apply(estilo_detalle_alertas, axis=1),
            use_container_width=True,
            hide_index=True
        )

    st.download_button(
        "Descargar detalle CSV",
        df_alertas.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"detalle_alertas_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
