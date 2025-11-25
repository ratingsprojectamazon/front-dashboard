# 📊 Amazon Electronics Risk Monitor - Frontend

Este directorio contiene la aplicación de **Streamlit** que actúa como la capa de presentación del sistema de Nowcasting. Su objetivo es transformar los datos crudos de riesgo en *insights* visuales accionables para la toma de decisiones operativas.

## 🛠️ Stack Tecnológico

* **Framework:** `Streamlit` (v1.35+) - Renderizado reactivo de componentes web.
* **Visualización:** `Plotly Express` - Gráficos interactivos (Donas, Barras).
* **Manipulación de Datos:** `Pandas` - Filtrado y ordenamiento en memoria.
* **Conectividad:** `Requests` - Comunicación HTTP con el Backend.

## 🎨 Arquitectura Visual y Técnica

La interfaz está diseñada siguiendo un flujo de trabajo analítico de "Macro a Micro" (Overview -> Filter -> Drill-down).

### 1. Gestión de Estado y Filtros
La aplicación utiliza el modelo de ejecución procedural de Streamlit. Los filtros globales se alojan en el `st.sidebar` para persistir el contexto de análisis:
* **Periodo:** Selector estático de meses procesados (Snapshot Gold).
* **Top N:** Control deslizante que define el límite de visualización (Head).
* **Volumen Mínimo:** Filtro lógico crítico que elimina productos con pocas operaciones (ruido estadístico) para evitar falsos positivos de riesgo 100%.

### 2. Componentes de UI Personalizados (CSS Hack)
Para garantizar la legibilidad y el *branding* corporativo, se inyecta CSS personalizado (`st.markdown(unsafe_allow_html=True)`) que sobrescribe los estilos nativos del **Shadow DOM** de Streamlit:
* **Tarjetas de KPIs:** Se fuerza un fondo blanco con texto oscuro (`#232F3E` - Amazon Dark Blue) mediante selectores `!important` para evitar conflictos con el "Dark Mode" automático del navegador.
* **Jerarquía:** Se estilizan los contenedores `stMetric` para destacar sobre el fondo de la aplicación.

### 3. Tabla de Ranking Interactiva
Implementada con `st.dataframe` utilizando la API `column_config`:
* **Mapas de Calor Lineales:** La columna `% Negativas` utiliza `st.column_config.ProgressColumn` para visualizar la magnitud del riesgo de 0 a 1.
* **Ordenamiento Dinámico:** El DataFrame se ordena en tiempo real priorizando **Volumen de Quejas (`n_neg`)** sobre el porcentaje relativo, asegurando que los problemas masivos aparezcan primero.

### 4. Visualización de Causas (Plotly)
Se implementa una estrategia de doble visualización para el análisis de causa raíz:
* **Gráfico de Dona:** Para visualizar la *proporción* del problema.
* **Gráfico de Barras:** Para comparar la *magnitud* absoluta de las quejas.
Ambos gráficos son interactivos y responden al evento de selección del ASIN en la lista desplegable sincronizada.

---

## 🔗 Integración con Backend

El Frontend es agnóstico a la fuente de datos; depende completamente de la API RESTful.

### Dependencias del Backend
Para funcionar, este dashboard requiere que el servicio `backend_api_riesgo` esté activo y exponga los siguientes endpoints:
* `GET /ranking/riesgo`: Para poblar la tabla y los KPIs.
* `GET /productos/{asin}/mapa-causas`: Para generar los gráficos.
* `GET /productos/{asin}/evidencia`: Para la sección de "Voz del Cliente".

### Configuración de Conexión
La URL del backend se configura dinámicamente. El sistema busca primero en los **Streamlit Secrets** (para producción) y hace *fallback* a `localhost` (para desarrollo).

**Variable de Entorno / Secreto:**
```toml
API_URL = "[http://127.0.0.1:8000/api/v1](http://127.0.0.1:8000/api/v1)"  # Local
# O para producción con Ngrok/Render:
# API_URL = "[https://tu-api-publica.ngrok-free.app/api/v1](https://tu-api-publica.ngrok-free.app/api/v1)"
```

**Variable de Entorno / Secreto:**
1. Instalar dependencias
    ```bash
    pip install -r requirements.txt
    ```
2. Ejecutar la aplicación
    ```bash
    streamlit run app.py
    ```