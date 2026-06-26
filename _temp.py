import glob
import os

files = [file for file in glob.glob('autostraddle-stats/extracted_data/*')]
for file in files:
    os.rename(file, f'{file}.txt')