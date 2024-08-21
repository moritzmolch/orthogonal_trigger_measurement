import mplhep
import matplotlib.pyplot as plt


# colorblind-friendly plot colors
PETROFF_COLORS = {
    "blue": "#3f90da",
    "light_orange": "#ffa90e",
    "red": "#bd1f01",
    "light_gray": "#94a4a2",
    "purple": "#832db6",
    "brown": "#a96b59",
    "orange": "#e76300",
    "tan": "#b9ac70",
    "gray": "#717581",
    "light_blue": "#92dadd",
    "black": "#000000",
    "white": "#ffffff",
}


def plot_2d_colormesh(
    x_bin_edges,
    y_bin_edges,
    z_values,
    x_label,
    y_label,
    z_label,
    pcolormesh_kwargs=None,
    colorbar_kwargs=None,
    mplhep_label_kwargs=None,
):
    # preprocess keyword arguments of pcolormesh
    pcolormesh_kwargs = pcolormesh_kwargs or {}
    pcolormesh_kwargs["cmap"] = pcolormesh_kwargs.get("cmap", "viridis")
    pcolormesh_kwargs["vmin"] = pcolormesh_kwargs.get("vmin", None)
    pcolormesh_kwargs["vmax"] = pcolormesh_kwargs.get("vmax", None)

    # preprocess keyword arguments for colobar
    colorbar_kwargs = colorbar_kwargs or {}

    # preprocess keyword arguments of mplhep.cms.label
    mplhep_label_kwargs = mplhep_label_kwargs or {}
    mplhep_label_kwargs["label"] = mplhep_label_kwargs.get("label", "Work in progress")
    mplhep_label_kwargs["data"] = mplhep_label_kwargs.get("data", True)

    # create the figure
    fig, ax = plt.subplots()

    # CMS labeling
    mplhep.cms.label(ax=ax, **mplhep_label_kwargs)

    # plot the values
    artists = ax.pcolormesh(x_bin_edges, y_bin_edges, z_values.T, **pcolormesh_kwargs)

    # add a colorbar and x and y labels
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    fig.colorbar(artists, label=z_label, **colorbar_kwargs)

    # print the numbers in the plot
    x_bin_centers = (x_bin_edges[1:] + x_bin_edges[:-1]) / 2
    y_bin_centers = (y_bin_edges[1:] + y_bin_edges[:-1]) / 2
    for i in range(z_values.shape[0]):
        for j in range(z_values.shape[1]):
            ax.text(
                x_bin_centers[i],
                y_bin_centers[j],
                f"{z_values.T[j, i]:.2f}",
                fontsize="small",
                ha="center",
                va="center",
                color="white",
                transform=ax.transData,
            )

    return fig, ax
