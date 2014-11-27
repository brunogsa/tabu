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
  while attempt < 10:
    attempt += 1
    team = heroes.loc[random.sample(heroes.index, len(villains_team))]
    if is_feasible_solution(villains_team, team, budget):
      break
  return team
  
  
def is_feasible_solution(villains, heroes, budget):
  # O número de heróis escolhidos é menor ou igual ao de vilões
  feasible = len(heroes) <= len(villains)
  
  # Para cada habilidade H, (Ex força, velocidade, etc...) 
  # a média de H dos heróis escolhidos é maior que a média de H dos vilões
  villains_skills = villains[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean()
  heroes_skills = heroes[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]].mean()
  
  feasible &= True in villains_skills.sub(heroes_skills).apply(lambda diff: diff < 0).values
  
  # O custo" dos heróis escolhidos é menor ou igual ao "orçamento" disponível, 
  # sendo o custo: a soma das habilidades e da popularidade dos heróis escolhidos.
  feasible &= budget >= villains[["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills", "Number of Comic Books Where Character Appeared"]].sum().values.sum()
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
  print budget
  #heroes_team = construct_initial_solution(villains, heroes, villains_team, budget)
  #print "Heroes team:"
  #print heroes_team

main()
