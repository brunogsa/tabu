# -*- coding: utf-8 -*-
import sys
import config
import math
import random
import numpy as np
import pandas as pd

MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 100
POWERGRID = ["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]
POPULARITY = "Number of Comic Books Where Character Appeared"
COLLABORATION_LEVEL = "Number of Comic Books Where Character 1 and Character 2 Both Appeared"


def construct_solution(initial_heroes_team, exclusion_list, villains_team, budget, villains, heroes, collaboration):
  # tamanho maximo do time de herois

  # TODO make a list with only heroes collaboration

  team_max_size = len(villains_team)

  heroes_team = initial_heroes_team

  # obter os herois para a solucao inicial
  # obtem um par de herois que tem a colaboracao maxima
  if len(heroes_team) == 0:
    tmp = collaboration.loc[-collaboration["Character 1 ID"].isin(villains["Character ID"]) & -collaboration["Character 2 ID"].isin(villains["Character ID"])]
    max_collaboration = tmp.loc[tmp[COLLABORATION_LEVEL].argmax()]
    heroes_team = heroes.loc[heroes["Character ID"].isin([max_collaboration["Character 1 ID"]]) | heroes["Character ID"].isin([max_collaboration["Character 2 ID"]])]
    exclusion_list.append(heroes_team[1:2]["Character ID"].values[0])

  # enquanto nao encontrar uma solucao viavel, continua procurando
  while not is_viable_solution(villains_team, heroes_team, budget):
    # remove um heroi da lista caso nao for solucao viavel
    exclusion_list.append(heroes_team[0:1]["Character ID"].values[0])
    heroes_team = heroes_team[1:]

    # enquanto nao tiver o tamanho maximo de time
    while len(heroes_team) < team_max_size:
      # condicao de parada para solucao inviavel
      if len(heroes_team) + len(exclusion_list) > len(heroes):
        return None

      random_hero = heroes_team.loc[random.sample(heroes_team.index, 1)]
      tmp = collaboration.loc[collaboration["Character 1 ID"].isin([random_hero["Character ID"].values[0]])]
      tmp = tmp.loc[-tmp["Character 2 ID"].isin(exclusion_list)]
      tmp = tmp.loc[-tmp["Character 2 ID"].isin(villains["Character ID"])]
      max_collaboration = tmp.loc[tmp[COLLABORATION_LEVEL].argmax()]
      hero_max_colaboration_level = heroes.loc[heroes["Character ID"].isin([max_collaboration["Character 2 ID"]])]
      heroes_team = heroes_team.append(hero_max_colaboration_level)
      exclusion_list.append(hero_max_colaboration_level["Character ID"].values[0])

  return heroes_team

# Versão 1: considerando usar a mesma funcao do tabu search
def construct_initial_solution(villains_team, budget, villains, heroes, collaboration):
  initial_heroes_team = pd.DataFrame(columns=heroes.columns.values)
  return construct_solution(initial_heroes_team, [], villains_team, budget, villains, heroes, collaboration)
  
# Verifica se uma solução é viável dados um time de vilões, 
# um time de heróis e um orçamento disponível
def is_viable_solution(villains_team, heroes_team, budget):
  # Não é solução viável se o time de heróis é MAIOR que o de vilões
  if len(heroes_team) != len(villains_team): return False

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
    c_level += c_heroes[COLLABORATION_LEVEL].sum()/2

  c_villains = collaboration.loc[(collaboration["Character 1 ID"].isin(heroes_ids)) & (collaboration["Character 2 ID"].isin(villains_team))]
  if not c_villains.empty:
    c_level += c_villains[COLLABORATION_LEVEL].sum()
  
  return c_level


def tabu_search(villains, heroes, villains_team, collaboration, budget, max_tabu, max_candidates):
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

  # Constrói solução inicial
  gl_solution = {}
  gl_solution["team"] = construct_initial_solution(villains_team, budget, villains, heroes, collaboration)
  gl_solution["collaboration_level"] = collaboration_level(collaboration, gl_solution["team"], villains_team) # Melhor solução global
  gl_last_improvement = 0 # Iterações desde a última melhoria
  tabu_list = [] #lista tabu
  while gl_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:


    neighboor_solutions = []
    initial_heroes_team = gl_solution["team"].loc[-gl_solution["team"]["Character ID"].isin(tabu_list)]
    while len(neighboor_solutions) < max_candidates:
      neighboor_solution = {}
      neighboor_solution["team"] = construct_solution(initial_heroes_team, tabu_list, villains_team, budget, villains, heroes, collaboration)
      neighboor_solution["collaboration_level"] = collaboration_level(collaboration, neighboor_solution["team"], villains_team)
      neighboor_solutions.append(neighboor_solution)

    neighboor_solutions.sort(key=lambda c: c["collaboration_level"], reverse=True)
    best_candiate = neighboor_solutions[0]

    if best_candiate["collaboration_level"] > gl_solution["collaboration_level"]:
      gl_solution = best_candiate
      gl_last_improvement = 0
      best_candiate["team"].sort(key=lambda c: c["collaboration_level"], reverse=True)
      for hero in best_candiate["team"]:
        if len(tabu_list) >= max_tabu:
          tabu_list.pop(0)

        tabu_list.append(hero)
    else:
      gl_last_improvement += 1

  return gl_solution["team"]


def main():
  villains_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")


  df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
  villains = df.loc[df['Hero or Villain'] == 'villain']
  heroes = df.loc[df['Hero or Villain'] == 'hero']

  collaboration = pd.read_csv(config.SHARED_COMICS_CSV, sep=';')

  villains_team = df.loc[df["Character ID"].isin(villains_ids)]
  budget = calculate_budget(villains, heroes, villains_team)

  max_tabu = math.floor(len(villains_team))/2
  max_candidates = len(villains_team)
  heroes_team = tabu_search(villains, heroes, villains_team, collaboration, budget, max_tabu, max_candidates)

  print "Villains team:"
  print villains_team["Character Name"]

  print "Heroes team:"
  print heroes_team["Character Name"]

  cl = collaboration_level(collaboration, heroes_team, villains_team)
  print "collaboration_level:"
  print cl

main()
