# -*- coding: utf-8 -*-
import pandas as pd

df = pd.read_csv('data/marvel_characters.csv', sep=';')
heroes = df.loc[df['Hero or Villain'] == 'hero']
print heroes
