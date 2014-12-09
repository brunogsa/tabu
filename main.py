# -*- coding: utf-8 -*-
import os
import sys
import config
import math
import random
import numpy as np
import pandas as pd
import cPickle

MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 100
POWERGRID = ["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]
POPULARITY = "Number of Comic Books Where Character Appeared"
COLLABORATION_LEVEL = "Number of Comic Books Where Character 1 and Character 2 Both Appeared"
CHARACTER_ID = "Character ID"

collaboration = cPickle.load(open('data/colaboracao.pickle', 'rb'))
collaboration_coo = collaboration.tocoo()
collaboration_csc = collaboration.tocsc()

# Responsavel por escolher solucoes viaveis
def construct_solution(initial_heroes_team, exclusion_list, villains, heroes, villains_team, budget):
  # tamanho maximo do time de herois
  team_max_size = len(villains_team)

  # inicializa o time com os herois iniciais
  heroes_team = initial_heroes_team

  # obter os herois para a solucao inicial

  if len(heroes_team) == 0:
    # obtem um par de herois que tem a colaboracao maxima
    # Usar sparse COOrdinate matrix
    max_colab = collaboration_coo.data.argmax()
    heroes_team = heroes.loc[heroes[CHARACTER_ID].isin([collaboration_coo.row[max_colab]]) | heroes[CHARACTER_ID].isin([collaboration_coo.col[max_colab]])]
    # coloca na lista de exclusao somente o ultimo heroi excolhido (o outro vai ser removido caso nao encontre uma solucao viavel)
    exclusion_list.append(heroes_team[1:2][CHARACTER_ID].values[0])

  # enquanto nao encontrar uma solucao viavel, continua procurando
  while not is_viable_solution(villains_team, heroes_team, budget):
    # remove o primeiro heroi da lista caso nao for solucao viavel
    exclusion_list.append(heroes_team[0:1][CHARACTER_ID].values[0])
    heroes_team = heroes_team[1:]

    # enquanto nao tiver o tamanho maximo de time
    while len(heroes_team) < team_max_size:
      # condicao de parada para solucao inviavel
      if len(heroes_team) + len(exclusion_list) > len(heroes):
        return None

      # escolhe randomicamente dentre os herois já no time
      # pega o herois que tem maior nivel de colaboração com esse heroi escolhido
      # (já está sendo considerado remover os viloes e a lista de esclusão
      # adiciona no time de heroi
      random_hero = heroes_team.loc[random.sample(heroes_team.index, 1)]
      # Usar sparse COOrdinate matrix

      collaborators = collaboration[:,random_hero[CHARACTER_ID].values[0]]
      collaborators[exclusion_list,:] = 0
      collaborators[villains[CHARACTER_ID],:] = 0

      coordinate_collaboration = collaborators.tocoo()
      max_colab = coordinate_collaboration.data.argmax()

      hero_max_collaboration_level = heroes.loc[heroes[CHARACTER_ID].isin([coordinate_collaboration.row[max_colab]])]
      heroes_team = heroes_team.append(hero_max_collaboration_level)

      # adiciona o heroi escolhido na lista de exclusao
      exclusion_list.append(hero_max_collaboration_level[CHARACTER_ID].values[0])

  return heroes_team

# constroe a solucao inicial
def construct_initial_solution(villains, heroes, villains_team, budget):
  # monta um time em branco como inicial
  # deixa a lista de exclusao em branco
  initial_heroes_team = pd.DataFrame(columns=heroes.columns.values)
  exclusion_list = []

  return construct_solution(initial_heroes_team, exclusion_list, villains, heroes, villains_team, budget)
  
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
  if os.environ.get('WITH_BUDGET') != None and heroes_cost > budget: return False

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

# Calcula o nivel de colaboracao obtido de acordo com os times
def collaboration_level(heroes_team, villains_team):
  heroes_ids = heroes_team[CHARACTER_ID].values
  c_level = 0
  for i in range(len(heroes_ids)-1):
    c_level += collaboration_csc[heroes_ids[i], heroes_ids[i+1:]].sum()
  return c_level

# Algoritmo de tabu search
def tabu_search(villains, heroes, villains_team, budget, max_tabu, max_candidates):
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
  gl_solution["team"] = construct_initial_solution(villains, heroes, villains_team, budget)
  gl_solution["collaboration_level"] = collaboration_level(gl_solution["team"], villains_team)

  gl_last_improvement = 0 # Iterações desde a última melhoria
  tabu_list = [] #lista tabu

  while gl_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
    neighboor_solutions = []

    # Usa como time inicial de herois para montar as solucoes vizinhas
    # Remove todos que já estão na lista tabu
    initial_heroes_team = gl_solution["team"].loc[-gl_solution["team"][CHARACTER_ID].isin(tabu_list)]

    # Controi uma lista de vizinhos até o limite maximo de candidatos possiveis
    exclusion_list = []
    exclusion_list += tabu_list
    while len(neighboor_solutions) < max_candidates:
      neighboor_solution = {}
      neighboor_solution["team"] = construct_solution(initial_heroes_team, exclusion_list, villains, heroes, villains_team, budget)
      neighboor_solution["collaboration_level"] = collaboration_level(neighboor_solution["team"], villains_team)
      neighboor_solutions.append(neighboor_solution)
      # exclui todos os que ja foram escolhidos como solucao vizinha
      exclusion_list += list(set(neighboor_solution["team"][CHARACTER_ID].values) - set(exclusion_list))

    # Ordena em order descrescente as solucoes candidatas a melhores
    # Pega a melhor solucao encontrada
    neighboor_solutions.sort(key=lambda c: c["collaboration_level"], reverse=True)
    best_candiate = neighboor_solutions[0]

    # substitui a solucao global pela solucao encontrada atoe o momento
    if best_candiate["collaboration_level"] > gl_solution["collaboration_level"]:
      gl_solution = best_candiate
      gl_last_improvement = 0

      # Atualiza a lista tabu
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

  villains_team = villains.loc[villains[CHARACTER_ID].isin(villains_ids)]

  if os.environ.get('WITH_BUDGET') != None:
    budget = calculate_budget(villains, heroes, villains_team)
  else:
    budget = 0

  # Parametros variaveis para o tabu search
  max_tabu = math.floor(len(villains_team))/2
  max_candidates = len(villains_team)

  heroes_team = tabu_search(villains, heroes, villains_team, budget, max_tabu, max_candidates)

  if os.environ.get('DEBUG') != None:
    print "Villains team:"
    print villains_team["Character Name"]

    print "Heroes team:"
    print heroes_team["Character Name"]

  cl = collaboration_level(heroes_team, villains_team)
  if os.environ.get('DEBUG') != None:
    if os.environ.get('WITH_BUDGET') != None:
      print "collaboration_level (with budget):"
    else:
      print "collaboration_level (without budget):"
  print cl

main()
