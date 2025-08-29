import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta


def plot_radon():
    # Load and process data
    radon_levels = pd.read_csv("/home/grg/radon_levels.csv")
    radon_levels["timestamp"] = pd.to_datetime(radon_levels["timestamp"])
    last_day = datetime.now() - timedelta(days=1)
    recent_data = radon_levels[radon_levels["timestamp"] > last_day].sort_values(
        "timestamp", ascending=False
    )

    # Create the plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot radon levels
    ax1.plot(
        recent_data["timestamp"],
        recent_data["radon_level"],
        marker="o",
        linestyle="-",
        color="blue",
        label="Radon Level",
    )
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Radon Level", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.axhline(
        y=300, color="red", linestyle="--", linewidth=2, label="Seuil critique (300)"
    )
    ax1.axhline(
        y=100, color="orange", linestyle="--", linewidth=2, label="Alerte (100)"
    )
    ax1.grid(True)

    # Check if temperature column exists and plot
    if (
        "temperature" in recent_data.columns
        and not recent_data["temperature"].isnull().all()
    ):
        ax2 = ax1.twinx()  # create secondary y-axis
        ax2.plot(
            recent_data["timestamp"],
            recent_data["temperature"],
            marker="x",
            linestyle="--",
            color="green",
            label="Temperature (°C)",
        )
        ax2.set_ylabel("Temperature (°C)", color="green")
        ax2.tick_params(axis="y", labelcolor="green")

    # Check if windspeed column exists and plot
    if "wind" in recent_data.columns and not recent_data["wind"].isnull().all():
        ax3 = ax1.twinx()  # create secondary y-axis
        ax3.plot(
            recent_data["timestamp"],
            recent_data["wind"],
            marker="x",
            linestyle="--",
            color="magenta",
            label="Windspeed",
        )
        ax3.set_ylabel("Windspeed", color="magenta")
        ax3.tick_params(axis="y", labelcolor="magenta")
    plt.xticks(rotation=45)

    # Dernier timepoint
    latest_timestamp = recent_data["timestamp"].max()
    last_minute_unit = latest_timestamp.minute % 10  # chiffre des unités
    last_second = latest_timestamp.second
    delay_seconds = (last_second + 5) % 60  # rajoute 5 secondes

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    # Convert image to base64
    encoded_img = base64.b64encode(buf.read()).decode("utf-8")
    img_html = (
        f'<img src="data:image/png;base64,{encoded_img}" alt="Radon Levels Plot">'
    )

    # Generate HTML response
    table_html = recent_data.to_html(index=False)
    script = f"""<script>
        function scheduleRefresh() {{
            const now = new Date();
            let targetMinuteUnit = {last_minute_unit};
            let targetSecond = {delay_seconds};
            let delay;

            let nextTarget = new Date(now);
            nextTarget.setSeconds(targetSecond);
            nextTarget.setMilliseconds(0);

            while (nextTarget.getMinutes() % 10 !== targetMinuteUnit || nextTarget <= now) {{
                nextTarget.setMinutes(nextTarget.getMinutes() + 1);
            }}

            delay = nextTarget - now;
            console.log("Prochain rafraîchissement dans", delay / 1000, "secondes");
            setTimeout(() => {{
                window.location.reload();
            }}, delay);
        }}
        scheduleRefresh();
    </script>
    """

    full_html = (
        f"{script}<h1>Radon Levels</h1>{img_html}<h2>Data Table</h2>{table_html}"
    )
    return full_html


def plot_radon_old():
    # Load and process data
    radon_levels = pd.read_csv("/home/grg/radon_levels.csv")
    radon_levels["timestamp"] = pd.to_datetime(
        radon_levels["timestamp"]
    )  # Ensure timestamp is datetime
    last_day = datetime.now() - timedelta(days=1)
    recent_data = radon_levels[radon_levels["timestamp"] > last_day].sort_values(
        "timestamp", ascending=False
    )

    # Create the plot
    fig, ax = plt.subplots()
    ax.plot(
        recent_data["timestamp"], recent_data["radon_level"], marker="o", linestyle="-"
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Radon Level")
    ax.set_title("Radon Level Over the Last 24 Hours")
    ax.grid(True)
    plt.xticks(rotation=45)

    # Dernier timepoint
    latest_timestamp = recent_data["timestamp"].max()
    last_minute_unit = latest_timestamp.minute % 10  # chiffre des unités
    last_second = latest_timestamp.second
    delay_seconds = (last_second + 5) % 60  # on rajoute 5 secondes

    # Ajouter les lignes horizontales
    ax.axhline(
        y=300, color="red", linestyle="--", linewidth=2, label="Seuil critique (300)"
    )
    ax.axhline(y=100, color="yellow", linestyle="--", linewidth=2, label="Alerte (100)")

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    # Convert image to base64
    encoded_img = base64.b64encode(buf.read()).decode("utf-8")
    img_html = (
        f'<img src="data:image/png;base64,{encoded_img}" alt="Radon Levels Plot">'
    )

    # Generate HTML response
    table_html = recent_data.to_html(index=False)
    script = f"""<script>
        function scheduleRefresh() {{
            const now = new Date();
            let targetMinuteUnit = {last_minute_unit};
            let targetSecond = {delay_seconds};
            let delay;

            // Calcul du moment exact du prochain refresh
            let nextTarget = new Date(now);
            nextTarget.setSeconds(targetSecond);
            nextTarget.setMilliseconds(0);

            while (nextTarget.getMinutes() % 10 !== targetMinuteUnit || nextTarget <= now) {{
                nextTarget.setMinutes(nextTarget.getMinutes() + 1);
            }}

            delay = nextTarget - now;
            console.log("Prochain rafraîchissement dans", delay / 1000, "secondes");
            setTimeout(() => {{
                window.location.reload();
            }}, delay);
        }}
        scheduleRefresh();
    </script>
        """

    full_html = (
        f"{script}<h1>Radon Levels</h1>{img_html}<h2>Data Table</h2>{table_html}"
    )
    return full_html
