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
        ))

    fig.add_hline(y=0, line_dash="dot", line_color="gray")

    fig.update_layout(
        xaxis_title="Wavenumber (cm⁻¹)",
        yaxis_title="ΔSignal (IR on − IR off)",
        legend_title="Mass",
        hovermode="x unified",
        height=500,
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    return fig