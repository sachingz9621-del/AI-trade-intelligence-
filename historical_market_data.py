import requests
import tomllib
from pathlib import Path
from datetime import date, timedelta


def get_access_token():

    secrets_path = Path.cwd() / ".streamlit" / "secrets.toml"

    with open(secrets_path, "rb") as file:
        secrets = tomllib.load(file)

    return secrets["UPSTOX_ACCESS_TOKEN"]


def get_historical_data(
    instrument_key="NSE_INDEX|Nifty 50",
    unit="days",
    interval="1",
    days=30
):

    try:

        access_token = get_access_token()

        to_date = date.today()
        from_date = to_date - timedelta(days=days)

        url = (
            f"https://api.upstox.com/v3/historical-candle/"
            f"{instrument_key}/{unit}/{interval}/"
            f"{to_date}/{from_date}"
        )

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        result = response.json()

        candles = result.get("data", {}).get("candles", [])

        if not candles:
            return None

        import pandas as pd

        df = pd.DataFrame(
            candles,
            columns=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Open Interest"
            ]
        )

        df["Timestamp"] = pd.to_datetime(df["Timestamp"])

        df = df.sort_values("Timestamp")

        return df

    except Exception as e:

        print("Historical Data Error:", e)

        return None