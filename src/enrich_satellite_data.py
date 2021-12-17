import pandas as pd

from satellites import Satellites


def enrich_with_celestrak():
    sats = Satellites()
    sats_df = sats.get_dataframe()
    celes_df = pd.read_csv("https://celestrak.com/pub/satcat.csv")
    celes_df.set_index(['NORAD_CAT_ID'], inplace=True)
    for i in sats_df.index:
        if i in celes_df.index:
            sats_df.loc[i]['launched'] = celes_df.loc[i]['LAUNCH_DATE']
            sats_df.loc[i]['decayed'] = celes_df.loc[i]['DECAY_DATE']
            sats_df.loc[i]['countries'] = celes_df.loc[i]['OWNER']
    return sats_df


if __name__ == "__main__":
    sats_before_df = Satellites().get_dataframe()
    print("Number of dates before:")
    print(len(sats_before_df['launched'].value_counts()))
    sats_df = enrich_with_celestrak()
    sats_df.to_csv("../data/satellites_enriched.csv")
    print("Number of dates after:")
    print(len(sats_df['launched'].value_counts()))
