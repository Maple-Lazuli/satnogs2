import pandas as pd
import plotnine as p9


def find_satellite_dataset_numbers(df=None):
    """
    Use the enriched satellite dataset to print statistics and save a ggplot over the relative frequency of the
    owners of the satellites.
    :param df: Optional satellites DF to use in place of the enriched satellites df
    :return: None
    """
    df = pd.read_csv("data/satellites_enriched.csv") if df is None else df
    print(f'The non-unique NORADS are:')
    print(df[df['norad_cat_id'] == 0])
    print(f"There are {len(df['countries'].unique())} unique owners of satellites in this dataset")
    print(f"The unique owners of satellites are:\n {df['countries'].unique()}")
    rel_freq = df['countries'].value_counts() / sum(df['countries'].value_counts())
    print(f"The top ten most common owners of satellites in this dataset are: {rel_freq[:10]}")
    plot = plot_from_country_counts(rel_freq, "Top 10 Satellite Owners in Satnogs Dataset")
    plot.draw(show=True)
    p9_plot_save(plot, "satnogs_owner_numbers")


def plot_from_country_counts(rel_freq, title):
    """
    Helper function to reduce redundant code and maintain similar and consistent graphs
    :param rel_freq: The relative frequency pandas series to use in the plot
    :param title: The title the image should have
    :return: Returns a plot object.
    """
    plot_df = rel_freq[:10].to_frame()
    plot_df["Names"] = plot_df.index
    plot_df["Order"] = [str(l) for l in range(0, 10)]
    plot = p9.ggplot(plot_df[:10], p9.aes(x="Order", y="countries", color="Names", fill="Names"))
    plot += p9.xlab("Satellite Owner") + p9.ylab("Frequency %")
    plot += p9.ggtitle(title)
    plot += p9.scale_x_discrete(labels=plot_df[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    return plot


def celes_comparison(df=None):
    """
    Prints statistics and creates a plot of the owner data in the CELESTRAK dataset.
    :param df: An optional DF to use in place of the CELESTRAK dataset
    :return: None
    """
    celes_df = pd.read_csv("https://celestrak.com/pub/satcat.csv")
    celes_df = celes_df[celes_df['OBJECT_TYPE'] == 'PAY']
    celes_num_unique = len(celes_df["OWNER"].unique())
    print(f'Number of unique satellite owners in celestrak dataset: {celes_num_unique}')
    rel_freq_celes = celes_df['OWNER'].value_counts() / sum(celes_df['OWNER'].value_counts())
    print(f"The top ten most common owners of satellites in this dataset are: \n {rel_freq_celes[:10]}")
    print(f'Satellite owners not found in the satnogs network:')
    df = pd.read_csv("data/satellites_enriched.csv") if df is None else df
    satellites_not_covered = set(celes_df['OWNER'].unique()) - set(df['countries'].unique())
    print(str(satellites_not_covered))

    plot_df = rel_freq_celes[:10].to_frame()
    plot_df["Names"] = plot_df.index
    plot_df["Order"] = [str(l) for l in range(0, 10)]
    plot = p9.ggplot(plot_df[:10], p9.aes(x="Order", y="OWNER", color="Names", fill="Names"))
    plot += p9.xlab("Satellite Owner") + p9.ylab("Frequency %")
    plot += p9.ggtitle("Top 10 Satellite Owners in Celestrak Dataset")
    plot += p9.scale_x_discrete(labels=plot_df[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    plot.draw(show=True)
    p9_plot_save(plot, "celes_owner_numbers")


def frequency_band_review():
    """
    Prints statistics over the observation frequencies and creates plots for them.
    :return: None
    """
    observations_df = pd.read_csv("data/complete.csv")
    print(f"The status counts for the observations are:\n{observations_df['Status'].value_counts()}")
    observations_df["Band"] = observations_df['Frequency'].apply(lambda x: label_freq(x))
    status_df = observations_df['Status'].value_counts().to_frame()
    status_df["Names"] = status_df.index
    status_df['Order'] = [str(l) for l in range(0, status_df.shape[0])]
    plot = p9.ggplot(status_df, p9.aes(x="Order", y="Status", color="Names", fill="Names"))
    plot += p9.scale_x_discrete(labels=status_df[:10]['Names'])
    plot += p9.xlab("Observation Status") + p9.ylab("Number of Observations")
    plot += p9.ggtitle("SATNOGS Observation Breakout")
    plot += p9.scale_x_discrete(labels=status_df[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    p9_plot_save(plot, "status_breakdown")
    plot.draw(show=True)

    vhf, uhf, two_ghz = get_vhf_uhf_2ghz(observations_df)
    print(f'The frequency band breakout for all observations is:'
          f'\nvhf:{vhf.shape[0]} \nuhf:{uhf.shape[0]} \n2GHz:{two_ghz.shape[0]}')

    status_df = observations_df['Band'].value_counts().to_frame()
    status_df["Names"] = status_df.index
    status_df['Order'] = [str(l) for l in range(0, status_df.shape[0])]
    plot = p9.ggplot(status_df, p9.aes(x="Order", y="Band", color="Names", fill="Names"))
    plot += p9.scale_x_discrete(labels=status_df[:10]['Names'])
    plot += p9.xlab("Frequency Band") + p9.ylab("Number of Observations")
    plot += p9.ggtitle("Frequency Bands")
    plot += p9.scale_x_discrete(labels=status_df[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    p9_plot_save(plot, "frequency_bands")
    plot.draw(show=True)

    vhf, uhf, two_ghz = get_vhf_uhf_2ghz(observations_df[observations_df['Status'] == 'Good'])
    print(f'The frequency band breakout for good observations is:'
          f'\nvhf:{vhf.shape[0]} \nuhf:{uhf.shape[0]} \n2GHz:{two_ghz.shape[0]}')

    print("Top 10 successful VHF Countries:")
    print(get_top_10_countries(vhf))

    print("Top 10 successful UHF Countries:")
    print(get_top_10_countries(uhf))

    print("Top 10 successful 2GHz Countries:")
    print(get_top_10_countries(two_ghz))

    rel_2ghz = get_top_10_countries(two_ghz)
    rel_2ghz = rel_2ghz.to_frame()
    rel_2ghz["Names"] = rel_2ghz.index
    rel_2ghz['Order'] = [str(l) for l in range(0, rel_2ghz.shape[0])]
    plot = p9.ggplot(rel_2ghz, p9.aes(x="Order", y="countries", color="Names", fill="Names"))
    plot += p9.scale_x_discrete(labels=rel_2ghz[:10]['Names'])
    plot += p9.xlab("Country") + p9.ylab("Number of Observations")
    plot += p9.ggtitle("2 GHz Owners")
    plot += p9.scale_x_discrete(labels=rel_2ghz[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    p9_plot_save(plot, "2ghz_success_breakdown")
    plot.draw(show=True)

    print("Top 10 2GHz PRC Satellites")
    print(two_ghz['Satellite'].value_counts()[:10])
    two_ghz['Satellite'] = two_ghz['Satellite'].apply(lambda x: x.split('-')[1].strip())
    two_ghz = two_ghz[two_ghz['countries'] == 'PRC']
    rel_2ghz_sats = two_ghz['Satellite'].value_counts() / sum(two_ghz['Satellite'].value_counts())
    rel_2ghz_sats = rel_2ghz_sats.to_frame()
    rel_2ghz_sats["Names"] = rel_2ghz_sats.index
    rel_2ghz_sats['Order'] = [str(l) for l in range(0, rel_2ghz_sats.shape[0])]
    plot = p9.ggplot(rel_2ghz_sats[:10], p9.aes(x="Order", y="Satellite", color="Names", fill="Names"))
    plot += p9.scale_x_discrete(labels=rel_2ghz_sats[:10]['Names'])
    plot += p9.xlab("Satellite") + p9.ylab("Number of Observations")
    plot += p9.ggtitle("PRC 2 GHz Satellites")
    plot += p9.scale_x_discrete(labels=rel_2ghz_sats[:10]['Names'])
    plot += p9.geom_col(position="dodge")
    plot += p9_consistent_look()
    plot.save("images/2ghz_prc_sat.png", format="png", width=10, height=8)
    plot.draw(show=True)
    print(
        f"The number of ground stations that collect on the 2GHZ PRC satellites is {len(two_ghz['Station'].unique())}")
    vhf, uhf, two_ghz = get_vhf_uhf_2ghz(observations_df[observations_df['Status'] == 'Bad'])
    print(f'The frequency band breakout for bad observations is:'
          f'\nvhf:{vhf.shape[0]} \nuhf:{uhf.shape[0]} \n2GHz:{two_ghz.shape[0]}')

    print("Top 10 unsuccessful VHF Countries:")
    print(get_top_10_countries(vhf))

    print("Top 10 unsuccessful UHF Countries:")
    print(get_top_10_countries(uhf))

    print("Top 10 unsuccessful 2GHz Countries:")
    print(get_top_10_countries(two_ghz))


def get_vhf_uhf_2ghz(df):
    """
    Returns slices of the input dataframe based on the frequency category
    :param df: The pandas dataframe to slice
    :return: A tuple of dataframe slices
    """
    vhf_df = df[df['Frequency'] <= 300 * 10 ** 6]
    uhf_df = df[(df['Frequency'] > 300 * 10 ** 6) & (df['Frequency'] < 2 * 10 ** 9)]
    two_ghz_df = df[df['Frequency'] >= 2 * 10 ** 9]
    return vhf_df, uhf_df, two_ghz_df


def label_freq(freq):
    """
    Helper function to label to classify the frequency band a particular observation occurred in.
    :param freq: The frequency to classify.
    :return: String representing the band classification.
    """
    if freq <= 300 * 10 ** 6:
        return "VHF"
    elif freq < 2 * 10 ** 9:
        return "UHF"
    elif freq < 3 * 10 ** 9:
        return "2ghz"
    else:
        return "3ghz+"


def get_top_10_countries(df):
    """
    Helper function to get the relative frequency of the top ten countries in a dataframe.
    :param df: The dataframe to get the relative frequency counts for.
    :return: A pandas series of the first 10 elements in a relative frequency table
    """
    rel_freq = df['countries'].value_counts() / sum(df['countries'].value_counts())
    return rel_freq[:10]


def get_complete_df(path_name='data/complete.csv'):
    """
    Helper function to load the compleded dataframe from the data pull phase.
    :param path_name: The path and file name of the completed CSV
    :return: Returns a pandas dataframe loaded from the completed CSV
    """
    return pd.read_csv(path_name, low_memory=False)


def p9_consistent_look():
    """
    Helper function to give plots a consistent and clean look.
    :return: Plotnine functions
    """
    return p9.theme_classic() + p9.theme(text=p9.element_text(family="serif"))


def p9_plot_save(plot, name, path="images/", format="png", dpi=100):
    """
    Helper function to save images in the same location with similar properties.
    :param plot: The plot object to use
    :param name: The name to save the plot as
    :param path: The location to save the plot image in
    :param format: The image encoding to use
    :param dpi: The dots per inch to use for the image
    :return: None
    """
    plot.save(path + name + "." + format, format=format, dpi=dpi)


def prc():
    """
    Get statistics around the PRC satellites seen in the various frequency bands.
    :return: None
    """
    obs_df = pd.read_csv("data/complete.csv")
    obs_df = obs_df[obs_df['countries'] == 'PRC']
    obs_df = obs_df[obs_df['Status'] == 'Good']

    vhf, uhf, two_ghz = get_vhf_uhf_2ghz(obs_df)
    print(f'most common successful PRC 2 GHz targets: \n')
    rel_freq = two_ghz['Satellite'].value_counts() / sum(two_ghz['Satellite'].value_counts())
    print(rel_freq[:10])

    print(f'most common successful PRC UHF targets: \n')
    rel_freq = uhf['Satellite'].value_counts() / sum(uhf['Satellite'].value_counts())
    print(rel_freq[:10])

    print(f'most common successful PRC VHF targets: \n')
    rel_freq = vhf['Satellite'].value_counts() / sum(vhf['Satellite'].value_counts())
    print(rel_freq[:10])


if __name__ == '__main__':
    find_satellite_dataset_numbers()
    celes_comparison()
    frequency_band_review()
    prc()
