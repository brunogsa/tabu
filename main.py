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
  # TODO: Calcular como no slide
  return 1000

def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")

  df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
  villains = df.loc[df['Hero or Villain'] == 'hero']
  heroes = df.loc[df['Hero or Villain'] == 'hero']
  villains_team = df.loc[df["Character ID"].isin(villains_ids)]
  budget = calculate_budget(villains, heroes, villains_team)
  heroes_team = construct_initial_solution(villains, heroes, villains_team, budget)
  print "Heroes team:"
  print heroes_team

main()
