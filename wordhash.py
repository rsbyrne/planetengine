import math
import random
import os

path = os.path.dirname(__file__)

with open(os.path.join(path, 'words_alpha.txt'), 'r') as file:
    wordlist = list(set(file.read().split('\n')))

def wordhash(hashID, shortening = 10):
    random.seed(hashID)
    nWords = math.ceil(len(hashID) * math.log(260, len(wordlist)) / shortening)
    wordhashlist = random.sample(wordlist, nWords)
    wordhashstr = '-'.join(wordhashlist).replace('--', '-')
    random.seed()
    return wordhashstr

with open(os.path.join(path, 'moby.txt'), 'r') as file:
    mobystring = file.read().replace(' ', 'xxxsplitherexxx')
cleanstring = ''.join(e for e in mobystring if e.isalpha()).lower()
rawmobylist = cleanstring.split('xxxsplitherexxx')
mobylist = sorted(list(set(rawmobylist)))[1:]
del mobystring
del cleanstring
del rawmobylist

def mobyhash(hashID, shortening = 10):
    random.seed(hashID)
    mobyhashlen = math.ceil(len(hashID) * math.log(260, len(mobylist)))
    mobyhashlist = random.sample(mobylist, mobyhashlen)
    mobyhashstr = '-'.join(mobyhashlist).replace('--', '-').lower()
    random.seed()
    return mobyhashstr