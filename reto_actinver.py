
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Análisis Financiero - Yahoo Finance",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Análisis Financiero con Yahoo Finance")

st.markdown(
    """
    Aplicación para analizar precios, rendimientos,
    fundamentales y probabilidades de ganancia/pérdida.
    """
)


# ============================================================
# SELECCIÓN DEL TICKER
# ============================================================

st.sidebar.header("🔎 Selección del activo")

ticker = st.sidebar.text_input(
    "Ingrese la clave de Yahoo Finance:",
    value="SOFI",
    placeholder="Ejemplo: SOFI, BTC-USD, SLB, TSM, IWM, HOOD"
).strip().upper()


if not ticker:
    st.warning("Ingrese una clave de Yahoo Finance.")
    st.stop()


# ============================================================
# DESCARGAR DATOS
# ============================================================

@st.cache_data(ttl=3600)
def descargar_historicos(ticker):

    datos = yf.download(
        ticker,
        period="5y",
        auto_adjust=False,
        progress=False
    )

    return datos


@st.cache_data(ttl=3600)
def descargar_ultimo_anio(ticker):

    datos = yf.download(
        ticker,
        period="1y",
        auto_adjust=False,
        progress=False
    )

    return datos


# ============================================================
# CONSULTAR YAHOO FINANCE
# ============================================================

with st.spinner(
    f"Consultando Yahoo Finance para {ticker}..."
):

    try:

        historical_data = descargar_historicos(
            ticker
        )

        df1 = descargar_ultimo_anio(
            ticker
        )

        if historical_data.empty:

            st.error(
                f"No se encontraron datos para {ticker}. "
                "Verifique el ticker."
            )

            st.stop()

    except Exception as e:

        st.error(
            f"No fue posible consultar Yahoo Finance: {e}"
        )

        st.stop()


st.success(
    f"Ticker {ticker} consultado correctamente."
)


# ============================================================
# OBTENER PRECIO DE CIERRE
# ============================================================

def obtener_close(df, ticker):

    if df.empty:
        return pd.Series(dtype=float)

    # Caso MultiIndex
    if isinstance(df.columns, pd.MultiIndex):

        # Intentar obtener Close -> ticker
        try:

            close = df["Close"][ticker]

            return close

        except Exception:

            pass

        # Alternativa
        try:

            close = df.xs(
                "Close",
                axis=1,
                level=0
            )

            if isinstance(close, pd.DataFrame):
                return close.iloc[:, 0]

            return close

        except Exception:

            pass

    # Caso columnas normales
    if "Close" in df.columns:

        close = df["Close"]

        if isinstance(close, pd.DataFrame):

            return close.iloc[:, 0]

        return close

    return pd.Series(dtype=float)


# ============================================================
# PRECIO HISTÓRICO
# ============================================================

close_5y = obtener_close(
    historical_data,
    ticker
)

close_1y = obtener_close(
    df1,
    ticker
)


if close_5y.empty:

    st.error(
        "No fue posible obtener la columna Close."
    )

    st.stop()


# ============================================================
# DATAFRAME HISTÓRICO
# ============================================================

historical = pd.DataFrame(
    index=close_5y.index
)

historical["Close"] = close_5y


# ============================================================
# RENDIMIENTOS DIARIOS
# ============================================================

historical["Daily Return"] = (
    historical["Close"].pct_change()
)


# ============================================================
# RENDIMIENTO ACUMULADO
# ============================================================

historical["Cumulative Return"] = (
    1 + historical["Daily Return"]
).cumprod()


# ============================================================
# AÑO
# ============================================================

historical["Year"] = (
    historical.index.year
)


# ============================================================
# RENDIMIENTOS ANUALES
# ============================================================

annual_returns = (

    historical
    .groupby("Year")["Daily Return"]
    .apply(
        lambda x:
        (1 + x.dropna()).prod() - 1
    )
)


# ============================================================
# MÉTRICAS
# ============================================================

precio_actual = (
    historical["Close"].iloc[-1]
)

rendimiento_total = (
    historical["Cumulative Return"].iloc[-1]
    - 1
)

volatilidad_diaria = (
    historical["Daily Return"].std()
)

volatilidad_anual = (
    volatilidad_diaria * np.sqrt(252)
)


# ============================================================
# FUNDAMENTALES
# ============================================================

@st.cache_data(ttl=3600)
def obtener_fundamentales(ticker):

    activo = yf.Ticker(ticker)

    try:

        info = activo.info

    except Exception:

        info = {}

    fundamentals = {

        "Price/Earnings":
            info.get("trailingPE"),

        "Price/Book":
            info.get("priceToBook"),

        "Debt/Equity":
            info.get("debtToEquity"),

        "Return on Equity":
            info.get("returnOnEquity"),

        "Dividend Yield":
            info.get("dividendYield")
    }

    return fundamentals


try:

    fundamentals = obtener_fundamentales(
        ticker
    )

except Exception:

    fundamentals = {

        "Price/Earnings": None,

        "Price/Book": None,

        "Debt/Equity": None,

        "Return on Equity": None,

        "Dividend Yield": None
    }


# ============================================================
# PESTAÑAS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Resumen",
        "📈 Rendimientos",
        "🎲 Bernoulli",
        "📋 Datos"
    ]
)


# ============================================================
# TAB 1 - RESUMEN
# ============================================================

with tab1:

    st.header(
        f"Resumen financiero: {ticker}"
    )

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
            "Volatilidad diaria",
            f"{volatilidad_diaria * 100:.2f}%"
        )

    with col4:

        st.metric(
            "Volatilidad anual",
            f"{volatilidad_anual * 100:.2f}%"
        )


    # --------------------------------------------------------
    # FUNDAMENTALES
    # --------------------------------------------------------

    st.subheader(
        "📌 Fundamentales seleccionados"
    )

    fundamentals_df = pd.DataFrame(
        list(fundamentals.items()),
        columns=[
            "Indicador",
            "Valor"
        ]
    )


    def formato_fundamental(
        indicador,
        valor
    ):

        if valor is None:
            return "N/D"

        if pd.isna(valor):
            return "N/D"

        if indicador in [
            "Return on Equity",
            "Dividend Yield"
        ]:

            return f"{valor * 100:.2f}%"

        return f"{valor:.2f}"


    fundamentals_df["Valor"] = (
        fundamentals_df.apply(
            lambda row:
            formato_fundamental(
                row["Indicador"],
                row["Valor"]
            ),
            axis=1
        )
    )


    st.dataframe(
        fundamentals_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 2 - RENDIMIENTOS
# ============================================================

with tab2:

    st.header(
        f"📈 Rendimientos históricos de {ticker}"
    )


    # --------------------------------------------------------
    # PRECIO
    # --------------------------------------------------------

    st.subheader(
        "Precio histórico - últimos 5 años"
    )

    fig1, ax1 = plt.subplots(
        figsize=(12, 5)
    )

    ax1.plot(
        historical.index,
        historical["Close"],
        label="Precio de cierre"
    )

    ax1.set_title(
        f"Precio Histórico de {ticker}"
    )

    ax1.set_xlabel("Fecha")

    ax1.set_ylabel("Precio ($)")

    ax1.legend()

    ax1.grid(alpha=0.3)

    st.pyplot(fig1)

    plt.close(fig1)


    # --------------------------------------------------------
    # RENDIMIENTO ACUMULADO
    # --------------------------------------------------------

    st.subheader(
        "Rendimiento acumulado"
    )

    fig2, ax2 = plt.subplots(
        figsize=(12, 5)
    )

    ax2.plot(
        historical.index,
        historical["Cumulative Return"],
        label="Rendimiento acumulado"
    )

    ax2.set_title(
        f"Rendimiento Acumulado de {ticker}"
    )

    ax2.set_xlabel("Fecha")

    ax2.set_ylabel("Crecimiento")

    ax2.legend()

    ax2.grid(alpha=0.3)

    st.pyplot(fig2)

    plt.close(fig2)


    # --------------------------------------------------------
    # RENDIMIENTOS ANUALES
    # --------------------------------------------------------

    st.subheader(
        "Rendimientos anuales"
    )

    fig3, ax3 = plt.subplots(
        figsize=(12, 5)
    )

    annual_returns.plot(
        kind="bar",
        ax=ax3
    )

    ax3.axhline(
        y=0.10,
        linestyle="--",
        label="10%"
    )

    ax3.axhline(
        y=0,
        linestyle="-"
    )

    ax3.set_title(
        f"Rendimientos Anuales de {ticker}"
    )

    ax3.set_xlabel("Año")

    ax3.set_ylabel(
        "Rendimiento"
    )

    ax3.legend()

    ax3.grid(
        axis="y",
        alpha=0.3
    )

    st.pyplot(fig3)

    plt.close(fig3)


    # --------------------------------------------------------
    # TABLA ANUAL
    # --------------------------------------------------------

    annual_table = pd.DataFrame(
        annual_returns * 100
    )

    annual_table.columns = [
        "Rendimiento (%)"
    ]

    annual_table[
        "Rendimiento (%)"
    ] = annual_table[
        "Rendimiento (%)"
    ].round(2)


    st.dataframe(
        annual_table,
        use_container_width=True
    )


# ============================================================
# TAB 3 - BERNOULLI
# ============================================================

with tab3:

    st.header(
        f"🎲 Distribución de Bernoulli: {ticker}"
    )

    st.markdown(
        """
        Para cada día del último año:

        **1 = Ganancia**

        **0 = Pérdida o rendimiento no positivo**
        """
    )


    # --------------------------------------------------------
    # CREAR DATAFRAME BERNOULLI
    # --------------------------------------------------------

    if close_1y.empty:

        st.error(
            "No hay datos del último año."
        )

    else:

        bernoulli_df = pd.DataFrame(
            index=close_1y.index
        )

        bernoulli_df["Close"] = (
            close_1y
        )

        bernoulli_df[
            "Daily Returns"
        ] = (

            bernoulli_df["Close"]
            .pct_change() * 100
        )

        bernoulli_df = (
            bernoulli_df.dropna()
        )


        # ----------------------------------------------------
        # VARIABLE BERNOULLI
        # ----------------------------------------------------

        bernoulli_df[
            "Binary Returns"
        ] = np.where(

            bernoulli_df[
                "Daily Returns"
            ] > 0,

            1,

            0
        )


        # ----------------------------------------------------
        # PROBABILIDADES
        # ----------------------------------------------------

        probabilidad_exito = np.mean(
            bernoulli_df[
                "Binary Returns"
            ]
        )

        probabilidad_fracaso = (
            1 - probabilidad_exito
        )


        # ----------------------------------------------------
        # MÉTRICAS
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "P(Ganancia)",
                f"{probabilidad_exito * 100:.2f}%"
            )

        with col2:

            st.metric(
                "P(Pérdida)",
                f"{probabilidad_fracaso * 100:.2f}%"
            )

        with col3:

            st.metric(
                "Observaciones",
                f"{len(bernoulli_df):,}"
            )


        # ----------------------------------------------------
        # GRÁFICO BERNOULLI
        # ----------------------------------------------------

        valores_posibles = [
            0,
            1
        ]

        probabilidades = [
            probabilidad_fracaso,
            probabilidad_exito
        ]


        fig4, ax4 = plt.subplots(
            figsize=(8, 5)
        )


        barras = ax4.bar(
            valores_posibles,
            probabilidades
        )


        ax4.set_title(
            f"Distribución de Bernoulli\n"
            f"Rendimientos de {ticker}"
        )


        ax4.set_xlabel(
            "Resultado"
        )


        ax4.set_ylabel(
            "Probabilidad"
        )


        ax4.set_xticks(
            [0, 1],
            [
                "Pérdida",
                "Ganancia"
            ]
        )


        ax4.set_ylim(
            0,
            max(probabilidades) * 1.25
        )


        ax4.grid(
            axis="y",
            alpha=0.3
        )


        # ----------------------------------------------------
        # ETIQUETAS
        # ----------------------------------------------------

        for barra, prob in zip(
            barras,
            probabilidades
        ):

            ax4.text(

                barra.get_x()
                + barra.get_width() / 2,

                barra.get_height(),

                f"{prob * 100:.2f}%",

                ha="center",

                va="bottom",

                fontsize=11
            )


        st.pyplot(fig4)

        plt.close(fig4)


        # ----------------------------------------------------
        # INTERPRETACIÓN
        # ----------------------------------------------------

        st.subheader(
            "📝 Interpretación"
        )

        st.write(
            f"""
            Para **{ticker}**, durante el último año,
            la probabilidad histórica estimada de obtener
            un rendimiento diario positivo fue de:

            **{probabilidad_exito * 100:.2f}%**

            mientras que la probabilidad de obtener un
            rendimiento diario no positivo fue de:

            **{probabilidad_fracaso * 100:.2f}%**
            """
        )


# ============================================================
# TAB 4 - DATOS
# ============================================================

with tab4:

    st.header(
        "📋 Datos"
    )


    # --------------------------------------------------------
    # DATOS 5 AÑOS
    # --------------------------------------------------------

    st.subheader(
        "Datos históricos de 5 años"
    )

    st.dataframe(
        historical,
        use_container_width=True
    )


    # --------------------------------------------------------
    # DESCARGA
    # --------------------------------------------------------

    csv = (
        historical
        .to_csv()
        .encode("utf-8")
    )


    st.download_button(

        label="⬇️ Descargar datos históricos",

        data=csv,

        file_name=(
            f"{ticker}_historico_5y.csv"
        ),

        mime="text/csv"
    )


    # --------------------------------------------------------
    # DATOS BERNOULLI
    # --------------------------------------------------------

    if not close_1y.empty:

        st.subheader(
            "Datos utilizados para Bernoulli"
        )

        st.dataframe(
            bernoulli_df,
            use_container_width=True
        )


        csv_bernoulli = (
            bernoulli_df
            .to_csv()
            .encode("utf-8")
        )


        st.download_button(

            label="⬇️ Descargar datos Bernoulli",

            data=csv_bernoulli,

            file_name=(
                f"{ticker}_bernoulli_1y.csv"
            ),

            mime="text/csv"
        )


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.divider()

st.caption(
    "Fuente: Yahoo Finance mediante yfinance. "
    "Los datos de mercado y fundamentales pueden actualizarse."
)

