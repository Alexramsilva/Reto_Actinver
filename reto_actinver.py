import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
# ============================================================
# CONFIGURACIÓN
# ============================================================
st.image("UNRC.png", caption="Universidad Nacional Rosario Castellanos", width=300)
st.subheader("Licenciatura en Contaduría y Finanzas UNRC")

st.set_page_config(
    page_title="Reto Actinver 2026",
    page_icon="📈",
    layout="wide"
)

st.title("Reto Actinver 2026")
st.subheader("Análisis financiero con Yahoo Finance")

st.write(
    "Escriba la clave de Yahoo Finance del activo que desea analizar."
)

# ============================================================
# INGRESAR CLAVE DEL ACTIVO
# ============================================================

st.markdown("### 🔎 Selección del activo")

ticker = st.text_input(
    "Clave de Yahoo Finance:",
    placeholder="Ejemplo: BIMBOA.MX",
    help="Escriba el ticker exactamente como aparece en Yahoo Finance."
).strip().upper()

# ============================================================
# VALIDAR TICKER
# ============================================================

if not ticker:

    st.info(
        "👆 Escriba la clave de la acción en el campo anterior."
    )

    st.stop()

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
            "Dividend Yield": info.get("dividendYield"),
            "1Y Target Estimate": info.get("targetMeanPrice"),
                   }
    except Exception:

        return {
            "Price/Earnings": None,
            "Price/Book": None,
            "Debt/Equity": None,
            "Return on Equity": None,
            "Dividend Yield": None,
                               
                    }

   #####
@st.cache_data(ttl=3600)
def fecha_dividendo(ticker):
    try:
        activo = yf.Ticker(ticker)
        info = activo.info

        return {
            "Fecha Dividendo": datetime.fromtimestamp(info.get("exDividendDate")).strftime("%d/%m/%Y")
        }

    except Exception:
        return {
            "Fecha Dividendo": "No disponible"
        }
resultado = fecha_dividendo(ticker)

st.write("Fecha Dividendo:", resultado["Fecha Dividendo"])
##### 
    
# ============================================================
# OBTENER PRECIO DE CIERRE
# ============================================================

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

st.success(
    f"Activo analizado: **{ticker}**"
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

st.header("Indicadores fundamentales")

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

st.header("Rendimientos diarios")


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

st.header("Rendimientos anuales")


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

st.header("Precio histórico")


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

st.header("Rendimiento acumulado")


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

st.header("Rendimientos anuales")


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

st.header("Modelo de Bernoulli")


st.markdown(
    """
    Se define una variable aleatoria Bernoulli:

    **X = 1:** rendimiento diario positivo.

    **X = 0:** rendimiento diario cero o negativo.
    """
)


# ============================================================
# DATOS DEL ÚLTIMO AÑO
# ============================================================

try:

    datos_1y = descargar_ultimo_anio(ticker)

except Exception as e:

    st.warning(
        f"No fue posible descargar el último año: {e}"
    )

    datos_1y = pd.DataFrame()


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


    bernoulli_df["Daily Returns"] = (
        bernoulli_df["Close"].pct_change()
    )


    bernoulli_df = (
        bernoulli_df.dropna()
    )


    bernoulli_df["Daily Returns (%)"] = (
        bernoulli_df["Daily Returns"] * 100
    )


    bernoulli_df["Binary Returns"] = np.where(
        bernoulli_df["Daily Returns"] > 0,
        1,
        0
    )


    probabilidad_exito = (
        bernoulli_df["Binary Returns"].mean()
    )


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

st.header("Interpretación")


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
