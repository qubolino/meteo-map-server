from matplotlib.patheffects import Normal, Stroke
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from typing import Optional, Tuple, Any
import cartopy.crs as ccrs

DEFAULT_DPI = 150
DEFAULT_FIGSIZE = (8, 6)
DEFAULT_MAP_EXTENT = (-10, 15, 38, 55)  # (xmin, xmax, ymin, ymax)


def create_rain_cmap() -> LinearSegmentedColormap:
    rain_colors = [
        (0.0, 0.7, 0.9, 0.6),
        (0, 0, 0.8, 0.6),
        (0, 0.8, 0, 0.6),
        (0, 0.8, 0.8, 0.6),
    ]
    return LinearSegmentedColormap.from_list("rain", rain_colors, N=256)


def extract_coordinates_and_data(
    layer: Any,
    subsample: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lons = layer.longitude.values
    lats = layer.latitude.values
    data = layer.values
    if subsample is not None:
        lons = lons[::subsample]
        lats = lats[::subsample]
        data = data[::subsample, ::subsample]
    return lons, lats, data


def create_figure(dpi: int = DEFAULT_DPI) -> plt.Figure:
    return plt.figure(figsize=DEFAULT_FIGSIZE, dpi=dpi)


def apply_map_extent(ax: plt.Axes, extent: Optional[Tuple] = None) -> None:
    if extent is None:
        extent = DEFAULT_MAP_EXTENT
    ax.set_extent(extent, crs=ccrs.PlateCarree())


def style_axes_clean(ax: plt.Axes) -> None:
    ax.set_title("")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def save_figure(fig: plt.Figure, output_path: Path, dpi: int = DEFAULT_DPI, transparent: bool = True) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0, transparent=transparent)


def finalize_plot(show: bool = False) -> None:
    if show:
        plt.show()
    plt.close()


def plot_layer_to_png(
    layer: Any,
    output_path: Path = Path("./layer_plot.png"),
    dpi: int = DEFAULT_DPI,
    show: bool = False,
    cmap: Optional[LinearSegmentedColormap] = None,
    vmin: Optional[float] = 0,
    vmax: Optional[float] = None,
    levels: Optional[int] = 100,
    transparent: bool = True
) -> None:
    lons, lats, data = extract_coordinates_and_data(layer)
    if vmax is None:
        vmax = np.nanmax(data)
    fig = create_figure(dpi)
    ax = plt.axes(projection=ccrs.Mercator())
    apply_map_extent(ax)
    ax.contourf(
        lons, lats, data,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        levels=np.linspace(vmin or 0, vmax, levels),
        extend='neither',
        transform=ccrs.PlateCarree()
    )
    ax.text(
        0.98, 0.05,
        f"data from AROME model produced by Météo-France\nprediction for hour ending {layer['time'].values}",
        transform=ax.transAxes, fontsize=10, color="black", ha="right", va="bottom",
        path_effects=[Stroke(linewidth=3, foreground="white"), Normal()]
    )
    style_axes_clean(ax)
    save_figure(fig, output_path, dpi, transparent)
    finalize_plot(show)


def plot_rain_layer_to_png(
    layer: Any,
    output_dir: Path = Path("./generated_maps/"),
    dpi: int = DEFAULT_DPI,
    show: bool = False,
    vmax=None,
    vmin=0.1,
    levels=20,
) -> None:
    plot_layer_to_png(
        layer=layer,
        output_path=output_dir / f"rain_map_{np.datetime_as_string(layer['time'].values, unit='s', timezone='UTC')}.png",
        dpi=dpi,
        show=show,
        cmap=create_rain_cmap(),
        vmin=vmin,
        vmax=vmax,
        levels=levels,
        transparent=True
    )


def plot_wind_barbs_to_png(
    u_layer,
    v_layer,
    output_dir: Path = Path("./generated_maps/"),
    dpi: int = 450,
    subsample: int = 5,
    show: bool = False,
    barb_color: str = "black",
    barb_length: float = 3.5,
):
    lons = u_layer.longitude.values
    lats = u_layer.latitude.values
    u_data = u_layer.values * 1.94384  # m/s to kt
    v_data = v_layer.values * 1.94384

    lons_sub = lons[::subsample]
    lats_sub = lats[::subsample]
    u_sub = u_data[::subsample, ::subsample]
    v_sub = v_data[::subsample, ::subsample]

    fig = create_figure(dpi)
    ax = plt.axes(projection=ccrs.Mercator())
    apply_map_extent(ax)

    ax.barbs(
        lons_sub, lats_sub, u_sub, v_sub,
        color=barb_color,
        length=barb_length,
        linewidth=0.25,
        transform=ccrs.PlateCarree(),
    )

    ax.text(
        0.98, 0.05,
        f"data from AROME model produced by Météo-France\nprediction for time {u_layer['time'].values}\nat alt {u_layer['isobaricInhPa'].values}hPa",
        transform=ax.transAxes, fontsize=10, color="black", ha="right", va="bottom",
        path_effects=[Stroke(linewidth=3, foreground="white"), Normal()]
    )

    style_axes_clean(ax)
    save_figure(
        fig,
        output_dir / f"wind_map_{u_layer['isobaricInhPa'].values}hPa_{np.datetime_as_string(u_layer['time'].values, unit='s', timezone='UTC')}.png",
        dpi=dpi,
        transparent=True
    )
    finalize_plot(show)
    plt.close()
