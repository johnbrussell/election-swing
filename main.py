import os
import sys

from csv_reader.csv_reader import CsvReader, dataWithColumns
from csv_writer.csv_writer import CsvWriter


TWO_PARTIES = ["DEMOCRAT", "REPUBLICAN"]


# WLOG, positive margin is more D votes


def expected(y1_margin, y2_margin, y1_votes, y2_votes, y1_county_votes, y1_county_margin):
    national_vote_increase = y2_votes / float(y1_votes)
    expected_national_margin = national_vote_increase * y1_margin
    expected_r_voters = (y2_votes - expected_national_margin) / 2.0
    expected_d_voters = y2_votes - expected_r_voters
    actual_r_voters = (y2_votes - y2_margin) / 2.0
    rs_who_flipped = expected_r_voters - actual_r_voters
    pct_rs_who_flipped = max(0, rs_who_flipped) / expected_r_voters
    ds_who_flipped = -1 * rs_who_flipped
    pct_ds_who_flipped = max(0, ds_who_flipped) / expected_d_voters

    expected_county_voters = y1_county_votes * national_vote_increase
    expected_county_margin = y1_county_margin * national_vote_increase
    expected_county_rs = (expected_county_voters - expected_county_margin) / 2.0
    expected_county_ds = expected_county_voters - expected_county_rs
    adj_expected_county_rs = expected_county_rs + \
        expected_county_ds * pct_ds_who_flipped - \
        expected_county_rs * pct_rs_who_flipped
    adj_expected_county_ds = expected_county_ds + \
        expected_county_rs * pct_rs_who_flipped - \
        expected_county_ds * pct_ds_who_flipped
    return adj_expected_county_ds - adj_expected_county_rs


def validate_data(data_csv, columns):
    state_county_years = {(row[columns["state"]], row[columns["county_name"]], int(row[columns["year"]])) for row in data_csv}
    for state_county in state_county_years:
        state_county_rows = [d for d in data_csv if (d[columns["state"]], d[columns["county_name"]], int(d[columns["year"]])) == state_county]
        total = state_county_rows[0][columns["totalvotes"]]
        assert sum(int(row[columns["candidatevotes"]]) for row in state_county_rows) == int(total), (state_county, total, sum(int(row[columns["candidatevotes"]]) for row in state_county_rows))


data = CsvReader().read("countypres_2000-2024.csv")
# Data from https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
#  I have cleaned the data slightly
# validate_data(data.data, data.columns)
data_list = [row for row in data.data if row[data.columns["party"]] in TWO_PARTIES]

counties = {}
total_party_votes = {}
years_set = set()
for row in data_list:
    if f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}" not in counties:
        counties[f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"] = {}
    if row[data.columns["year"]] not in counties[f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"]:
        counties[f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"][row[data.columns["year"]]] = {}
    if row[data.columns["party"]] not in counties[
            f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"][row[data.columns["year"]]]:
        counties[
            f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"
        ][row[data.columns["year"]]][row[data.columns["party"]]] = 0
    counties[
        f"{row[data.columns['county_name']]}-{row[data.columns['state_po']]}"
    ][row[data.columns["year"]]][row[data.columns['party']]] += int(row[data.columns["candidatevotes"]])
    if row[data.columns["year"]] not in total_party_votes:
        total_party_votes[row[data.columns["year"]]] = {}
    if row[data.columns["party"]] not in total_party_votes[row[data.columns["year"]]]:
        total_party_votes[row[data.columns["year"]]][row[data.columns["party"]]] = 0
    total_party_votes[row[data.columns["year"]]][row[data.columns["party"]]] += int(row[data.columns["candidatevotes"]])
    years_set.add(row[data.columns["year"]])

for county, county_data in counties.items():
    # not sure what RI's federal precinct is.
    # Broomfield County was founded in 2001.
    # For some reason this data set splits out Kansas City's data after 2000.
    # UOCAVA = overseas voters. AK's district 99 is overseas voters.
    if county not in ["BROOMFIELD-CO", "MAINE UOCAVA-ME", "FEDERAL PRECINCT-RI", "DISTRICT 99-AK", "KANSAS CITY-MO"]:
        assert set(county_data.keys()) == years_set, (county, county_data)

years_list = sorted(list(years_set))
county_swings = {}
for county in counties.keys():
    if county in ["MAINE UOCAVA-ME", "FEDERAL PRECINCT-RI", "DISTRICT 99-AK"]:
        continue
    county_swings[county] = {}
    for year in years_list:
        if county in ["BROOMFIELD-CO", "KANSAS CITY-MO"] and year == '2000':
            for subsequent_year in [y for y in years_list if y > year]:
                county_swings[county][f"{year}-{subsequent_year}"] = {
                    "expected_margin": 0,
                    "actual_margin": 0,
                }
                county_swings[county][f"{year}-{subsequent_year}"]["diff"] = 0
                county_swings[county][f"{year}-{subsequent_year}"]["pct"] = 0
            continue
        for subsequent_year in [y for y in years_list if y > year]:
            county_swings[county][f"{year}-{subsequent_year}"] = {
                "expected_margin": expected(
                    total_party_votes[year]["DEMOCRAT"] - total_party_votes[year]["REPUBLICAN"],
                    total_party_votes[subsequent_year]["DEMOCRAT"] - total_party_votes[subsequent_year]["REPUBLICAN"],
                    sum(total_party_votes[year].values()),
                    sum(total_party_votes[subsequent_year].values()),
                    sum(counties[county][year].values()),
                    counties[county][year]["DEMOCRAT"] - counties[county][year]["REPUBLICAN"],
                ),
                "actual_margin": counties[county][subsequent_year]["DEMOCRAT"] -
                counties[county][subsequent_year]["REPUBLICAN"],
            }
            county_swings[county][f"{year}-{subsequent_year}"]["diff"] = \
                county_swings[county][f"{year}-{subsequent_year}"]["actual_margin"] - \
                county_swings[county][f"{year}-{subsequent_year}"]["expected_margin"]
            county_swings[county][f"{year}-{subsequent_year}"]["pct"] = \
                county_swings[county][f"{year}-{subsequent_year}"]["diff"] / \
                float(sum(counties[county][year].values()))


name = None
if len(sys.argv) > 1:
    name = sys.argv[1]

if not name:
    i = 1
    print(list(county_swings.keys())[i])
    for time, swing in county_swings[list(county_swings.keys())[i]].items():
        print(time, swing)

if name:
    print(name)
    for time, swing in county_swings[name].items():
        y1, y2 = time.split('-')
        if int(y2) - int(y1) == 4:
            print(time, swing)
    print("2012-2024", county_swings[name]["2012-2024"])
    print("2016-2024", county_swings[name]["2016-2024"])

states = {}
for county, swings in county_swings.items():
    for time, swing in swings.items():
        if county[-2:] not in states:
            states[county[-2:]] = {}
        if time not in states[county[-2:]]:
            states[county[-2:]][time] = {}
            for k in swing.keys():
                if k != "pct":
                    states[county[-2:]][time][k] = 0
        for k in swing.keys():
            if k != "pct":
                states[county[-2:]][time][k] += swing[k]

states_and_counties = {}
for county, data in county_swings.items():
    states_and_counties[county] = data
for state, data in states.items():
    states_and_counties[state] = data

diff_dict = {
    k: {
        t: t_data["diff"]
        for t, t_data in v.items()
    }
    for k, v in states_and_counties.items()
}

for place in diff_dict.keys():
    diff_dict[place]["place"] = place

columns = [
    "place", "2000-2004", "2000-2008", "2000-2012", "2000-2016", "2000-2020", "2000-2024",
    "2004-2008", "2004-2012", "2004-2016", "2004-2020", "2004-2024",
    "2008-2012", "2008-2016", "2008-2020", "2008-2024",
    "2012-2016", "2012-2020", "2012-2024",
    "2016-2020", "2016-2024",
    "2020-2024",
]

output_path = os.path.join(os.getcwd(), "output", "output.csv")
CsvWriter().write(dataWithColumns(data=[d for d in diff_dict.values()], columns=columns), output_path)
