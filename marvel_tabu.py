# -*- coding: utf-8 -*-
import config
import cPickle
import numpy as np
from operator import itemgetter
import pandas as pd
import random

MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 10
CHARACTER_ID = "Character ID"
POWERGRID = ["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]
POPULARITY = "Number of Comic Books Where Character Appeared"

class MarvelTabu:
  def __init__(self, villains_ids, with_budget):
    self.with_budget = with_budget
    self.collaboration = cPickle.load(open('data/colaboracao.pickle', 'rb'))
    self.collaboration_all_csc = cPickle.load(open('data/colaboracao_all.pickle', 'rb')).tocsc()
    self.collaboration_coo = self.collaboration.tocoo()
    self.collaboration_csc = self.collaboration.tocsc()
    df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
    self.villains_ids = villains_ids
    self.villains = df.loc[df['Hero or Villain'] == 'villain']
    self.heroes = df.loc[df['Hero or Villain'] == 'hero']
    self.villains_team = self.villains.loc[self.villains[CHARACTER_ID].isin(villains_ids)]
    self.tabu_size = len(self.heroes) - (len(self.heroes) / len(self.villains_team))
    self.budget_calc = None


  # Algoritmo de tabu search
  def tabu_search(self):
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

    self.tabu_list = [] #lista tabu

    # Constrói solução inicial
    gl_solution = {}
    initial_team = self.construct_initial_solution()
    if not self.is_viable_solution(initial_team):
      initial_team = self.construct_solution(initial_team)
    gl_solution["team"] = initial_team
    gl_solution["collaboration_level"] = self.collaboration_level(initial_team)

    gl_last_improvement = 0 # Iterações desde a última melhoria
    neighboors_amount = (len(self.heroes) / len(self.villains_team) / 4)

    while gl_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
      neighboor_solutions = []
      # Controi uma lista de vizinhos até o limite maximo de candidatos possiveis
      while len(neighboor_solutions) < neighboors_amount:
        neighboor_solution = {}
        neighboor_solution["team"] = self.construct_solution(gl_solution["team"])
        neighboor_solution["collaboration_level"] = self.collaboration_level(neighboor_solution["team"])
        neighboor_solutions.append(neighboor_solution)
      # Ordena em order descrescente as solucoes candidatas a melhores
      # Pega a melhor solucao encontrada
      best_candiate = sorted(neighboor_solutions, key=itemgetter('collaboration_level'), reverse=True)[0]
      #best_candiate = neighboor_solutions.sort(key=lambda c: c["collaboration_level"], reverse=True)[0]
      # substitui a solucao global pela solucao encontrada atoe o momento
      if best_candiate["collaboration_level"] > gl_solution["collaboration_level"]:
        gl_solution = best_candiate
        gl_last_improvement = 0
      else:
        gl_last_improvement += 1
    gl_solution["collaboration_level"] = self.score(gl_solution["team"])
    return gl_solution

  # Adiciona um heroi a lista tabu
  # Se a lista estiver cheia remove o ultimo adicionado
  # Fila FIFO
  def add_hero_to_tabu(self, hero):
    if len(self.tabu_list) >= self.tabu_size:
      self.tabu_list.pop(0)
    self.tabu_list.append(hero)

  # constroe a solucao inicial
  # Seja N a quantidade de viloes
  # Aqui a gente cria uma equipe de N herois
  # pegando pares que maximizam a colaboracao
  # Usar sparse COOrdinate matrix
  def construct_initial_solution(self):
    ind = np.argpartition(self.collaboration_coo.data, -len(self.villains_team))[-len(self.villains_team):]
    inc = 1
    while len(np.unique(self.collaboration_coo.row[ind])) < len(self.villains_team):
      ind = np.argpartition(self.collaboration_coo.data, -(len(self.villains_team) + inc))[-(len(self.villains_team) + inc):]
      inc += 1
    heroes_team = self.heroes.loc[self.heroes[CHARACTER_ID].isin(self.collaboration_coo.row[ind])]
    return heroes_team

  # Responsavel por escolher solucoes viaveis
  def construct_solution(self, initial_heroes_team):
    # inicializa o time com os herois iniciais
    heroes_team = initial_heroes_team
    tries = 0
    # enquanto nao encontrar uma solucao viavel, continua procurando
    while not self.is_viable_solution(heroes_team):
      tries += 1
      # remover heroi aleatorio
      random_hero = heroes_team.loc[random.sample(heroes_team.index, 1)]
      heroes_team = heroes_team[heroes_team[CHARACTER_ID] != random_hero[CHARACTER_ID].values[0]]
      self.add_hero_to_tabu(random_hero[CHARACTER_ID].values[0])

      collaborators = self.collaboration[heroes_team[CHARACTER_ID].values,:]
      collaborators[:,self.tabu_list] = 0
      collaborators[:,heroes_team[CHARACTER_ID].values] = 0
      coo_colabs = collaborators.tocoo()
      if len(coo_colabs.data) != 0:
        heroes_team = heroes_team.append(self.heroes.loc[self.heroes[CHARACTER_ID].isin([coo_colabs.col[coo_colabs.data.argmax()]])])

      if not self.is_viable_solution(heroes_team) and tries > (len(self.heroes) / len(self.villains_team)):
        random_hero = heroes_team.loc[random.sample(heroes_team.index, 1)]
        heroes_team = heroes_team[heroes_team[CHARACTER_ID] != random_hero[CHARACTER_ID].values[0]]
        self.add_hero_to_tabu(random_hero[CHARACTER_ID].values[0])
        tries = 0
    return heroes_team

  # Verifica se uma solução é viável dados um time de vilões,
  # um time de heróis e um orçamento disponível
  def is_viable_solution(self, heroes_team):
    # Não é solução viável se o time de heróis é MAIOR que o de vilões
    if len(heroes_team) > len(self.villains_team): return False

    # CALCULAR CUSTO DO TIME
    # CUSTO: SUM(Popularidade[h]*PowegridMedio[h]) para cada herói h

    # Para cada herói, calcula a média de suas hablidades (powergrid médio)
    heroes_team_pg = heroes_team[POWERGRID].mean(1).values
    # Para cada herói, seleciona sua popularidade
    if self.with_budget:
      heroes_team_pop = heroes_team[POPULARITY].values
      # Multiplica powergrid médio e popularidade e soma os resultados para obter custo
      heroes_cost = (heroes_team_pg*heroes_team_pop).sum()
      # Não é solução viável se o custo do time de heróis é maior que o orçamento
      if heroes_cost > self.budget():
        return False
    # Para cada vilão, calcula a média de suas hablidades (powergrid médio)
    villains_team_pg = self.villains_team[POWERGRID].mean(1).values
    # Não é solução viável se a média das habilidades dos vilões é MAIOR que a média dos heróis
    if villains_team_pg.mean() > heroes_team_pg.mean(): return False

    return True

  # Calcula a colaboracao entre os herois
  # Soma a matriz triangular superior da submatriz
  # de colaboracao entre os herois do time candidato
  def collaboration_level(self, heroes_team):
    heroes_ids = heroes_team[CHARACTER_ID].values
    c_level = 0
    for i in range(len(heroes_ids)-1):
      c_level += self.collaboration_csc[heroes_ids[i], heroes_ids[i+1:]].sum()
    return c_level

  def score(self, heroes_team):
    heroes_ids = heroes_team[CHARACTER_ID].values
    score = self.collaboration_level(heroes_team)
    for i in heroes_ids:
      score += self.collaboration_all_csc[i, self.villains_ids].sum()
    return score;

  def budget(self):
    if self.budget_calc == None:
      # Exp 1
      heroes_pg = self.heroes[POWERGRID].mean(1).values.mean()
      villains_team_pg = self.villains_team[POWERGRID].mean(1).values.mean()
      ratio_pg = heroes_pg/villains_team_pg

      heroes_pop = self.heroes[POPULARITY].mean()
      villains_team_pop = self.villains_team[POPULARITY].mean()
      ratio_pop = heroes_pop/villains_team_pop

      villains_team_pg = self.villains_team[POWERGRID].mean(1).values
      villains_team_pop = self.villains_team[POPULARITY].values
      vt_cost = (villains_team_pg*villains_team_pop).sum()

      exp1 = ratio_pg*ratio_pop*vt_cost

      # Exp 2
      villains_pg = self.villains[POWERGRID].mean(1).values.mean()
      factor = villains_team_pg.mean()/villains_pg

      exp2 = factor*heroes_pg*heroes_pop*len(self.villains_team)

      self.budget_calc = max(exp1, exp2)
    return self.budget_calc
