from flask import Flask
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import os

app = Flask(__name__)

cities_file = "/usr/src/app/cities.csv"
worldcities_file = "/usr/src/app/worldcities.csv"

# -------------------------------
# Helpers
# -------------------------------
def country_to_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


def load_data():
    # User input (NEW: 3 columns only)
    df = pd.read_csv(
        cities_file,
        sep=";",
        usecols=["group", "city", "country"]
    )

    # Static reference dataset
    cities = pd.read_csv(worldcities_file)

    # Normalize
    df["city"] = df["city"].str.strip().str.lower()
    df["country"] = df["country"].str.strip().str.lower()

    cities["city"] = cities["city"].str.strip().str.lower()
    cities["country"] = cities["country"].str.strip().str.lower()

    df["group"] = df["group"].astype(int)

    # Merge coordinates
    merged = df.merge(
        cities[["city", "country", "lat", "lng"]],
        on=["city", "country"],
        how="left"
    )

    merged = merged.dropna(subset=["lat", "lng"])

    return merged


def build_map(df):
    # Country highlight
    countries_df = pd.DataFrame({
        "country": df["country"].str.title().unique()
    })

    countries_df["iso_alpha"] = countries_df["country"].map(country_to_iso3)
    countries_df = countries_df.dropna(subset=["iso_alpha"])

    fig = px.choropleth(
        countries_df,
        locations="iso_alpha",
        color_discrete_sequence=["burlywood"],
        projection="natural earth"
    )

    # City markers by group
    groups = sorted(df["group"].unique())

    colors = {
        1: "green",
        2: "blue",
        3: "orange",
        4: "yellow",
        5: "red"
    }

    for g in groups:
        group_df = df[df["group"] == g]

        fig.add_trace(
            go.Scattergeo(
                lon=group_df["lng"],
                lat=group_df["lat"],
                text=group_df["city"].str.title(),
                mode="markers",
                marker=dict(
                    size=8,
                    color=colors.get(g, "black"),
                    line=dict(width=0.5, color="black")
                ),
                name=f"Group {g} ({len(group_df)})"
            )
        )

    fig.update_geos(
        showcountries=True,
        showland=True,
        landcolor="wheat",
        showocean=True,
        oceancolor="lightskyblue",
        lakecolor="lightskyblue",
        projection_type="natural earth"
    )

    fig.update_layout(
        title="My Cities Map",
        legend=dict(title="Groups"),
        coloraxis_showscale=False
    )

    return fig.to_html(full_html=True)


# -------------------------------
# Route
# -------------------------------
@app.route("/")
def home():
    df = load_data()
    return build_map(df)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)