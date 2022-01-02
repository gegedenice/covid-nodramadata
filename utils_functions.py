#!/usr/bin/env python
# -*- coding: utf-8 -*-

###-----SOME UTILS FUNCTIONS---###
def remove_cols(df,list_cols_numbers):
    d = df.drop([df.columns[int(i)] for i in list_cols_numbers], axis=1)
    return d

def change_cols_type(df):
    for c in [i for i in list(df.columns) if (i != 'reg') & (i != 'annee')]:
        df[c] = df[c].astype(str).str.replace(' ','').astype(int) 
    df["reg"] = df["reg"].astype(str)
    return df

def calcul_rate(df,new_col,denominateur_col,numerateur_col):
    df.loc[df[denominateur_col] == 0.0, new_col] = 0
    df.loc[df[denominateur_col] != 0.0, new_col] = round((df[numerateur_col]/df[denominateur_col]) *100,1)
    return df