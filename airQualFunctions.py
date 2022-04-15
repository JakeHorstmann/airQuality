import os
from google.cloud import bigquery
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from pandas.core.common import SettingWithCopyWarning
import matplotlib.colors as mcolors

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# convert dates to times assuming 365 days in a year and 30.4167 days per month

def dateToTime(frame, refYear):
    refYear = int(refYear)
    daysInYear = 365
    daysInMonth = daysInYear/12
    
    splitDates = frame.date_local.apply(lambda x: x.split('-'))
    days = splitDates.apply(lambda x: (int(x[0]) - refYear)*daysInYear + (int(x[1])-1)*daysInMonth + int(x[2]))
    frame['days'] = days

    
    
# set plot colors

def CountyColors(frame, colors = mcolors.CSS4_COLORS):
    cmap = {}
    goodColors = []
    for color in colors:
        if ('white' in color) or ('White' in color) or ('Black' in color):
            pass
        else:
            goodColors.append(color)
    i = 0
    goodColors.reverse()
    for county in frame.county_name.value_counts().index:
        cmap[county] = goodColors[i]
        i += 1
    frame['colors'] = frame.county_name.map(cmap)
    

# convert full file into just data from a state

def StateData(frame, stateName, fileName):
    df1 = frame.loc[frame['state_name'] == stateName]
    firstYear = df1.sort_values(by = 'date_local', ascending = True).date_local.iloc[0].split('-')[0]
    dateToTime(df1, firstYear)
    CountyColors(df1)
    df1.to_csv(fileName + '.csv', index_label = False)
    
def PlotByCounty(frame, ymax = 250):
    # fit a line to all the data
    m, b = np.polyfit(frame.days, frame.aqi, 1)
    lineLabel = 'm = ' + str(round(m,4)) + ', b = ' + str(round(b,2))
    
    # plot all counties together
    plt.figure(figsize =(20,10))
    plt.scatter(frame['days'], frame['aqi'], c = frame['colors'])
    plt.plot([frame.days.min(), frame.days.max()], [m*frame.days.min() + b, m*frame.days.max() + b], c = 'k', label = lineLabel)
    plt.legend()
    plt.ylim(0,ymax)
    
    # try to pick a smart subplot design 

    if (frame.county_name.value_counts().shape[0] % 3 == 0):
        column = 3
        row = frame.county_name.value_counts().shape[0] / 3
        fig, ax = plt.subplots(int(row), int(column), figsize = (20,20))
    elif (frame.county_name.value_counts().shape[0] % 2 == 0):
        column = 2
        row = frame.county_name.value_counts().shape[0] / 2
        fig, ax = plt.subplots(int(row), int(column), figsize = (20,40))
    else:
        column = 1
        row = frame.county_name.value_counts().shape[0]
        fig, ax = plt.subplots(int(row), int(column), figsize = (20,20))
        
    # plot points based on county
    
    i = 0
    for county in frame.county_name.value_counts().index:
        j = i // column
        k = i % column
        data = frame.loc[frame['county_name'] == county]
        ax[j][k].scatter(data['days'], data['aqi'], c = data['colors'], label = county)
        ax[j][k].set_ylim(0, ymax)

        # fit a line EXCLUDING very high points
        
        filData = data.loc[data['aqi'] < 250]
        m, b = np.polyfit(filData.days, filData.aqi, 1)
        lineLabel = 'm = ' + str(round(m,4)) + ', b = ' + str(round(b,2))
        if m < 0:
            ax[j][k].plot([filData.days.min(), filData.days.max()], [m*filData.days.min() + b, m*filData.days.max() + b], c = 'k', label = lineLabel)
        else:
            ax[j][k].plot([filData.days.min(), filData.days.max()], [m*filData.days.min() + b, m*filData.days.max() + b], c = 'k', linestyle = '--', label = lineLabel)
        ax[j][k].legend()

        i += 1
    fig.tight_layout()