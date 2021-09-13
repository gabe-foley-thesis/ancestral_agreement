import numpy as np
import matplotlib.pyplot as plt


def bland_altman_plot(
    m1,
    m2,
    sd_limit=1.96,
    ax=None,
    fig=None,
    ages=None,
    point_labels=None,
    display_labels=None,
    highlight_points=None,
    hide_points=None,
    y_lim=100,
    title="",
    x_axis="",
    scatter_kwds=None,
    mean_line_kwds=None,
    limit_lines_kwds=None,
):
    """
     Bland-Altman Plot.

     A Bland-Altman plot is a graphical method to analyze the differences
     between two methods of measurement. The mean of the measures is plotted
     against their difference.

     Parameters
     ----------
     m1, m2: pandas Series or array-like

     sd_limit : float, default 1.96
         The limit of agreements expressed in terms of the standard deviation of
         the differences. If `md` is the mean of the differences, and `sd` is
         the standard deviation of those differences, then the limits of
         agreement that will be plotted will be
                        md - sd_limit * sd, md + sd_limit * sd
         The default of 1.96 will produce 95% confidence intervals for the means
         of the differences.
         If sd_limit = 0, no limits will be plotted, and the ylimit of the plot
         defaults to 3 standard deviatons on either side of the mean.

     ax: matplotlib.axis, optional
         matplotlib axis object to plot on.

     scatter_kwargs: keywords
         Options to to style the scatter plot. Accepts any keywords for the
         matplotlib Axes.scatter plotting method

     mean_line_kwds: keywords
         Options to to style the scatter plot. Accepts any keywords for the
         matplotlib Axes.axhline plotting method

     limit_lines_kwds: keywords
         Options to to style the scatter plot. Accepts any keywords for the
         matplotlib Axes.axhline plotting method

    Returns
     -------
     ax: matplotlib Axis object
     :param display_labels:
    """

    if display_labels and not point_labels:
        print("Warning: Display labels was requested but no labels have been provided")

    # if highlight_points and not point_labels:
    #         print ("Warning: Highlight points was requested but no labels have been provided")

    #     if hide_points and not point_labels:
    #         print ("Warning: Hide points was requested but no labels have been provided")

    if len(m1) != len(m2):
        raise ValueError("m1 does not have the same length as m2.")
    if sd_limit < 0:
        raise ValueError("sd_limit ({}) is less than 0.".format(sd_limit))

    if ages:
        agesLabel = True
    else:
        agesLabel = False

    if point_labels:
        pointLabel = True
    else:
        pointLabel = False

    means = np.mean([m1, m2], axis=0)
    diffs = m1 - m2
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, axis=0)

    if hide_points:
        del_idx = []
        idx = 0
        for label in point_labels:
            if label in hide_points:
                del_idx.append(idx)
            idx += 1

        m1 = np.delete(m1, del_idx)
        m2 = np.delete(m2, del_idx)
        ages = np.delete(ages, del_idx)
        point_labels = np.delete(point_labels, del_idx)

    # if ax is None:
    #         ax = plt.gca()

    scatter_kwds = scatter_kwds or {}
    if "s" not in scatter_kwds:
        scatter_kwds["s"] = 20
    mean_line_kwds = mean_line_kwds or {}
    limit_lines_kwds = limit_lines_kwds or {}
    for kwds in [mean_line_kwds, limit_lines_kwds]:
        if "color" not in kwds:
            kwds["color"] = "gray"
        if "linewidth" not in kwds:
            kwds["linewidth"] = 1
    if "linestyle" not in mean_line_kwds:
        kwds["linestyle"] = "--"
    if "linestyle" not in limit_lines_kwds:
        kwds["linestyle"] = ":"

    if agesLabel:
        x = ages
        y = diffs
    else:
        x = means
        y = diffs

    fig, ax = plt.subplots(figsize=(8, 5))

    sc = ax

    if highlight_points and pointLabel:
        cmap = []
        for point in point_labels:
            if not hide_points or point not in hide_points:
                colour = "Red" if point in highlight_points else "Blue"
                cmap.append(colour)

    else:
        cmap = ["Blue"] * len(m1)

    # z = np.polyfit(x, y, 2)
    #     p = np.poly1d(z)

    #     ax.plot(x,p(x))

    sc = ax.scatter(x, y, c=cmap, **scatter_kwds)

    ax.axhline(mean_diff, **mean_line_kwds)  # draw mean line.

    # Annotate mean line with mean difference.
    ax.annotate(
        "mean diff:\n{}".format(np.round(mean_diff, 2)),
        xy=(0.99, 0.5),
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=14,
        xycoords="axes fraction",
    )

    if display_labels and pointLabel:
        for label, x_val, y_val in zip(point_labels, x, y):
            if label in display_labels:
                plt.annotate(
                    label,
                    xy=(x_val, y_val),
                    xytext=(-20, 20),
                    textcoords="offset points",
                    ha="right",
                    va="bottom",
                    bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                )

    if pointLabel:
        for label, x_val, y_val in zip(point_labels, x, y):
            annot = plt.annotate(
                label,
                xy=(x_val, y_val),
                xytext=(-20, 20),
                textcoords="offset points",
                ha="right",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )

            annot.set_visible(False)

    if sd_limit > 0:
        half_ylim = (1.5 * sd_limit) * std_diff
        ax.set_ylim(mean_diff - half_ylim, mean_diff + half_ylim)

        limit_of_agreement = sd_limit * std_diff
        lower = mean_diff - limit_of_agreement
        upper = mean_diff + limit_of_agreement
        for j, lim in enumerate([lower, upper]):
            ax.axhline(lim, **limit_lines_kwds)
        ax.annotate(
            "-SD{}: {}".format(sd_limit, np.round(lower, 2)),
            xy=(0.99, 0.07),
            horizontalalignment="right",
            verticalalignment="bottom",
            fontsize=14,
            xycoords="axes fraction",
        )
        ax.annotate(
            "+SD{}: {}".format(sd_limit, np.round(upper, 2)),
            xy=(0.99, 0.92),
            horizontalalignment="right",
            fontsize=14,
            xycoords="axes fraction",
        )

    elif sd_limit == 0:
        half_ylim = 3 * std_diff
        ax.set_ylim(mean_diff - half_ylim, mean_diff + half_ylim)

    ax.set_title(title)
    ax.set_ylim(-1 * y_lim, y_lim)

    ax.set_ylabel("Difference", fontsize=24)
    if agesLabel:
        ax.set_xlabel(x_axis, fontsize=24)
    else:
        ax.set_xlabel("Means", fontsize=24)
    ax.tick_params(labelsize=13)
    plt.tight_layout()

    def update_annot(ind):
        pos = sc.get_offsets()[ind["ind"][0]]
        annot.xy = pos
        #         text = "N{}".format(" N".join(list(map(str,ind["ind"]))))
        text = "{}".format(" ").join(list(map(get_label, (ind["ind"]))))

        annot.set_text(text)

    #     annot.get_bbox_patch().set_facecolor(cmap(norm(c[ind["ind"][0]])))
    #     annot.get_bbox_patch().set_alpha(0.4)

    def get_label(pos):
        if len(point_labels[int(pos)]) > 0:
            return point_labels[int(pos)]

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = sc.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)

    return ax
