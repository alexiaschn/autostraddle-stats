import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px
import pandas as pd
import glob 
import json
import re 
import csv 
from collections import Counter


files = [file for file in glob.glob('autostraddle-stats/enriched_data_full/*.json')]


months = "(january|february|march|april|may|june|july|august|september|october|november|december|fall|spring|winter|summer)"
excl = r"^(?!Netflix|Apple|Hulu|HBO|Peacock|Prime Video|Paramount\+|Starz).+"
pattern = re.compile(excl, re.IGNORECASE)  # Case-insensitive matching
month_order = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "winter": 1, "spring": 4, "summer": 7, "fall": 10
}


def extract_month_year(file):
    year, month = None, None
    name = file.split('/')[-1]
    if re.search(rf"({months}-20\d\d).*", name):
        date = re.search(rf"({months}-20\d\d).*", name)
        month, year = date.group(1).split('-')
    elif re.search(rf"(20\d\d-{months})", name):
        date = re.search(rf"(20\d\d-{months})", name)
        year, month = date.group(1).split('-')
    return file, name, year, month
 


def count_clean(file, name, year, month):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        counts = len(data)
        titles = [movie['Title'] for movie in data]
    with open('autostraddle-stats/data3.csv', 'a', newline='', encoding='utf-8') as g: 
        writer = csv.writer(g)
        writer.writerow([name, year, month, counts, titles])

# couldn't be bothered with plt: thanks Mistral AI
# Define the order of months and seasons for sorting
# Chargement des données
def quantification():
    data = []
    with open('autostraddle-stats/data3.csv', 'r', encoding='utf-8') as g:
        reader = csv.reader(g)
        next(reader)  # Skip header
        for line in reader:
            try:
                title, year, month, count, movies = line
                month_num = month_order.get(month.lower(), 0)
                data.append({
                    'Title': title, 
                    'Year': int(year), 
                    'Month': month, 
                    'MonthNum': month_num, 
                    'Count': int(count)
                })
            except ValueError:
                print(line)
                break
                

    # Tri des données
    data.sort(key=lambda x: (x['Year'], x['MonthNum']))

    # Création d'un DataFrame pour Plotly
    df = pd.DataFrame(data)
    df['YearMonth'] = df['Year'].astype(str) + ' - ' + df['Month']
    return df


def visualisation(df):
    # Création du graphique interactif
    fig = px.line(df, x='YearMonth', y='Count', 
                hover_data=['Title', 'Year', 'Month', 'Count'],
                title='Counts by Month and Year')

    fig.update_layout(xaxis_tickangle=45)
    fig.show()

def most_recommanded():
    tops = dict()
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for movie in data:
                normalized_title = re.sub('’', "'", movie['Title'])
                normalized_title = normalized_title.lower()
                if normalized_title in tops.keys():
                    tops[normalized_title] += 1
                else:
                    tops[normalized_title] = 1
    tops = dict(sorted(tops.items(), key=lambda item: item[1], reverse=True))
    with open('autostraddle-stats/tops.json', 'w', encoding='utf-8') as g:
        json.dump(tops, g, indent=2, ensure_ascii=False)

def visualisation_most_reco():
    with open('autostraddle-stats/tops.json', 'r', encoding='utf-8') as g:
        data = json.load(g)
        freq_of_freq = Counter(data.values())
        x = sorted(freq_of_freq.keys())
        y = [freq_of_freq[k] for k in x]

        plt.bar(x, y)
        plt.yscale("log")  # counts of counts often span orders of magnitude
        plt.xlabel("TV Series or film occurs N times")
        plt.ylabel("Number of recommandations (log scale)")
        plt.title("Distribution of recommandation frequencies")
        # plt.show()
        plt.savefig("autostraddle-stats/freq.png", dpi=150, bbox_inches="tight")

def visualisation_most_recommanded_films():
    with open('autostraddle-stats/tops.json', 'r', encoding='utf-8') as g:
        data = json.load(g)
        top_n = sorted(data.items(), key=lambda x: -x[1])[:20]
        reco, counts = zip(*top_n)

        plt.figure(figsize=(10, 5))
        plt.bar(reco, counts)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Occurrences")
        plt.title("Top 20 most frequent recommandations")
        plt.tight_layout()
        plt.savefig("autostraddle-stats/20_most_reco.png", dpi=150, bbox_inches="tight")
        
if __name__ == '__main__':
    # for file in files:
    #     print(file)
    #     file, name, year, month = extract_month_year(file)
    #     count_clean(file, name, year, month)
    df = quantification()

    visualisation(df)

    # visualisation_most_recommanded_films()