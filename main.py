# -*- coding: utf-8 -*-
import config
import math
import numpy as np
from marvel_tabu import MarvelTabu
import os
import sys

def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")
  marvel_tabu = MarvelTabu(villains_ids, math.floor(len(villains_ids))/2, os.environ.get('WITH_BUDGET') != None)
  team = marvel_tabu.tabu_search()

  if os.environ.get('DEBUG') != None:
    print "Villains team:"
    print marvel_tabu.villains_team["Character Name"]

    print "Heroes team:"
    print team["team"]["Character Name"]

  cl = team["collaboration_level"]
  if os.environ.get('DEBUG') != None:
    if os.environ.get('WITH_BUDGET') != None:
      print "collaboration_level (with budget):"
    else:
      print "collaboration_level (without budget):"
  print cl

main()
