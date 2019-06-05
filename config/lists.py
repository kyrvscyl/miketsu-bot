import json, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('../data/shikigami.json', 'r') as f:
	shikigami = json.load(f)

poolSP = list(shikigami['SP'].keys())
poolSSR = list(shikigami['SSR'].keys())
poolSR = list(shikigami['SR'].keys())
poolR = list(shikigami['R'].keys())
poolAll = poolSP + poolSSR + poolSR + poolR
countSP = len(poolSP)
countSSR = len(poolSSR)
countSR = len(poolSR)
countR = len(poolR)

with open("../lists/summon.lists", 'r') as f:
	summonList = f.read().splitlines()
	
with open("../lists/bosses.lists", 'r') as f:
	bossesList = f.read().splitlines()

with open("../lists/attack.lists", 'r') as f:
	attackVerb = f.read().splitlines()
