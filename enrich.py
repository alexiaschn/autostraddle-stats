import re 
import json
import glob
import requests
import time

API_KEY = '3fbfa58a'
BASE_URL = 'http://www.omdbapi.com/'

files = [file for file in glob.glob('autostraddle-stats/extracted_data/*.txt')]
done = [file.split('/')[-1][:-5] for file in glob.glob('autostraddle-stats/enriched_data/*.json')]

URL =  "https://api.tvmaze.com/search/shows"

files_complete = [file for file in glob.glob('autostraddle-stats/enriched_data/*.json')]
done_complete = [file.split('/')[-1] for file in glob.glob('autostraddle-stats/enriched_data_full/*.json')]


def get_title(line):
    # monster regex
    t = re.search(r'^(.+?)(?:\s*\((?!\d{4}\))[^)]*\))*(\s*\(\d{4}\))?(?:\s*\([^)]*\))*(?:\s*(?:[-–—]|\(|\/\/).*)?$', line)
    if t is not None:
        title = t.group(1)
        if t.group(2) is not None:
            year = re.search(r'\((\d{4})\)', t.group(2)).group(1)
        else:
            year = None
    else:
        # print(f'did not : {line} on {file}')
        title = line
        year = None
    return title, year

def call(title, year):
    if year is not None:
        to_send = f'{BASE_URL}?t={title}&y={year}&apikey={API_KEY}'
    else:
        to_send = f'{BASE_URL}?t={title}&apikey={API_KEY}'
    try: 
        response = requests.get(to_send)
        # print(response)
        if response.status_code == 200:
            posts = response.json()
            return posts
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None

def complete_TV_info(file):
    res = []
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for movie in data:
            if 'Rated' not in movie.keys():
                clean_title = re.sub(r'\*', '', movie['Title'])
                clean_title = re.sub(r':? ?Seasons? (One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+)', '', clean_title)
                clean_title = re.sub(r':? ?Limited Series', '', clean_title)
                clean_title = re.sub(r'Complete Series', '', clean_title)
                clean_title = re.sub(r'NEW! ', '', clean_title)
                clean_title = re.sub(r'Premiere', '', clean_title)
                clean_title = re.sub(r'Special Episode', '', clean_title)
                clean_title = re.sub(r'\d? Episodes?', '', clean_title)
                clean_title = re.sub(r':$', '', clean_title)
                print(clean_title)
                try:
                    response = requests.get(f'{URL}?q={clean_title}')
                    if response.status_code == 200:
                        info = response.json()
                        if len(info) > 0 :
                            movie['Genre'] = info[0]['show']['genres']
                            movie['Year'] = info[0]['show']['premiered']
                            res.append(movie)
                        else: 
                            res.append(movie)
                except requests.exceptions.RequestException as e:
                    print('Error:', e)
                    
            else:
                res.append(movie)
    with open(f'autostraddle-stats/enriched_data_full/{name}', 'w', encoding='utf-8') as g:
        json.dump(res, g, indent=3, ensure_ascii=False)


if __name__ == '__main__':
    file = 'autostraddle-stats/extracted_data/spring-2019-tv-preview-shows-thatll-please-your-eyeballs-with-lgbtq-women-characters-454850.txt'
    # for file in files:
    # done = []
    name = file.split('/')[-1][:-4]
    # if name not in done:
    #     res = []
    #     with open(file, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             title, year = get_title(line)
    #             print(f'{title}: {year}')
    #             time.sleep(1)
    #             info = call(title, year)
    #             try:
    #                 if info['Response'] == 'False':
    #                     res.append({'Title': title, 'Year': year})
    #                 else:
    #                     res.append(info)
    #             except TypeError:
    #                 res.append({'Title': title, 'Year': year})

    #     print(res)
    #     with open(f"autostraddle-stats/enriched_data/{name}.json", 'w', encoding='utf-8') as g:
    #         json.dump(res, g, indent=3, ensure_ascii=False)

    # for file in files_complete:
    #     print(file)
    #     name = file.split('/')[-1]
    #     if name not in done_complete:
    #         complete_TV_info(file)
    complete_TV_info(f"autostraddle-stats/enriched_data/{name}.json")
    
                
                
