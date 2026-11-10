
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import requests 

API = "https://api.coingecko.com/api/v3"

st.set_page_config(
    page_title="Crypto Tracker",
    page_icon="🪙",
    layout="wide"
)

@st.cache_data(ttl=60)
def get_coins(currency):

    url = API + "/coins/markets"

    parameters = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "price_change_percentage": "24h,7d"
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    coins = pd.DataFrame(data)

    return coins


@st.cache_data(ttl=300)
def get_coin_history(coin_id, currency, days):

    url = API + "/coins/" + coin_id + "/market_chart"

    parameters = {
        "vs_currency": currency,
        "days": days
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    history = pd.DataFrame(
        data["prices"],
        columns=["Date", "Price"]
    )

    history["Date"] = pd.to_datetime(
        history["Date"],
        unit="ms"
    )

    return history


st.sidebar.title("🪙 Crypto Tracker")

currency = st.sidebar.selectbox(
    "Select Currency",
    ["usd", "pkr", "eur", "gbp"]
)

days = st.sidebar.selectbox(
    "Select History",
    [1, 7, 30, 90, 180, 365]
)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()


try:
    coins = get_coins(currency)

except requests.exceptions.RequestException as error:
    st.error("Unable to load cryptocurrency data.")
    st.write(error)
    st.stop()


coin_names = dict(
    zip(coins["name"], coins["id"])
)


default_coins = [
    name for name in ["Bitcoin", "Ethereum", "Solana"]
    if name in coin_names
]


watchlist = st.sidebar.multiselect(
    "Select Coins",
    list(coin_names.keys()),
    default=default_coins
)



st.title("🪙 Cryptocurrency Dashboard")

# Display current prices
if watchlist:

    columns = st.columns(len(watchlist))

    for column, name in zip(columns, watchlist):

        coin = coins[
            coins["id"] == coin_names[name]
        ].iloc[0]

        column.metric(
            name,
            f"{coin['current_price']:,.2f} {currency.upper()}",
            f"{coin['price_change_percentage_24h']:.2f}%"
        )

else:
    st.info("Please select a cryptocurrency.")


price_tab, compare_tab, market_tab = st.tabs(
    ["📈 Price Chart", "⚖️ Compare", "🌍 Market"]
)



with price_tab:

    if watchlist:

        selected_coin = st.selectbox(
            "Choose a Coin",
            watchlist
        )

        try:
            history = get_coin_history(
                coin_names[selected_coin],
                currency,
                days
            )

            if not history.empty:

                
                chart = px.line(
                    history,
                    x="Date",
                    y="Price",
                    title=selected_coin + " Price History"
                )

                st.plotly_chart(
                    chart,
                    use_container_width=True
                )

                
                high_price = history["Price"].max()
                low_price = history["Price"].min()

                
                first_price = history["Price"].iloc[0]
                last_price = history["Price"].iloc[-1]

                percentage = (
                    (last_price / first_price) - 1
                ) * 100 if first_price else 0

                col1, col2, col3 = st.columns(3)

                col1.metric("Highest Price", f"{high_price:,.2f}")
                col2.metric("Lowest Price", f"{low_price:,.2f}")
                col3.metric("Price Change", f"{percentage:.2f}%")

            else:
                st.warning("No historical data available.")

        except requests.exceptions.RequestException:
            st.error("Unable to load price history.")



with compare_tab:

    if len(watchlist) >= 2:

        all_data = []

        for name in watchlist:

            try:
                history = get_coin_history(
                    coin_names[name],
                    currency,
                    days
                )

                if history.empty:
                    continue

                
                history["Performance"] = (
                    history["Price"] /
                    history["Price"].iloc[0]
                ) * 100

                history["Coin"] = name

                all_data.append(history)

            except requests.exceptions.RequestException:
                st.warning("Could not load " + name)

        if all_data:

            comparison = pd.concat(all_data)

            chart = px.line(
                comparison,
                x="Date",
                y="Performance",
                color="Coin",
                title="Cryptocurrency Performance Comparison"
            )

            st.plotly_chart(
                chart,
                use_container_width=True
            )

        else:
            st.warning("No comparison data available.")

    else:
        st.info("Select at least two coins to compare.")



with market_tab:

    market_data = coins[
        [
            "market_cap_rank",
            "name",
            "symbol",
            "current_price",
            "market_cap",
            "total_volume",
            "price_change_percentage_24h",
            "price_change_percentage_7d_in_currency"
        ]
    ]

    
    market_data = market_data.rename(
        columns={
            "market_cap_rank": "Rank",
            "name": "Name",
            "symbol": "Symbol",
            "current_price": "Current Price",
            "market_cap": "Market Cap",
            "total_volume": "24h Volume",
            "price_change_percentage_24h": "24h Change %",
            "price_change_percentage_7d_in_currency": "7d Change %"
        }
    )

    st.dataframe(
        market_data,
        use_container_width=True,
        hide_index=True
    )



st.caption(
    "Data provided by CoinGecko API | "
    "Cryptocurrency Tracker Project | "
    "Not financial advice"
)
