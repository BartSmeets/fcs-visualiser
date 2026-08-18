"""Plot generation for the FCS Visualiser."""
 
import plotly.express as px
import plotly.graph_objects as go

from .state import AppState


def generate_fig(state: AppState, spectrum_type: str, pointer: bool, pointer_value: float):
    def prepare_axes(fig, xlabel, ylabel):
        fig.update_layout(
            xaxis_title=xlabel,
            yaxis_title=ylabel,
            legend={"yanchor": "bottom", "y": 1.02, "xanchor": "left", "orientation": "h"},
            legend_title_text="",
            xaxis={"showgrid": True},
            uirevision=True,
        )
 
    if spectrum_type == "time":
        fig = px.line(state.dataframe, x="time", y="voltage", color="name")
        prepare_axes(fig, "time (us)", "accumulated voltage (V)")
    else:  # mass
        fig = px.line(state.dataframe, x="mass", y="voltage", color="name")
        prepare_axes(fig, "mass (amu)", "accumulated voltage (V)")
 
    if pointer:
        fig.add_vline(pointer_value, line_dash="dash", line_color="red")
 
    return fig


def plot_on_off_difference(wavelengths, ioff, ion, targets):
    diff = ion - ioff  # shape (n_targets, n_wavelengths)

    fig = go.Figure()
    for i, mass in enumerate(targets):
        fig.add_trace(go.Scatter(
            x=wavelengths,
            y=diff[i, :],
            mode="lines+markers",
            name=f"m/z {mass}",
            xaxis="x",
        ))

    fig.add_hline(y=0, line_dash="dot", line_color="gray")

    # --- secondary axis: wavenumber (cm^-1) ---
    wl_min, wl_max = min(wavelengths), max(wavelengths)
    wn_at_min = 1e7 / wl_min  # smaller wavenumber
    wn_at_max = 1e7 / wl_max  # larger wavenumber

    fig.update_layout(
        xaxis={
            "title": "Wavelength (nm)",
            "domain": [0, 1],
        },
        xaxis2={
            "title": "Wavenumber (cm⁻¹)",
            "overlaying": "x",
            "side": "top",
            "range": [wn_at_min, wn_at_max],  # reversed to align with wavelength axis
        },
        yaxis_title="ΔSignal (IR on − IR off)",
        legend_title="Mass",
        hovermode="closest",
        height=500,
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
    )

    # dummy invisible trace to force xaxis2 to render
    fig.add_trace(go.Scatter(
        x=[wl_min, wl_max], y=[None, None],
        xaxis="x2", showlegend=False, hoverinfo="skip",
    ))

    return fig