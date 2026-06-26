import re 
from bs4 import BeautifulSoup
import requests
import glob
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px
import pandas as pd

months = "(january|february|march|april|may|june|july|august|september|october|november|december|fall|spring|winter|summer)"
excl = r"^(?!Netflix|Apple|Hulu|HBO|Peacock|Prime Video|Paramount\+|Starz).+"
pattern = re.compile(excl, re.IGNORECASE)  # Case-insensitive matching
month_order = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "winter": 1, "spring": 4, "summer": 7, "fall": 10
}

done_extracted = [file.split('/')[-1][:-4] for file in glob.glob('autostraddle-stats/extracted-data/*.txt')]

with open('autostraddle-stats/data1.csv', 'r', encoding='utf-8') as f:
    done = [line.split(',')[0] for line in f]

def get_tv_guides_months(): 
    with open("autostraddle-stats/src/TV Lists _ Autostraddle_complete.html", "r", encoding="utf-8") as f:
        
        soup = BeautifulSoup(f)
        links = soup.find_all(href=re.compile(months))
        for link in links:
            print('****')
            # print(link)
            l = link['href']
            name = re.search(r'([^/]*)/$', l)
            print(name)
            contents = requests.get(l)
            if f"{name}.html" not in files:
                with open(f"autostraddle-stats/data/{name}.html", 'w', encoding='utf-8') as g:
                    g.write(contents.text)

def extract_month_year(file):
        year, month = None, None
        name = re.search(r"autostraddle-stats/data/(.*)\.html", file).group(1)
        if re.search(rf"({months}-20\d\d).*", name):
            date = re.search(rf"({months}-20\d\d).*", name)
            month, year = date.group(1).split('-')
        elif re.search(rf"(20\d\d-{months})", name):
            date = re.search(rf"(20\d\d-{months})", name)
            year, month = date.group(1).split('-')
        return file, name, year, month
        

def extract_data(file, name, year, month):   
    comment = ''          
    with open(file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        # hopefully all are in strong balise
        tags = soup.find_all(['strong'])
        # Filter tags whose text does NOT match the exclusion pattern 
        filtered_tags = [tag for tag in tags if tag.get_text(strip=True) and pattern.match(tag.get_text(strip=True))]

    # if name not in done_extracted:
    #     with open(f'autostraddle-stats/extracted_data/{name}.txt', 'w', encoding='utf-8') as f:
    #         for tag in filtered_tags:
    #             print(tag.text)
    #             f.write(tag.text + '\n')

def count_clean(file, name, year, month):
    with open(file, 'r', encoding='utf-8') as f:
        counts = len([line for line in f])
    if name not in done: 
        with open('autostraddle-stats/data1.csv', 'a', newline='', encoding='utf-8') as g: 
            writer = csv.writer(g)
            writer.writerow([name, year, month, counts])

# couldn't be bothered with plt: thanks Mistral AI
# Define the order of months and seasons for sorting
# Chargement des données
def quantification():
    data = []
    with open('autostraddle-stats/data1.csv', 'r', encoding='utf-8') as g:
        reader = csv.reader(g)
        next(reader)  # Skip header
        for line in reader:
            try:
                title, year, month, count = line
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



if __name__ == '__main__':
    # files = glob.glob("autostraddle-stats/data/*")
    # for file in files:
    #     if file.split('/')[-1][:-5] not in done:
    #         file, name, year, month = extract_month_year(file)
    #         if year != None:
    #             # extract_data(file, name, year, month )
    #             try:
    #                 extracted_data_file = f'autostraddle-stats/extracted_data/{file.split('/')[-1][:-4]}txt'
    #                 count_clean(extracted_data_file, name, year, month)
    #             except FileNotFoundError:
    #                 continue
            # else:
            #     print(name+'\n')            
    df = quantification()
    visualisation(df)

