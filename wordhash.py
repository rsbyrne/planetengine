import math
import random
import os
import csv
import unicodedata

class Reseed:
    def __init__(self, randomseed = None):
        if randomseed is None:
            randomseed = random.random()
        self.randomseed = randomseed
    def __enter__(self):
        random.seed(self.randomseed)
    def __exit__(self, *args):
        random.seed()

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

def wordhash(hashID, nWords = 2):
    with Reseed(hashID):
        wordhashlist = []
        for n in range(nWords):
            randindex = random.randint(0, (len(wordlist) - 1))
            wordhashlist.append(wordlist[randindex])
        wordhashstr = '-'.join(wordhashlist).replace('--', '-').lower()
    return wordhashstr

def _make_syllables():
    consonants = list("bcdfghjklmnpqrstvwxyz")
    conclusters = ['bl', 'br', 'dr', 'dw', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr', 'kw', 'pl', 'pr', 'sf', 'sk', 'sl', 'sm', 'sn', 'sp', 'st', 'sw', 'tr', 'tw']
    condigraphs = ['sh', 'ch', 'th', 'ph']
    allcons = [*consonants, *conclusters, *condigraphs]
    vowels = [*list("aeiou")]
    syllables = [consonant + vowel for vowel in vowels for consonant in allcons]
    syllables.extend([vowel + syllable for vowel in vowels for syllable in syllables])
    syllables = list(sorted(syllables))
    return syllables

SYLLABLES = _make_syllables()

def random_syllable():
    syllable = random.choice(SYLLABLES)
    return syllable

def random_word(length = 3):
    outWord = ''
    for _ in range(length):
        outWord += random_syllable()
    return outWord

def random_phrase(phraselength = 2, wordlength = 3):
    phraseList = []
    for _ in range(phraselength):
        phraseList.append(
            random_word(wordlength)
            )
    phrase = "-".join(phraseList)
    return phrase

def get_random_word(randomseed = None, **kwargs):
    with Reseed(randomseed):
        output = random_word(**kwargs)
    return output

def get_random_phrase(randomseed = None, **kwargs):
    with Reseed(randomseed):
        output = random_phrase(**kwargs)
    return output

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
