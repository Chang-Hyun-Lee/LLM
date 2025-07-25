import streamlit as st
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
import seaborn as sns

st.title('Titanic dataset 분석')

df = sns.load_dataset('titanic')

g = sns.barplot(x='sex', y='survived', data=df)
st.pyplot(g.get_figure())

g = sns.barplot(x='sex', y='fare', data=df)
st.pyplot(g.get_figure())

g =sns.barplot(x='sex', y='survived', hue = 'class', data=df)
st.pyplot(g.get_figure())

g = sns.barplot(x='sex', y='survived', hue = 'class', order = ['female', 'male'], data=df)
st.pyplot(g.get_figure())

g = sns.barplot(x='sex', y='survived', hue = 'class', order = ['female', 'male'], estimator = sum, data=df)
st.pyplot(g.get_figure())

g = sns.barplot(x='sex', y='survived', hue = 'class', order = ['female', 'male'], palette="Blues_d", data=df)
st.pyplot(g.get_figure())

g = sns.barplot(x = 'sex', y = 'survived', hue = 'class', data = df)
g.set(xlabel='Gender', ylabel='Survival Rate')
st.pyplot(g.get_figure())

g = sns.barplot(x = 'sex', y = 'survived', hue = 'class', data = df)
g.set_title("Gender vs Survival Rate in Males and Females") 
st.pyplot(g.get_figure())

g = sns.violinplot(x ="sex", y ="age", hue ="survived", data = df, split = True)
st.pyplot(g.get_figure())
