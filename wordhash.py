import math
import random
import os
import csv
import unicodedata

path = os.path.join(os.path.dirname(__file__), 'hashwords')

placenames = []
with open(os.path.join(path, 'worldcities.csv')) as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    next(reader)
    for row in reader:
        city, country, state, number = row
        words = [city, country, state]
        for word in words:
            outwd = unicodedata.normalize('NFD', word)
            outwd = outwd.encode('ascii', 'ignore')
            outwd = outwd.decode("utf-8")
            outwd = ''.join(filter(str.isalpha, outwd)).lower()
            if outwd.isalpha():
                placenames.append(outwd)
placenames = list(set(placenames))

babynames = []
with open(os.path.join(path, 'babynames.csv')) as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    next(reader)
    for row in reader:
        word = row[3]
        outwd = unicodedata.normalize('NFD', word)
        outwd = outwd.encode('ascii', 'ignore')
        outwd = outwd.decode("utf-8")
        outwd = ''.join(filter(str.isalpha, outwd)).lower()
        if outwd.isalpha:
            babynames.append(outwd)
babynames = list(set(babynames))

with open(os.path.join(path, 'wordsalpha.txt'), 'r') as file:
    englishwords = list(set(file.read().split('\n')))

wordlist = sorted(list(set([*englishwords, *placenames, *babynames])))

def wordhash(hashID, shortening = 10):
    random.seed(hashID)
    nWords = math.ceil(len(hashID) * math.log(260, len(wordlist)) / shortening)
    wordhashlist = []
    for n in range(nWords):
        randindex = random.randint(0, (len(wordlist) - 1))
        wordhashlist.append(wordlist[randindex])
    wordhashstr = '-'.join(wordhashlist).replace('--', '-').lower()
    random.seed()
    return wordhashstr

# with open(os.path.join(path, 'moby.txt'), 'r') as file:
#     mobystring = file.read().replace(' ', 'xxxsplitherexxx')
# cleanstring = ''.join(e for e in mobystring if e.isalpha()).lower()
# rawmobylist = cleanstring.split('xxxsplitherexxx')
# mobylist = sorted(list(set(rawmobylist)))[1:]
# del mobystring
# del cleanstring
# del rawmobylist

# def mobyhash(hashID, shortening = 10):
#     random.seed(hashID)
#     mobyhashlen = math.ceil(len(hashID) * math.log(260, len(mobylist)))
#     mobyhashlist = random.sample(mobylist, mobyhashlen)
#     mobyhashstr = '-'.join(mobyhashlist).replace('--', '-').lower()
#     random.seed()
#     return mobyhashstr