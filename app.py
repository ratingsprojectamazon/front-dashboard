import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Amazon Electronics Risk Monitor",
    layout="wide",
    page_icon="📦"
)

# Gestión de URL de la API (Nube vs Local)
try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = "http://127.0.0.1:8000/api/v1"

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* 1. TARJETA (Fondo Blanco) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* 2. REGLA UNIVERSAL: Todo lo que viva dentro de la tarjeta es oscuro */
    /* El selector universal (*) fuerza el color en títulos, valores, párrafos y divs */
    div[data-testid="stMetric"] * {
        color: #202124 !important; /* Gris muy oscuro (casi negro) */
    }

    /* 3. Ajuste opcional para el título (hacerlo un poco más pequeño que el número) */
    div[data-testid="stMetricLabel"] p {
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    
    /* 4. Ajuste para el Valor (hacerlo grande) */
    div[data-testid="stMetricValue"] div {
        font-size: 28px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=100) 
with col_title:
    st.title("Monitor de Riesgo de Devoluciones")
    st.caption("Análisis predictivo de reseñas y causas raíz (Electronics Category)")

# --- SIDEBAR (FILTROS) ---
with st.sidebar:
    st.header("⚙️ Filtros")
    
    periodo_seleccionado = st.selectbox(
        "Periodo de Análisis:",
        [
            "2023-01", "2023-02", "2023-03", 
            "2023-04", "2023-05", "2023-06", 
            "2023-07", "2023-08", "2023-09"
        ], 
        index=0
    )
    
    top_n_display = st.slider("Mostrar Top Riesgo:", 5, 100, 10)
    
    min_reviews = st.slider(
        "Mínimo de Reseñas (Volumen):", 
        min_value=0,        
        max_value=200,      
        value=20,           
        step=5,
        help="Filtra productos con pocas operaciones para evitar falsos positivos."
    )
    
    st.divider()
    st.caption(f"🟢 API Conectada: {API_URL}")

# --- LOGICA DE DATOS ---

@st.cache_data(ttl=600)
def cargar_ranking_api(periodo):
    try:
        resp = requests.get(
            f"{API_URL}/ranking/riesgo", 
            params={"periodo": periodo, "top_n": 2000} 
        )
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 1. Cargar Datos
df_ranking = cargar_ranking_api(periodo_seleccionado)

if not df_ranking.empty:
    # 2. Filtro de Volumen
    df_filtrado = df_ranking[df_ranking['n_reviews'] >= min_reviews]

    # --- SECCIÓN 1: KPIS ---
    riesgo_prom = df_filtrado['pct_neg'].mean() * 100 if not df_filtrado.empty else 0
    total_reviews = df_filtrado['n_reviews'].sum() if not df_filtrado.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Productos en Riesgo", len(df_filtrado))
    col2.metric("Tasa de Negativas Promedio", f"{riesgo_prom:.1f}%")
    col3.metric("Volumen de Reseñas", f"{total_reviews:,}")
    col4.metric("Periodo", periodo_seleccionado)

    st.divider()

    # --- SECCIÓN 2: TABLA Y DETALLE ---
    col_tabla, col_detalle = st.columns([3, 2])

    if df_filtrado.empty:
        st.warning(f"Ningún producto tiene más de {min_reviews} reseñas.")
    else:
        # Ordenamiento y Corte
        df_ordenado = df_filtrado.sort_values(by=['n_neg', 'pct_neg'], ascending=[False, False])
        df_display = df_ordenado.head(top_n_display)
        
        # --- TABLA ---
        with col_tabla:
            st.subheader(f"📉 Ranking: Top {len(df_display)} Críticos")
            st.dataframe(
                df_display[['risk_rank', 'asin', 'pct_neg', 'n_reviews', 'n_neg']],
                column_config={
                    "risk_rank": st.column_config.NumberColumn("Ranking", format="%d"),
                    "asin": "ASIN (Productos)",
                    "pct_neg": st.column_config.ProgressColumn("Negativas (%)", format="%.1f%%", min_value=0, max_value=1),
                    "n_reviews": st.column_config.NumberColumn("Total Ops"),
                    "n_neg": st.column_config.NumberColumn("Quejas")
                },
                use_container_width=True,
                hide_index=True,
                height=600, # Aumenté la altura para equilibrar con los dos gráficos
                selection_mode="single-row"
            )

        # --- DETALLE (GRÁFICOS) ---
        with col_detalle:
            st.subheader("🔍 Análisis de Causas")
            
            lista_asins_visibles = df_display['asin'].tolist()
            
            if not lista_asins_visibles:
                st.info("No hay productos para mostrar.")
                asin_seleccionado = None
            else:
                asin_seleccionado = st.selectbox("Selecciona un ASIN:", lista_asins_visibles)
            
            if asin_seleccionado:
                try:
                    resp_causas = requests.get(
                        f"{API_URL}/productos/{asin_seleccionado}/mapa-causas", 
                        params={"periodo": periodo_seleccionado}
                    )
                    data_causas = resp_causas.json() if resp_causas.status_code == 200 else {}
                    lista_items = data_causas.get("mapa_causas", [])
                    
                    if lista_items:
                        df_causas = pd.DataFrame(lista_items)
                        # Ordenar datos
                        df_causas = df_causas.sort_values(by="conteo", ascending=True)
                        
                        # 1. GRÁFICO DE DONA (ARRIBA) - Para Proporción
                        fig_pie = px.pie(
                            df_causas, 
                            values='conteo', 
                            names='causa', 
                            title=f"<b>Distribución de Problemas</b>",
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig_pie.update_traces(textposition='inside', textinfo='percent')
                        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
                        st.plotly_chart(fig_pie, use_container_width=True)

                        st.divider() # Separador visual

                        # 2. GRÁFICO DE BARRAS (ABAJO) - Para Magnitud
                        fig_bar = px.bar(
                            df_causas, 
                            x='conteo', 
                            y='causa', 
                            orientation='h',
                            title=f"<b>Detalle por Cantidad</b>",
                            text='conteo',
                            color='conteo',
                            color_continuous_scale='Reds'
                        )
                        fig_bar.update_layout(
                            xaxis_title="Cantidad de Quejas",
                            yaxis_title=None,
                            plot_bgcolor='rgba(0,0,0,0)',
                            showlegend=False,
                            height=250,
                            margin=dict(t=40, b=0, l=0, r=0)
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                        # Causa principal (la última del df ordenado)
                        causa_principal = df_causas.iloc[-1]['causa']
                    else:
                        st.info("No hay causas específicas detectadas.")
                        causa_principal = None
                except Exception as e:
                    st.error(f"Error: {e}")
                    causa_principal = None

    # --- SECCIÓN 3: EVIDENCIA ---
    if 'asin_seleccionado' in locals() and asin_seleccionado and 'causa_principal' in locals() and causa_principal:
        st.divider()
        st.subheader(f"🗣️ Voz del Cliente: Evidencia de '{causa_principal}'")
        
        with st.expander("Ver testimonios reales (Clic para desplegar)", expanded=True):
            try:
                resp_ev = requests.get(
                    f"{API_URL}/productos/{asin_seleccionado}/evidencia",
                    params={"periodo": periodo_seleccionado, "causa": causa_principal}
                )
                evidencias = resp_ev.json() if resp_ev.status_code == 200 else []
                
                if evidencias:
                    for ev in evidencias:
                        st.warning(f"⭐ ({ev['overall']}/5) ...{ev['reviewText'][:250]}...")
                else:
                    st.caption("⚠️ No hay textos de evidencia disponibles en el snapshot local (Solo Metadata).")
            except:
                st.caption("Error conectando con el servicio de evidencia.")

else:
    st.error(f"No se pudo conectar con el Backend en {API_URL}. Asegúrate de ejecutar 'uvicorn'.")