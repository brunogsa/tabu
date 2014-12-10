# -*- coding: utf-8 -*-
import config
import math
import numpy as np
from marvel_tabu import MarvelTabu
import os
import sys

def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")
  marvel_tabu = MarvelTabu(villains_ids, os.environ.get('WITH_BUDGET') != None)
  team = marvel_tabu.tabu_search()

  if os.environ.get('DEBUG') != None:
    print "Villains team:"
    print marvel_tabu.villains_team["Character Name"]

    print "Heroes team:"
    print team["team"]["Character Name"]

  cl = team["collaboration_level"]

  collaboration_heroes = marvel_tabu.collaboration_level(team["team"])
  fighting_experience = marvel_tabu.fighting_experience(team["team"]["Character ID"].values)


  if os.environ.get('DEBUG') != None:
    if os.environ.get('WITH_BUDGET') != None:
      print "collaboration_level (with budget):"
    else:
      print "collaboration_level (without budget):"

  if os.environ.get('WITH_BUDGET') != None:
    print str(cl) + "\t" + str(collaboration_heroes) + "\t" + str(fighting_experience) + "\t" + ','.join(team["team"]["Character ID"].values) + "\t" + str(marvel_tabu.budget())
  else:
    print str(cl) + "\t" + str(collaboration_heroes) + "\t" + str(fighting_experience)
    

main()
