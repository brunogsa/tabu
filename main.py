# -*- coding: utf-8 -*-
import sys
import config
import numpy as np
import pandas as pd

villians_ids = np.fromfile(sys.argv[1], dtype=int, sep=" ")

df = pd.read_csv(config.CHARACTERS_CSV, sep=';')
vilians = df.loc[df["Character ID"].isin(villians_ids)]
#heroes = df.loc[df['Hero or Villain'] == 'hero']
print vilians["Character Name"]
