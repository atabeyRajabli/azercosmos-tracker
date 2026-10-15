import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Azercosmos brand colors
COLORS = {
    "Azerspace-1": "#00AEEF",   # Azercosmos blue
    "Azerspace-2": "#0057A8",   # deeper blue
    "Azersky":     "#E8B84B",   # warm gold for Earth observation
}

BAKU_LAT = 40.4093
BAKU_LON = 49.8671


def build_ground_track_map(tracks: dict[str, pd.DataFrame],
                           positions: dict[str, dict]) -> go.Figure:
    """
    Build an interactive Plotly globe showing ground tracks + current positions.
    tracks:    {sat_name: DataFrame with lat/lon columns}
    positions: {sat_name: {latitude, longitude, altitude_km}}
    """
    fig = go.Figure()

    # Ground tracks
    for name, df in tracks.items():
        color = COLORS.get(name, "#FFFFFF")
        fig.add_trace(go.Scattergeo(
            lat=df["lat"],
            lon=df["lon"],
            mode="lines",
            name=f"{name} track",
            line=dict(color=color, width=1.5),
            opacity=0.6,
            hoverinfo="skip",
        ))

    # Current positions
    for name, pos in positions.items():
        color = COLORS.get(name, "#FFFFFF")
        fig.add_trace(go.Scattergeo(
            lat=[pos["latitude"]],
            lon=[pos["longitude"]],
            mode="markers+text",
            name=name,
            marker=dict(size=12, color=color, symbol="circle",
                        line=dict(color="white", width=1.5)),
            text=[name],
            textposition="top center",
            textfont=dict(color=color, size=11),
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Lat: %{{lat:.2f}}°<br>"
                f"Lon: %{{lon:.2f}}°<br>"
                f"Alt: {pos['altitude_km']:.0f} km<extra></extra>"
            ),
        ))

    # Baku ground station
    fig.add_trace(go.Scattergeo(
        lat=[BAKU_LAT],
        lon=[BAKU_LON],
        mode="markers+text",
        name="Baku (Ground Station)",
        marker=dict(size=10, color="#FF4444", symbol="triangle-up"),
        text=["Baku"],
        textposition="bottom center",
        textfont=dict(color="#FF4444", size=11),
        hovertemplate="<b>Baku Ground Station</b><br>40.41°N, 49.87°E<extra></extra>",
    ))

    fig.update_layout(
        geo=dict(
            showland=True,
            landcolor="#1a1f2e",
            showocean=True,
            oceancolor="#0d1117",
            showcountries=True,
            countrycolor="#333a4d",
            showframe=False,
            projection_type="natural earth",
            bgcolor="#0d1117",
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white"),
        legend=dict(bgcolor="#1a1f2e", bordercolor="#333a4d", borderwidth=1),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
    )

    return fig


def build_pass_table(passes: list[dict]) -> pd.DataFrame:
    """Convert pass list to a clean DataFrame for display."""
    if not passes:
        return pd.DataFrame(columns=["Rise Time (UTC)", "Max Elevation", "Azimuth", "Set Time (UTC)", "Duration"])
    
    rows = []
    for p in passes:
        rows.append({
            "Rise Time (UTC)":  p.get("rise_time", "—"),
            "Max Elevation":    f"{p.get('max_elevation_deg', 0):.1f}°",
            "Azimuth":          f"{p.get('azimuth_deg', 0):.1f}°",
            "Set Time (UTC)":   p.get("set_time", "—"),
            "Duration (min)":   p.get("duration_minutes", 0),
        })
    return pd.DataFrame(rows)


def build_elevation_chart(passes: list[dict]) -> go.Figure:
    """
    Bar chart of max elevations for upcoming passes.
    """
    if not passes:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="white"),
        )
        return fig
    
    labels = [f"Pass {i+1}\n{p['rise_time'][5:16]}" for i, p in enumerate(passes)]
    elevations = [p.get("max_elevation_deg", 0) for p in passes]
    colors_list = ["#E8B84B" if e >= 45 else "#00AEEF" if e >= 20 else "#555" for e in elevations]
    
    fig = go.Figure(go.Bar(
        x=labels,
        y=elevations,
        marker_color=colors_list,
        hovertemplate="Pass %{x}<br>Max elevation: %{y:.1f}°<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Azersky Pass Elevations over Baku", font=dict(color="white", size=14)),
        yaxis=dict(title="Elevation (°)", range=[0, 90], gridcolor="#333a4d", color="white"),
        xaxis=dict(color="white"),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white"),
        margin=dict(l=40, r=20, t=40, b=40),
        height=300,
    )
    fig.add_hline(y=10, line_dash="dot", line_color="#666",
                  annotation_text="Min horizon (10°)", annotation_font_color="#666")
    
    return fig
