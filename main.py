# -*- coding: utf-8 -*-
import sys
import config
import math
import random
import numpy as np
import pandas as pd

MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 20
POWERGRID = ["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]
POPULARITY = "Number of Comic Books Where Character Appeared"

# Versão 1: Sortear soluções e verificar se é viável
def construct_initial_solution(villains, heroes, villains_team, budget):
  # Variável 'attempt' criada para evitar loop infinito
  attempt = 0
  while attempt < 50:
    attempt += 1
    heroes_team = heroes.loc[random.sample(heroes.index, len(villains_team))]
    if is_viable_solution(villains_team, heroes_team, budget):
      break
  
  return heroes_team
  
# Verifica se uma solução é viável dados um time de vilões, 
# um time de heróis e um orçamento disponível
def is_viable_solution(villains_team, heroes_team, budget):
  # Não é solução viável se o time de heróis é MAIOR que o de vilões
  if len(heroes_team) > len(villains_team): return False
  
  # CALCULAR CUSTO DO TIME
  # CUSTO: SUM(Popularidade[h]*PowegridMedio[h]) para cada herói h
  
  # Para cada herói, calcula a média de suas hablidades (powergrid médio)
  heroes_team_pg = heroes_team[POWERGRID].mean(1).values

  # Para cada herói, seleciona sua popularidade
  heroes_team_pop = heroes_team[POPULARITY].values
  
  # Multiplica powergrid médio e popularidade e soma os resultados para obter custo
  heroes_cost = (heroes_team_pg*heroes_team_pop).sum()
  
  # Não é solução viável se o custo do time de heróis é maior que o orçamento
  if heroes_cost > budget: return False

  # Para cada vilão, calcula a média de suas hablidades (powergrid médio)
  villains_team_pg = villains_team[POWERGRID].mean(1).values

  # Não é solução viável se a média das habilidades dos vilões é MAIOR que a média dos heróis
  if villains_team_pg.mean() > heroes_team_pg.mean(): return False
  
  return True

# Calcula orçamento disponível, ver slide enviado pelo professor
def calculate_budget(villains, heroes, villains_team):
  # Exp 1
  heroes_pg = heroes[POWERGRID].mean(1).values.mean()
  villains_team_pg = villains_team[POWERGRID].mean(1).values.mean()
  ratio_pg = heroes_pg/villains_team_pg
  
  heroes_pop = heroes[POPULARITY].mean()
  villains_team_pop = villains_team[POPULARITY].mean()
  ratio_pop = heroes_pop/villains_team_pop
  
  villains_team_pg = villains_team[POWERGRID].mean(1).values
  villains_team_pop = villains_team[POPULARITY].values
  vt_cost = (villains_team_pg*villains_team_pop).sum()
  
  exp1 = ratio_pg*ratio_pop*vt_cost
  
  # Exp 2
  villains_pg = villains[POWERGRID].mean(1).values.mean()
  factor = villains_team_pg.mean()/villains_pg

  exp2 = factor*heroes_pg*heroes_pop*len(villains_team)
  
  return max(exp1, exp2)

def collaboration_level(collaboration, heroes_team, villains_team):
  heroes_ids = heroes_team["Character ID"].values
  
  c_level = 0
  c_heroes = collaboration.loc[(collaboration["Character 1 ID"].isin(heroes_ids)) & (collaboration["Character 2 ID"].isin(heroes_ids))]
  if not c_heroes.empty:
    c_level += c_heroes["Number of Comic Books Where Character 1 and Character 2 Both Appeared"].sum()/2
  
  c_villains = collaboration.loc[(collaboration["Character 1 ID"].isin(heroes_ids)) & (collaboration["Character 2 ID"].isin(villains_team))]
  if not c_villains.empty:
    c_level += c_villains["Number of Comic Books Where Character 1 and Character 2 Both Appeared"].sum()
  
  return c_level


def tabu_search(villains, heroes, villains_team, collaboration, budget):
  # Inserir na busca local uma lista de movimentos tabu que
  # impedem, por algumas iterações, que um determinado
  # movimento seja realizado.
  # Objetivo: evitar que uma solução seja revisitada.
  # Exemplo: no caso da equipartição de grafos, pode-se impedir
  # que a troca de dois vértices por t iterações.
  # Repetir a busca local básica por α iterações ou se nenhuma
  # melhora foi obtida nas últimas β iterações.
  # Os parâmetros α e β são fixados a priori.
  # Parâmetros a ajustar: tamanho da lista tabu t, α e β.

  gl_solution = -1 # Melhor solução global
  gl_last_improvement = 0 # Iterações desde a última melhoria
  while gl_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
    # Contrói solução inicial
    heroes_team = construct_initial_solution()
    lc_solution = collaboration_level(collaboration, heroes_team, villains_team)
    lc_last_improvement = 0
    
    while lc_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
      neighboor_solutions = []
      # TODO: Gera soluções vizinhas (levando o tabu em consideração)
      # TODO: Encontra a melhor solução e faz dela a atual
      # TODO: Coloca no tabu os movimentos realizados para chegar na solução atual
      
      curr_solution = -1
      if curr_solution > lc_solution:
        lc_solution = curr_solution
        lc_last_improvement = 0
      else:
        lc_last_improvement += 1

    if lc_solution > gl_solution:
      gl_solution = lc_solution
      gl_last_improvement = 0
    else: 
      gl_last_improvement += 1


def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")

  df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
  villains = df.loc[df['Hero or Villain'] == 'villain']
  heroes = df.loc[df['Hero or Villain'] == 'hero']

  villains_team = df.loc[df["Character ID"].isin(villains_ids)]
  budget = calculate_budget(villains, heroes, villains_team)
  heroes_team = construct_initial_solution(villains, heroes, villains_team, budget)

  collaboration = pd.read_csv(config.SHARED_COMICS_CSV, sep=';')
  
  print "Villains team:"
  print villains_team["Character Name"]

  print "Heroes team:"
  print heroes_team["Character Name"]

  cl = collaboration_level(collaboration, heroes_team, villains_team)
  print "collaboration_level:"
  print cl

main()
