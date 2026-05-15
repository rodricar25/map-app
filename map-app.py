from flask import Flask, render_template_string
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import os

app = Flask(__name__)

# -------------------------------
# Parameters
# -------------------------------
#BASE_PATH = r"C:\_rodricar\e-learning\work\travel_2026"
BASE_PATH = r"/usr/src/app"
cities_file = os.path.join(BASE_PATH, "cities.csv")
worldcities_file = os.path.join(BASE_PATH, "worldcities.csv")

MAX_GROUP = 4
SHOW_NAMES_ON_MAP = False
MAP_PROJECTION = "natural earth"

GROUPS = {
    1: {"name": "Group One", "color": "green"},
    2: {"name": "Group Two", "color": "blue"},
    3: {"name": "Group Three", "color": "orange"},
    4: {"name": "Group Four", "color": "yellow"},
}

GROUP_NAMES = {k: v["name"] for k, v in GROUPS.items()}

# -------------------------------
# Helpers
# -------------------------------
def normalize_text(df, cols):
    for col in cols:
        df[col] = df[col].str.strip().str.lower()
    return df


def country_to_iso3(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None


def build_figure():
    # Load data
    cities = pd.read_csv(worldcities_file)
    df = pd.read_csv(cities_file, sep=";", encoding="latin1")
    df = df[df["group"] <= MAX_GROUP]

    # Normalize
    df = normalize_text(df, ["city", "country"])
    cities = normalize_text(cities, ["city", "country"])

    # Merge
    merged_df = df.merge(
        cities[["city", "country", "lat", "lng", "population"]],
        on=["city", "country"],
        how="left"
    )

    df = merged_df.dropna(subset=["lat", "lng"]).copy()

    df["hover_text"] = df["city"].str.title() + ", " + df["country"].str.upper()
    df["group"] = df["group"].astype(int)

    df = (
        df.groupby(["city", "country"], as_index=False)
          .agg(
              group=("group", "min"),
              lat=("lat", "first"),
              lng=("lng", "first"),
              hover_text=("hover_text", "first")
          )
    )

    df["group_name"] = df["group"].map(GROUP_NAMES)

    counts = df.groupby("group").size().to_dict()

    # Countries highlight
    countries_df = pd.DataFrame({
        "country": df["country"].str.title().unique()
    })
    countries_df["iso_alpha"] = countries_df["country"].map(country_to_iso3)
    countries_df["highlight"] = 1
    countries_df = countries_df.dropna(subset=["iso_alpha"])

    # Base map
    fig = px.choropleth(
        countries_df,
        locations="iso_alpha",
        color="highlight",
        color_continuous_scale=["burlywood", "sienna"],
        range_color=[0, 1],
        projection=MAP_PROJECTION,
        hover_name = "country"
    )

    fig.update_traces(
        hovertemplate="%{hovertext}<extra></extra>"
    )

    # City markers
    for group_id, group_info in GROUPS.items():
        group_df = df[df["group"] == group_id]

        fig.add_trace(
            go.Scattergeo(
                lon=group_df["lng"],
                lat=group_df["lat"],
                text=group_df["hover_text"],
                marker=dict(
                    size=8,
                    color=group_info["color"],
                    opacity=0.9,
                    line=dict(width=0.5, color="black")
                ),
                mode="markers",
                name=f"{group_info['name']} ({counts.get(group_id, 0)})",
                hoverinfo="text"
            )
        )

    fig.update_geos(
        showcountries=True,
        countrycolor="black",
        showland=True,
        landcolor="wheat",
        showocean=True,
        oceancolor="lightskyblue",
        showlakes=True,
        lakecolor="lightskyblue",
        showcoastlines=True,
        coastlinecolor="black",
        projection_type=MAP_PROJECTION
    )

    fig.update_layout(
        title="<b>Cities Around the World</b>",
        legend=dict(x=1.1),
        coloraxis_showscale=False
    )

    return fig


# -------------------------------
# Flask route
# -------------------------------
@app.route("/")
def index():
    fig = build_figure()

    # Convert Plotly figure to HTML
    graph_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return render_template_string("""
    <html>
        <head>
            <title>My World Map</title>
        </head>
        <body>
            <h1>My World Map</h1>
            {{ graph|safe }}
        </body>
    </html>
    """, graph=graph_html)


if __name__ == "__main__":
    app.run(debug=True)
