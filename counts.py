import csv 
from collections import OrderedDict

res = dict()
with open('autostraddle-stats/data1.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for line in reader:
        if line[1] in res.keys():
            res[line[1]] += int(line[-1])
        else:
            res[line[1]] = int(line[-1])

print(sorted(res.items(), key=lambda item: item[1]))