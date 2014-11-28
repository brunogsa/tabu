# -*- coding: utf-8 -*-
import sys
import config
import math
import random
import numpy as np
import pandas as pd


# 1a versão: Buscar uma solução viável qualquer
def construct_initial_solution(villains, heroes, villains_team, budget):
  attempt = 0
  while attempt < 50:
    attempt += 1
    heroes_team = heroes.loc[random.sample(heroes.index, len(villains_team))]
    if is_feasible_solution(villains_team, heroes_team, budget):
      break
  print str(attempt) + " attempts"
  return heroes_team
  
  
def is_feasible_solution(villains_team, heroes_team, budget):
  # O número de heróis escolhidos é menor ou igual ao de vilões
  feasible = len(heroes_team) <= len(villains_team)
  if not feasible: return False
  
  # O custo" dos heróis escolhidos é menor ou igual ao "orçamento" disponível, 
  # sendo o custo: o somatório de Popularidade[h]*PowegridMedio[h] para os h heróis do time.
  heroes_team_pg = heroes_team[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values
  heroes_team_pop = heroes_team["Number of Comic Books Where Character Appeared"].values
  heroes_cost = (heroes_team_pg*heroes_team_pop).sum()
  feasible &= budget >= heroes_cost
  if not feasible: return False

  # A média das habilidades dos heróis escolhidos é maior que a média dos vilões
  villains_team_pg = villains_team[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values

  feasible &= heroes_team_pg.mean() > villains_team_pg.mean()
  
  return feasible
  
def calculate_budget(villains, heroes, villains_team):
  # Exp 1
  heroes_pg = heroes[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values.mean()
  villains_team_pg = villains_team[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values.mean()
  ratio_pg = heroes_pg/villains_team_pg
  
  heroes_pop = heroes["Number of Comic Books Where Character Appeared"].mean()
  villains_team_pop = villains_team["Number of Comic Books Where Character Appeared"].mean()
  ratio_pop = heroes_pop/villains_team_pop
  
  villains_team_pg = villains_team[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values
  villains_team_pop = villains_team["Number of Comic Books Where Character Appeared"].values
  vt_cost = (villains_team_pg*villains_team_pop).sum()
  
  exp1 = ratio_pg*ratio_pop*vt_cost
  
  # Exp 2
  villains_pg = villains[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean(1).values.mean()
  factor = villains_team_pg.mean()/villains_pg

  exp2 = factor*heroes_pg*heroes_pop*len(villains_team)
  
  return max(exp1, exp2)

def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")

  df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
  villains = df.loc[df['Hero or Villain'] == 'villain']
  heroes = df.loc[df['Hero or Villain'] == 'hero']
  villains_team = df.loc[df["Character ID"].isin(villains_ids)]
  budget = calculate_budget(villains, heroes, villains_team)
  heroes_team = construct_initial_solution(villains, heroes, villains_team, budget)
  
  print "Villains team:"
  print villains_team

  print "Heroes team:"
  print heroes_team

main()
