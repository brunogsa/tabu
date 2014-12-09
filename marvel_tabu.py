# -*- coding: utf-8 -*-
import config
import cPickle
import pandas as pd
import random

MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 100
CHARACTER_ID = "Character ID"
POWERGRID = ["Intelligence", "Strength", "Speed", "Durability", "Energy Projection", "Fighting Skills"]
POPULARITY = "Number of Comic Books Where Character Appeared"

class MarvelTabu:
  def __init__(self, villains_ids, tabu_size, with_budget):
    self.with_budget = with_budget
    self.collaboration = cPickle.load(open('data/colaboracao.pickle', 'rb'))
    self.collaboration_coo = self.collaboration.tocoo()
    self.collaboration_csc = self.collaboration.tocsc()
    df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
    self.villains = df.loc[df['Hero or Villain'] == 'villain']
    self.heroes = df.loc[df['Hero or Villain'] == 'hero']
    self.villains_team = self.villains.loc[self.villains[CHARACTER_ID].isin(villains_ids)]
    self.tabu_size = tabu_size
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

    # Constrói solução inicial
    gl_solution = {}
    gl_solution["team"] = self.construct_initial_solution()
    gl_solution["collaboration_level"] = self.collaboration_level(gl_solution["team"])

    gl_last_improvement = 0 # Iterações desde a última melhoria
    tabu_list = [] #lista tabu

    while gl_last_improvement < MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
      neighboor_solutions = []
      # Usa como time inicial de herois para montar as solucoes vizinhas
      # Remove todos que já estão na lista tabu
      initial_heroes_team = gl_solution["team"].loc[-gl_solution["team"][CHARACTER_ID].isin(tabu_list)]
      # Controi uma lista de vizinhos até o limite maximo de candidatos possiveis
      self.exclusion_list = []
      self.exclusion_list += tabu_list
      while len(neighboor_solutions) < len(self.villains_team):
        neighboor_solution = {}
        neighboor_solution["team"] = self.construct_solution(initial_heroes_team)
        neighboor_solution["collaboration_level"] = self.collaboration_level(neighboor_solution["team"])
        neighboor_solutions.append(neighboor_solution)
        # exclui todos os que ja foram escolhidos como solucao vizinha
        self.exclusion_list += list(set(neighboor_solution["team"][CHARACTER_ID].values) - set(self.exclusion_list))
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
          if len(tabu_list) >= self.tabu_size:
            tabu_list.pop(0)
          tabu_list.append(hero)
      else:
        gl_last_improvement += 1

    return gl_solution


  # constroe a solucao inicial
  def construct_initial_solution(self):
    # monta um time em branco como inicial
    # deixa a lista de exclusao em branco
    initial_heroes_team = pd.DataFrame(columns=self.heroes.columns.values)
    return self.construct_solution(initial_heroes_team)

  # Responsavel por escolher solucoes viaveis
  def construct_solution(self, initial_heroes_team):
    greed_tabu = []
    # inicializa o time com os herois iniciais
    heroes_team = initial_heroes_team
    # obter os herois para a solucao inicial
    if len(heroes_team) == 0:
      # obtem um par de herois que tem a colaboracao maxima
      # Usar sparse COOrdinate matrix
      max_colab = self.collaboration_coo.data.argmax()
      heroes_team = self.heroes.loc[self.heroes[CHARACTER_ID].isin([self.collaboration_coo.row[max_colab]]) | self.heroes[CHARACTER_ID].isin([self.collaboration_coo.col[max_colab]])]
      # coloca na lista de exclusao somente o ultimo heroi excolhido (o outro vai ser removido caso nao encontre uma solucao viavel)
      greed_tabu.append(heroes_team[1:2][CHARACTER_ID].values[0])
    
	# enquanto nao encontrar uma solucao viavel, continua procurando
    while not self.is_viable_solution(heroes_team):
      # remove o primeiro heroi da lista caso nao for solucao viavel
      first_hero = heroes_team[0:1][CHARACTER_ID].values[0]
      if not first_hero in greed_tabu:
        greed_tabu.append(first_hero)
		
      heroes_team = heroes_team[1:]
      # enquanto nao tiver o tamanho maximo de time
      while len(heroes_team) < len(self.villains_team):
        # condicao de parada para solucao inviavel
        if len(heroes_team) + len(greed_tabu) > len(self.heroes):
          return None
        # escolhe randomicamente dentre os herois já no time
        # pega o herois que tem maior nivel de colaboração com esse heroi escolhido
        # (já está sendo considerado remover os viloes e a lista de esclusão
        # adiciona no time de heroi
        random_hero = heroes_team.loc[random.sample(heroes_team.index, 1)]
        # Usar sparse COOrdinate matrix
        collaborators = self.collaboration[:,random_hero[CHARACTER_ID].values[0]]
        collaborators[greed_tabu,:] = 0
        collaborators[self.villains[CHARACTER_ID],:] = 0

        coordinate_collaboration = collaborators.tocoo()
        max_colab = coordinate_collaboration.data.argmax()

        hero_max_collaboration_level = self.heroes.loc[self.heroes[CHARACTER_ID].isin([coordinate_collaboration.row[max_colab]])]
        heroes_team = heroes_team.append(hero_max_collaboration_level)
        # adiciona o heroi escolhido na lista de exclusao
        greed_tabu.append(hero_max_collaboration_level[CHARACTER_ID].values[0])
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
    heroes_team_pop = heroes_team[POPULARITY].values
    # Multiplica powergrid médio e popularidade e soma os resultados para obter custo
    heroes_cost = (heroes_team_pg*heroes_team_pop).sum()
    # Não é solução viável se o custo do time de heróis é maior que o orçamento
    if self.with_budget and heroes_cost > self.budget(): return False
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
