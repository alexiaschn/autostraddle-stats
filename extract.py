import re 
from bs4 import BeautifulSoup
import requests
import glob
import csv
import matplotlib.pyplot as plt
from datetime import datetime


ok = "(january|february|march|april|may|june|july|august|september|october|november|december|fall|spring|winter|summer)"
def check(): 
    with open("autostraddle-stats/src/TV Lists _ Autostraddle_complete.html", "r", encoding="utf-8") as f:
        
        soup = BeautifulSoup(f)
        links = soup.find_all(href=re.compile(ok))
        for link in links:
            print('****')
            # print(link)
            l = link['href']
            name = re.search(r'([^/]*)/$', l)
            print(name.group(1))
            contents = requests.get(l)
            if f"{name.group(1)}.html" not in files:
                with open(f"autostraddle-stats/data/{name.group(1)}.html", 'w', encoding='utf-8') as g:
                    g.write(contents.text)






# check()   
files = glob.glob("autostraddle-stats/data/*")

excl = r"^(?!Netflix|Apple|Hulu|HBO|Peacock|Prime Video|Paramount\+|Starz).+"
pattern = re.compile(excl, re.IGNORECASE)  # Case-insensitive matching



def reste():
    for file in files:
        print(file)
        name = re.search(r"autostraddle-stats/data/(.*)\.html", file)
        date = re.search(rf"({ok}-20\d\d).*", name.group(1))
        if date:
            month, year = date.group(1).split('-')

            with open(file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                # hopefully all are in strong balise
                tags = soup.find_all(['strong'])
                # Filter tags whose text does NOT match the exclusion pattern 
                filtered_tags = [tag for tag in tags if tag.get_text(strip=True) and pattern.match(tag.get_text(strip=True))]
                counts = len(filtered_tags)
                if counts < 5:
                    with open(f'autostraddle-stats/manual_check/{name.group(1)}.html', 'w', encoding='utf-8') as g2:
                        g2.write(f.read())
                else:
                    for t in filtered_tags:
                        print('****')
                        print(t)
                    with open('autostraddle-stats/counts.csv', 'a', newline='', encoding='utf-8') as g: 
                        writer = csv.writer(g)
                        writer.writerow([name.group(1), year, month, counts])

# couldn't be bothered with plt: thanks Mistral AI
# Define the order of months and seasons for sorting
month_order = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "winter": 1, "spring": 4, "summer": 7, "fall": 10
}
def sure_letsdothattoo():
    with open('autostraddle-stats/counts.csv', 'r', encoding='utf-8') as g:
        reader = csv.reader(g)
        header = next(reader)  # Skip header if present
        data = []
        for line in reader:
            title, year, month, count = line
            # Convert month to a numerical value for sorting
            month_num = month_order.get(month.lower(), 0)
            data.append((int(year), month_num, month, int(count)))

        # Sort by year, then by month
        data.sort(key=lambda x: (x[0], x[1]))

        # Extract sorted data for plotting
        years = [str(item[0]) for item in data]
        months = [item[2] for item in data]
        counts = [item[3] for item in data]

        # Plotting
        plt.figure(figsize=(15, 6))
        plt.plot(range(len(data)), counts, marker='o')
        plt.xticks(range(len(data)), [f"{y}-{m}" for y, m in zip(years, months)], rotation=45)
        plt.xlabel('Year-Month')
        plt.ylabel('Count')
        plt.title('Counts by Month and Year')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("autostraddle-stats/plot.png")
        plt.show()

reste()
sure_letsdothattoo()