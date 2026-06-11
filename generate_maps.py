"""
Map generation utilities for weather data visualization.

Provides functions to generate PNG maps from xarray DataArrays with consistent
styling and layout across different weather variables (wind, temperature, rain).
"""

from matplotlib.patheffects import Normal, Stroke
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from typing import Optional, Tuple, Any
import cartopy.crs as ccrs
import cartopy.feature as cfeature


# =============================================================================
# Constants
# =============================================================================

DEFAULT_DPI = 150
DEFAULT_FIGSIZE = (8, 6)
DEFAULT_MAP_EXTENT = (-10, 15, 38, 55)  # (xmin, xmax, ymin, ymax)


# =============================================================================
# Colormap Presets
# =============================================================================

def create_white_to_darkgray_cmap() -> LinearSegmentedColormap:
    """Create a colormap from transparent white to dark gray."""
    colors = [
        # (1, 1, 1, 0),    # Transparent white
        # (0.5, 0.5, 0.5, 1),  # Medium gray
        # (0, 0, 0, 1)     # Black
        (1, 1, 1, 0),    # Transparent white
        (0.7, 0.7, 0.7, 0.5),    # Transparent white
        (0.7, 0.7, 0.7, 1),    # Transparent white
    ]
    return LinearSegmentedColormap.from_list("white_to_darkgray", colors, N=256)


def create_rain_cmap() -> LinearSegmentedColormap:
    """Create a colormap for rain visualization with distinct colors."""
    rain_colors = [
        # (1, 1, 1, 0),        # Transparent white (0 mm)
        (0.0, 0.7, 0.9, 0.6),  # Violet (light rain)
        (0, 0, 0.8, 0.6),    # Dark blue (moderate rain)
        (0, 0.8, 0, 0.6),    # Green (heavy rain)
        (0, 0.8, 0.8, 0.6)   # yello (very heavy rain)
    ]
    return LinearSegmentedColormap.from_list("rain", rain_colors, N=256)
    


# =============================================================================
# Helper Functions
# =============================================================================

def extract_coordinates_and_data(
    layer: Any,
    subsample: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract longitude, latitude, and data arrays from an xarray DataArray.
    
    Args:
        layer: xarray.DataArray with latitude and longitude dimensions.
        subsample: Optional subsampling factor. If provided, data is subsampled.
        
    Returns:
        Tuple of (lons, lats, data) as numpy arrays.
    """
    lons = layer.longitude.values
    lats = layer.latitude.values
    data = layer.values
    
    if subsample is not None:
        lons = lons[::subsample]
        lats = lats[::subsample]
        data = data[::subsample, ::subsample]
    
    return lons, lats, data


def create_figure(dpi: int = DEFAULT_DPI) -> Tuple[plt.Figure, plt.Axes]:
    """Create a new figure with default settings."""
    return plt.figure(figsize=DEFAULT_FIGSIZE, dpi=dpi)


def apply_map_extent(ax: plt.Axes, extent: Optional[Tuple] = None) -> None:
    """Set the map extent on the axes."""
    if extent is None:
        extent = DEFAULT_MAP_EXTENT
    ax.set_extent(extent, crs=ccrs.PlateCarree())

def style_axes_clean(ax: plt.Axes) -> None:
    """Apply clean styling to axes: remove title, ticks, and spines."""
    ax.set_title("")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def save_figure(
    fig: plt.Figure,
    output_path: Path,
    dpi: int = DEFAULT_DPI,
    transparent: bool = True
) -> None:
    """Save the figure to the specified path with consistent settings."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        output_path,
        dpi=dpi,
        bbox_inches='tight',
        pad_inches=0,
        transparent=transparent
    )


def finalize_plot(show: bool = False) -> None:
    """Finalize the plot: show if requested and close the figure."""
    if show:
        plt.show()
    plt.close()


# =============================================================================
# Main Plot Functions
# =============================================================================

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
    """
    Plot a 2D layer (latitude x longitude) as a PNG with custom styling.
    
    Args:
        layer: xarray.DataArray with latitude and longitude dimensions.
        output_path: Path to save the PNG. Default: "./layer_plot.png".
        dpi: DPI for the output image. Default: 300.
        show: If True, display the plot interactively. Default: False.
        cmap: Colormap to use. Default: white_to_darkgray.
        vmin: Minimum value for the colormap. Default: 0.
        vmax: Maximum value for the colormap. If None, uses data max.
        levels: Number of contour levels. Default: 100.
        transparent: Whether to use transparent background. Default: True.
    """
    # Extract data
    lons, lats, data = extract_coordinates_and_data(layer)
    
    # Use provided colormap or default
    if cmap is None:
        cmap = create_white_to_darkgray_cmap()
    
    # Determine vmax if not provided
    if vmax is None:
        vmax = np.nanmax(data)
    
    # Create plot
    fig = create_figure(dpi)
    # ax = plt.axes(projection=ccrs.PlateCarree())
    ax = plt.axes(projection=ccrs.Mercator())

    apply_map_extent(ax)

    # Plot data
    ax.contourf(
        lons, lats, data,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        levels=np.linspace(vmin or 0, vmax, levels),
        extend='neither',
        transform=ccrs.PlateCarree()
    )
    
    # ax.coastlines()
    # ax.add_feature(cfeature.BORDERS, linestyle=':')  # Country borders

    ax.text(
        0.98, 0.05,
        f"data from AROME model produced by Météo-France\nprediction for hour ending {layer['time'].values}",
        transform=ax.transAxes,
        fontsize=10,
        color="black",
        ha="right",
        va="bottom",
        path_effects=[Stroke(linewidth=3, foreground="white"), Normal()]
    )


    # Define georeferencing points (lon, lat)
    georef_points = [
        (-10, 55),  # Top-left
        (15, 55),   # Top-right
        (15, 38),   # Bottom-right
        (-10, 38),  # Bottom-left
    ]

    # Add points to the axes
    ax.scatter(
        [p[0] for p in georef_points],  # Longitudes
        [p[1] for p in georef_points],  # Latitudes
        color='red',                    # Point color
        s=10,                          # Point size
        marker='o',                    # Marker style (circle)
        edgecolor='black',             # Edge color
        linewidth=0.5,                # Edge width
        transform=ccrs.PlateCarree(), # Use geographic coordinates
        zorder=10,                     # Ensure points are on top
        label='Georeference Points'    # Optional: for legend
    )




    # Apply consistent styling
    style_axes_clean(ax)
    # plt.tight_layout(pad=0)
    
    # Save and finalize
    save_figure(fig, output_path, dpi, transparent)
    finalize_plot(show)


def plot_rain_layer_to_png(
    layer: Any,
    output_dir: Path = Path("./generated_maps/"),
    dpi: int = DEFAULT_DPI,
    show: bool = False,
    vmax=None,
    vmin=0.1, # min 0.1kg.m-2 == h2o mm
    levels=20,
) -> None:
    """
    Plot a rain layer as a PNG with rain-specific colormap.
    
    Args:
        layer: xarray.DataArray with latitude and longitude dimensions.
        output_path: Path to save the PNG. Default: "./rain_plot.png".
        dpi: DPI for the output image. Default: 300.
        show: If True, display the plot interactively. Default: False.
    """
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
    """
    Plot wind barbs from u and v wind components as a PNG.

    Args:
        u_layer: xarray.DataArray for the u-component of wind (eastward).
        v_layer: xarray.DataArray for the v-component of wind (northward).
        output_path: Path to save the PNG. Default: "./wind_barbs.png".
        dpi: DPI for the output image. Default: 300.
        subsample: Subsampling factor for barbs (e.g., 5 = every 5th point). Default: 5.
        show: If True, display the plot interactively. Default: False.
        barb_color: Color for the barbs. Default: "black".
        barb_length: Length of the barb in points. Default: 7.0.
    """
    # Extract coordinates and data
    lons = u_layer.longitude.values
    lats = u_layer.latitude.values
    u_data = u_layer.values * 1.94384 # m.s-1 to kt
    v_data = v_layer.values * 1.94384 # m.s-1 to kt

    # Subsample the data for performance
    lons_sub = lons[::subsample]
    lats_sub = lats[::subsample]
    u_sub = u_data[::subsample, ::subsample]
    v_sub = v_data[::subsample, ::subsample]

    # Create the plot
    fig = create_figure(dpi)
    # ax = plt.axes(projection=ccrs.PlateCarree())
    ax = plt.axes(projection=ccrs.Mercator())


    # Set the map extent: 10W to 15E, 38N to 55N
    apply_map_extent(ax)

    # Plot wind barbs
    ax.barbs(
        lons_sub, lats_sub,
        u_sub, v_sub,
        color=barb_color,
        length=barb_length,
        linewidth=0.25,
        transform=ccrs.PlateCarree(),
    )

    # ax.coastlines()
    # ax.add_feature(cfeature.BORDERS, linestyle=':')  # Country borders

    ax.text(
        0.98, 0.05,
        f"data from AROME model produced by Météo-France\nprediction for time {u_layer['time'].values}\nat alt {u_layer['isobaricInhPa'].values}hPa",
        transform=ax.transAxes,
        fontsize=10,
        color="black",
        ha="right",
        va="bottom",
        path_effects=[Stroke(linewidth=3, foreground="white"), Normal()]
    )

    style_axes_clean(ax)

    # Save the plot
    save_figure(fig, 
        output_dir / f"wind_map_{u_layer['isobaricInhPa'].values}hPa_{np.datetime_as_string(u_layer['time'].values, unit='s', timezone='UTC')}.png",
        dpi=dpi,
        transparent=True
    )
    finalize_plot(show)
    plt.close()