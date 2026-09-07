import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Reto Actinver",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Reto Actinver")
st.subheader("Análisis financiero con Yahoo Finance")

st.write(
    "Seleccione una acción o activo financiero para realizar el análisis."
)

# ============================================================
# SELECCIÓN DEL ACTIVO
# ============================================================

st.sidebar.header("🔎 Selección del activo")

opciones = [
    "SOFI",
    "SLB",
    "TSM",
    "IWM",
    "HOOD",
    "BTC-USD",
    "Otra clave"
]

opcion = st.sidebar.selectbox(
    "Seleccione el activo:",
    opciones,
    index=0
)

if opcion == "Otra clave":

    ticker = st.sidebar.text_input(
        "Clave de Yahoo Finance:",
        value="AAPL",
        placeholder="Ejemplo: AAPL, MSFT, NVDA"
    ).strip().upper()

else:

    ticker = opcion

st.sidebar.markdown("---")

st.sidebar.success(
    f"Activo seleccionado: {ticker}"
)

# ============================================================
# FUNCIONES
# ============================================================

@st.cache_data(ttl=3600)
def descargar_historicos(ticker):

    return yf.download(
        ticker,
        period="5y",
        auto_adjust=False,
        progress=False
    )


@st.cache_data(ttl=3600)
def descargar_ultimo_anio(ticker):

    return yf.download(
        ticker,
        period="1y",
        auto_adjust=False,
        progress=False
    )


@st.cache_data(ttl=3600)
def obtener_fundamentales(ticker):

    try:

        activo = yf.Ticker(ticker)

        info = activo.info

        return {
            "Price/Earnings": info.get("trailingPE"),
            "Price/Book": info.get("priceToBook"),
            "Debt/Equity": info.get("debtToEquity"),
            "Return on Equity": info.get("returnOnEquity"),
            "Dividend Yield": info.get("dividendYield")
        }

    except Exception:

        return {
            "Price/Earnings": None,
            "Price/Book": None,
            "Debt/Equity": None,
            "Return on Equity": None,
            "Dividend Yield": None
        }


def obtener_close(df):

    if df.empty:
        return pd.Series(dtype=float)

    # --------------------------------------------------------
    # yfinance puede devolver MultiIndex
    # --------------------------------------------------------

    if isinstance(df.columns, pd.MultiIndex):

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

    # --------------------------------------------------------
    # DataFrame normal
    # --------------------------------------------------------

    if "Close" in df.columns:

        close = df["Close"]

        if isinstance(close, pd.DataFrame):

            close = close.iloc[:, 0]

        return close

    return pd.Series(dtype=float)


# ============================================================
# DESCARGAR INFORMACIÓN
# ============================================================

with st.spinner(
    f"Consultando Yahoo Finance para {ticker}..."
):

    try:

        datos_5y = descargar_historicos(ticker)

    except Exception as e:

        st.error(
            f"Error al consultar Yahoo Finance: {e}"
        )

        st.stop()


# ============================================================
# VALIDACIÓN
# ============================================================

if datos_5y.empty:

    st.error(
        f"""
        No se encontraron datos para **{ticker}**.

        Verifique que la clave de Yahoo Finance sea correcta.
        """
    )

    st.stop()


close_5y = obtener_close(datos_5y)

close_5y = close_5y.dropna()


if close_5y.empty:

    st.error(
        "No fue posible obtener los precios de cierre."
    )

    st.stop()


# ============================================================
# ACTIVO SELECCIONADO
# ============================================================

st.info(
    f"📌 Activo analizado: **{ticker}**"
)


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

precio_actual = float(close_5y.iloc[-1])

precio_inicial = float(close_5y.iloc[0])

rendimiento_total = (
    precio_actual / precio_inicial - 1
)

maximo = float(close_5y.max())

minimo = float(close_5y.min())


col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Precio actual",
        f"${precio_actual:,.2f}"
    )

with col2:

    st.metric(
        "Rendimiento 5 años",
        f"{rendimiento_total * 100:.2f}%"
    )

with col3:

    st.metric(
        "Máximo",
        f"${maximo:,.2f}"
    )

with col4:

    st.metric(
        "Mínimo",
        f"${minimo:,.2f}"
    )


# ============================================================
# 1. FUNDAMENTALES
# ============================================================

st.header("1️⃣ Indicadores fundamentales")

fundamentales = obtener_fundamentales(ticker)

fundamentales_df = pd.DataFrame(
    {
        "Indicador": fundamentales.keys(),
        "Valor": fundamentales.values()
    }
)


def formato_valor(x):

    if x is None:
        return "N/D"

    try:

        if pd.isna(x):
            return "N/D"

    except Exception:

        pass

    return x


fundamentales_df["Valor"] = (
    fundamentales_df["Valor"]
    .apply(formato_valor)
)


st.dataframe(
    fundamentales_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 2. RENDIMIENTOS DIARIOS
# ============================================================

st.header("2️⃣ Rendimientos diarios")

historical = pd.DataFrame(
    {
        "Close": close_5y
    }
)

historical["Daily Return"] = (
    historical["Close"].pct_change()
)

historical["Cumulative Return"] = (
    1 + historical["Daily Return"]
).cumprod()

historical["Year"] = (
    historical.index.year
)


st.dataframe(
    historical.tail(10),
    use_container_width=True
)


# ============================================================
# 3. RENDIMIENTOS ANUALES
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

annual_returns_df = pd.DataFrame(
    {
        "Año": annual_returns.index,
        "Rendimiento (%)":
            annual_returns.values * 100
    }
)


st.dataframe(
    annual_returns_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 4. PRECIO HISTÓRICO
# ============================================================

st.header("4️⃣ Precio histórico")

fig1, ax1 = plt.subplots(
    figsize=(12, 5)
)

ax1.plot(
    historical.index,
    historical["Close"]
)

ax1.set_title(
    f"Precio de cierre - {ticker}"
)

ax1.set_xlabel("Fecha")

ax1.set_ylabel("Precio")

ax1.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

st.pyplot(fig1)

plt.close(fig1)


# ============================================================
# 5. RENDIMIENTO ACUMULADO
# ============================================================

st.header("5️⃣ Rendimiento acumulado")

fig2, ax2 = plt.subplots(
    figsize=(12, 5)
)

ax2.plot(
    historical.index,
    historical["Cumulative Return"]
)

ax2.set_title(
    f"Rendimiento acumulado - {ticker}"
)

ax2.set_xlabel("Fecha")

ax2.set_ylabel(
    "Crecimiento de $1"
)

ax2.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

st.pyplot(fig2)

plt.close(fig2)


# ============================================================
# 6. RENDIMIENTOS ANUALES
# ============================================================

st.header("6️⃣ Rendimientos anuales")

fig3, ax3 = plt.subplots(
    figsize=(12, 5)
)

ax3.bar(
    annual_returns_df["Año"].astype(str),
    annual_returns_df["Rendimiento (%)"]
)

ax3.set_title(
    f"Rendimientos anuales - {ticker}"
)

ax3.set_xlabel("Año")

ax3.set_ylabel(
    "Rendimiento (%)"
)

ax3.axhline(
    y=0,
    linewidth=1
)

ax3.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

st.pyplot(fig3)

plt.close(fig3)


# ============================================================
# 7. MODELO DE BERNOULLI
# ============================================================

st.header("7️⃣ Modelo de Bernoulli")

st.markdown(
    """
    Se define una variable aleatoria Bernoulli:

    **X = 1:** rendimiento diario positivo.

    **X = 0:** rendimiento diario cero o negativo.
    """
)


datos_1y = descargar_ultimo_anio(ticker)

close_1y = obtener_close(datos_1y)

close_1y = close_1y.dropna()


if close_1y.empty:

    st.warning(
        "No fue posible obtener información del último año."
    )

else:

    bernoulli_df = pd.DataFrame(
        {
            "Close": close_1y
        }
    )

    # Rendimiento diario
    bernoulli_df["Daily Returns"] = (
        bernoulli_df["Close"].pct_change()
    )

    bernoulli_df = (
        bernoulli_df.dropna()
    )

    # Rendimiento en porcentaje
    bernoulli_df["Daily Returns (%)"] = (
        bernoulli_df["Daily Returns"] * 100
    )

    # Variable Bernoulli
    bernoulli_df["Binary Returns"] = np.where(
        bernoulli_df["Daily Returns"] > 0,
        1,
        0
    )

    # Probabilidad de éxito
    probabilidad_exito = (
        bernoulli_df["Binary Returns"].mean()
    )

    # Probabilidad de fracaso
    probabilidad_fracaso = (
        1 - probabilidad_exito
    )


    # ========================================================
    # PROBABILIDADES
    # ========================================================

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
    # GRÁFICA BERNOULLI
    # ========================================================

    st.subheader(
        "Distribución Bernoulli"
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
        f"Probabilidad de éxito y fracaso - {ticker}"
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

    for i, valor in enumerate(
        probabilidades
    ):

        ax4.text(
            i,
            valor + 0.02,
            f"{valor * 100:.2f}%",
            ha="center"
        )

    plt.tight_layout()

    st.pyplot(fig4)

    plt.close(fig4)


    # ========================================================
    # TABLA BERNOULLI
    # ========================================================

    st.subheader(
        "Últimas observaciones"
    )

    st.dataframe(
        bernoulli_df[
            [
                "Close",
                "Daily Returns (%)",
                "Binary Returns"
            ]
        ].tail(20),
        use_container_width=True
    )


# ============================================================
# 8. INTERPRETACIÓN
# ============================================================

st.header("8️⃣ Interpretación")

st.markdown(
    f"""
    ### Activo analizado: `{ticker}`

    **Precio actual:** ${precio_actual:,.2f}

    **Rendimiento acumulado:** {rendimiento_total * 100:.2f}%

    El modelo de Bernoulli considera como éxito un día
    en el que el rendimiento del activo es positivo.
    """
)

if not close_1y.empty:

    st.markdown(
        f"""
        Para el último año:

        - Probabilidad de éxito: **{probabilidad_exito * 100:.2f}%**
        - Probabilidad de fracaso: **{probabilidad_fracaso * 100:.2f}%**
        """
    )


# ============================================================
# PIE
# ============================================================

st.markdown("---")

st.caption(
    "Fuente: Yahoo Finance | Biblioteca: yfinance"
)
