import re 
from bs4 import BeautifulSoup
import requests
import glob
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px
import pandas as pd

def extract(file, name):
    with open(file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        tags = soup.find_all('h4')
        counts = len(tags)
    with open(f'autostraddle-stats/extracted_data/{name}.txt', 'w', encoding='utf-8') as f:
      for tag in tags:
          f.write(tag.text + '\n')

t = 'autostraddle-stats/data/july-2024-whats-new-gay-and-streaming.html'
extract(t, t.split('/')[-1][:-5])