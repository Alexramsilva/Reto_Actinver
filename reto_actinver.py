import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Reto Actinver - Análisis Financiero",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Reto Actinver")
st.subheader("Análisis financiero con Yahoo Finance")

st.markdown(
    """
    Esta aplicación permite analizar una acción o activo financiero
    utilizando su clave de Yahoo Finance.
    
    **Ejemplos:** SOFI, SLB, TSM, IWM, HOOD, BTC-USD
    """
)

# ============================================================
# SIDEBAR - SELECCIÓN DEL ACTIVO
# ============================================================

st.sidebar.header("🔎 Selección del activo")

ticker_input = st.sidebar.text_input(
    "Clave de Yahoo Finance:",
    value="SOFI",
    placeholder="Ejemplo: SOFI, TSM, BTC-USD"
).strip().upper()

st.sidebar.markdown(
    """
    **Ejemplos de claves:**
    - SOFI
    - SLB
    - TSM
    - IWM
    - HOOD
    - BTC-USD
    """
)

analizar = st.sidebar.button(
    "📊 Analizar activo",
    type="primary",
    use_container_width=True
)

# ============================================================
# CONTROL DEL TICKER
# ============================================================

if "ticker_analizado" not in st.session_state:
    st.session_state.ticker_analizado = "SOFI"

if analizar:
    if ticker_input == "":
        st.sidebar.error("Ingrese una clave de Yahoo Finance.")
    else:
        st.session_state.ticker_analizado = ticker_input

ticker = st.session_state.ticker_analizado

st.info(f"Activo seleccionado: **{ticker}**")

# ============================================================
# FUNCIONES
# ============================================================

@st.cache_data(ttl=3600)
def descargar_historicos(ticker):
    """
    Descarga 5 años de información histórica.
    """
    return yf.download(
        ticker,
        period="5y",
        auto_adjust=False,
        progress=False
    )


@st.cache_data(ttl=3600)
def descargar_ultimo_anio(ticker):
    """
    Descarga un año de información histórica.
    """
    return yf.download(
        ticker,
        period="1y",
        auto_adjust=False,
        progress=False
    )


@st.cache_data(ttl=3600)
def obtener_fundamentales(ticker):
    """
    Obtiene indicadores fundamentales actuales.
    """

    try:
        activo = yf.Ticker(ticker)
        info = activo.info
    except Exception:
        info = {}

    return {
        "Price/Earnings": info.get("trailingPE"),
        "Price/Book": info.get("priceToBook"),
        "Debt/Equity": info.get("debtToEquity"),
        "Return on Equity": info.get("returnOnEquity"),
        "Dividend Yield": info.get("dividendYield")
    }


def obtener_close(df, ticker):
    """
    Obtiene la columna Close de manera robusta,
    incluso cuando yfinance devuelve MultiIndex.
    """

    if df.empty:
        return pd.Series(dtype=float)

    # Caso MultiIndex
    if isinstance(df.columns, pd.MultiIndex):

        # Intentar Close + ticker
        try:
            close = df["Close"][ticker]

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

            return close
        except Exception:
            pass

        # Intentar obtener nivel Close
        try:
            close = df.xs(
                "Close",
                axis=1,
                level=0
            )

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

            return close
        except Exception:
            pass

    # Caso columnas normales
    if "Close" in df.columns:

        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        return close

    return pd.Series(dtype=float)


# ============================================================
# DESCARGA DE DATOS
# ============================================================

try:

    datos_5y = descargar_historicos(ticker)

    if datos_5y.empty:
        st.error(
            f"No se encontraron datos para **{ticker}**. "
            "Verifique que la clave de Yahoo Finance sea correcta."
        )
        st.stop()

except Exception as e:

    st.error(
        f"No fue posible consultar Yahoo Finance: {e}"
    )

    st.stop()


# ============================================================
# PRECIO DE CIERRE
# ============================================================

close_5y = obtener_close(datos_5y, ticker)

if close_5y.empty:
    st.error("No fue posible obtener los precios de cierre.")
    st.stop()

close_5y = close_5y.dropna()

# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

precio_actual = float(close_5y.iloc[-1])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Precio actual",
        f"${precio_actual:,.2f}"
    )

with col2:
    precio_inicial = float(close_5y.iloc[0])

    rendimiento_total = (
        precio_actual / precio_inicial - 1
    )

    st.metric(
        "Rendimiento 5 años",
        f"{rendimiento_total * 100:.2f}%"
    )

with col3:
    maximo = float(close_5y.max())

    st.metric(
        "Máximo 5 años",
        f"${maximo:,.2f}"
    )


# ============================================================
# FUNDAMENTALES
# ============================================================

st.header("1️⃣ Indicadores fundamentales")

fundamentales = obtener_fundamentales(ticker)

fundamentales_df = pd.DataFrame(
    {
        "Indicador": list(fundamentales.keys()),
        "Valor": list(fundamentales.values())
    }
)

fundamentales_df["Valor"] = fundamentales_df["Valor"].apply(
    lambda x: "N/D" if x is None else x
)

st.dataframe(
    fundamentales_df,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Los indicadores fundamentales corresponden a la información "
    "disponible actualmente en Yahoo Finance."
)


# ============================================================
# RENDIMIENTOS DIARIOS
# ============================================================

st.header("2️⃣ Rendimientos diarios")

historical = pd.DataFrame({
    "Close": close_5y
})

historical["Daily Return"] = (
    historical["Close"].pct_change()
)

historical["Cumulative Return"] = (
    1 + historical["Daily Return"]
).cumprod()

historical["Year"] = historical.index.year

st.dataframe(
    historical.tail(10),
    use_container_width=True
)


# ============================================================
# RENDIMIENTOS ANUALES
# ============================================================

st.header("3️⃣ Rendimientos anuales")

annual_returns = (
    historical
    .groupby("Year")["Daily Return"]
    .apply(
        lambda x:
        (1 + x.dropna()).prod() - 1
    )
)

annual_returns_df = pd.DataFrame({
    "Año": annual_returns.index,
    "Rendimiento": annual_returns.values
})

annual_returns_df["Rendimiento"] = (
    annual_returns_df["Rendimiento"] * 100
)

st.dataframe(
    annual_returns_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# GRÁFICA DEL PRECIO
# ============================================================

st.header("4️⃣ Precio histórico")

fig1, ax1 = plt.subplots(figsize=(12, 5))

ax1.plot(
    historical.index,
    historical["Close"]
)

ax1.set_title(
    f"Precio de cierre - {ticker}"
)

ax1.set_xlabel("Fecha")
ax1.set_ylabel("Precio")

ax1.grid(True)

st.pyplot(fig1)


# ============================================================
# GRÁFICA RENDIMIENTO ACUMULADO
# ============================================================

st.header("5️⃣ Rendimiento acumulado")

fig2, ax2 = plt.subplots(figsize=(12, 5))

ax2.plot(
    historical.index,
    historical["Cumulative Return"]
)

ax2.set_title(
    f"Rendimiento acumulado - {ticker}"
)

ax2.set_xlabel("Fecha")
ax2.set_ylabel("Crecimiento de $1")

ax2.grid(True)

st.pyplot(fig2)


# ============================================================
# GRÁFICA DE RENDIMIENTOS ANUALES
# ============================================================

st.header("6️⃣ Rendimientos anuales")

fig3, ax3 = plt.subplots(figsize=(12, 5))

ax3.bar(
    annual_returns_df["Año"].astype(str),
    annual_returns_df["Rendimiento"]
)

ax3.set_title(
    f"Rendimientos anuales - {ticker}"
)

ax3.set_xlabel("Año")
ax3.set_ylabel("Rendimiento (%)")

ax3.axhline(
    y=0,
    linewidth=1
)

ax3.grid(
    axis="y",
    alpha=0.3
)

st.pyplot(fig3)


# ============================================================
# BLOQUE BERNOULLI
# ============================================================

st.header("7️⃣ Modelo de Bernoulli")

st.markdown(
    """
    Para cada día se define una variable aleatoria binaria:

    - **1 = éxito:** rendimiento diario positivo.
    - **0 = fracaso:** rendimiento diario cero o negativo.
    """
)

datos_1y = descargar_ultimo_anio(ticker)

close_1y = obtener_close(
    datos_1y,
    ticker
)

if close_1y.empty:

    st.warning(
        "No fue posible obtener los datos del último año."
    )

else:

    bernoulli_df = pd.DataFrame({
        "Close": close_1y
    })

    bernoulli_df["Daily Returns"] = (
        bernoulli_df["Close"].pct_change() * 100
    )

    bernoulli_df = bernoulli_df.dropna()

    bernoulli_df["Binary Returns"] = np.where(
        bernoulli_df["Daily Returns"] > 0,
        1,
        0
    )

    # ========================================================
    # PROBABILIDADES
    # ========================================================

    probabilidad_exito = (
        bernoulli_df["Binary Returns"].mean()
    )

    probabilidad_fracaso = (
        1 - probabilidad_exito
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Probabilidad de éxito",
            f"{probabilidad_exito * 100:.2f}%"
        )

    with col2:

        st.metric(
            "Probabilidad de fracaso",
            f"{probabilidad_fracaso * 100:.2f}%"
        )

    # ========================================================
    # TABLA
    # ========================================================

    st.subheader("Resultados del experimento de Bernoulli")

    st.dataframe(
        bernoulli_df.tail(20),
        use_container_width=True
    )

    # ========================================================
    # GRÁFICA BERNOULLI
    # ========================================================

    st.subheader(
        "Distribución de éxito y fracaso"
    )

    categorias = [
        "Fracaso (0)",
        "Éxito (1)"
    ]

    probabilidades = [
        probabilidad_fracaso,
        probabilidad_exito
    ]

    fig4, ax4 = plt.subplots(
        figsize=(8, 5)
    )

    ax4.bar(
        categorias,
        probabilidades
    )

    ax4.set_title(
        f"Distribución Bernoulli - {ticker}"
    )

    ax4.set_ylabel(
        "Probabilidad"
    )

    ax4.set_ylim(
        0,
        1
    )

    ax4.grid(
        axis="y",
        alpha=0.3
    )

    # Mostrar porcentaje sobre las barras
    for i, valor in enumerate(probabilidades):

        ax4.text(
            i,
            valor + 0.02,
            f"{valor * 100:.2f}%",
            ha="center"
        )

    st.pyplot(fig4)


# ============================================================
# CONCLUSIÓN
# ============================================================

st.header("8️⃣ Interpretación")

st.markdown(
    f"""
    ### Activo analizado: `{ticker}`

    El análisis utiliza información histórica obtenida de Yahoo Finance.

    **Precio actual:** ${precio_actual:,.2f}

    **Rendimiento acumulado durante el periodo analizado:**
    {rendimiento_total * 100:.2f}%

    En el modelo de Bernoulli, un día se considera **éxito**
    cuando el rendimiento diario es positivo y **fracaso**
    cuando es cero o negativo.
    """
)

if not close_1y.empty:

    st.markdown(
        f"""
        Durante el último año analizado:

        - Probabilidad de éxito:
          **{probabilidad_exito * 100:.2f}%**

        - Probabilidad de fracaso:
          **{probabilidad_fracaso * 100:.2f}%**
        """
    )

st.caption(
    "Fuente de datos: Yahoo Finance mediante yfinance."
)
