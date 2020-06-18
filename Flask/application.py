"""
Flask application that controls the playback of a Spotify playlist and dynamically updates a webpage based on the current track using socket.io

 2020

"""

# Start with a basic flask app webpage.
from groupy.client import Client
from groupy import attachments
import requests
import json
import pprint
import pandas as pd
from pandas import DataFrame as df
import datetime
from datetime import timezone
import time
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, url_for, copy_current_request_context,request
from login import login
from analyze_group import *
import seaborn as sns
from io import StringIO
import base64


#

app = Flask(__name__)



@app.route('/')
def base():
    return render_template('index.html')

@app.route('/groups_list')
def list_groups():
    token = request.args.get('access_token')
    client = login(token)

    print('client = ',client)
    print('token = ', token)

    groups = client.groups.list_all()
    group_id = ''
    return render_template('base.html', groups = groups,
                                        token = token)

@app.route('/analyze')
def analyze():
    token = request.args.get('token')
    client = login(token)
    group_id = request.args.get('group_id')
    group_name = request.args.get('group_name')

    #df_group = pd.DataFrame()
    df_group, df_members = scrape_messages(group_id, token)

    print(df_group)
    #<center><img src={{ best_msg.attachments[0].url }}><center>
    print(df_members)
    # best comment
    best_msg_dict = best_msg(df_group)
    best_msg_attchmnt = 0
    if best_msg_dict['attachments']:
        print(best_msg_dict['attachments'])
        best_msg_attchmnt = 1
        if best_msg_dict['attachments'][0]['type'] == 'mentions':
            best_msg_attchmnt = 0
    if best_msg_dict['message'] != None and best_msg_dict['message'][-4:] == '.mp4':
        print('there is an attachment')
        best_msg_dict['attachments'] = [{ 'url': best_msg_dict['message']}]
        best_msg_attchmnt = 2




    total_group_stats_dict, superlative_members, likes_matrix = total_group_stats(df_group, df_members)

    #img = io.BytesIO()
    #sns.set_style(xlabel='Likes Given', ylabel='Likes Recieved')
    plt.figure(figsize=(15, 15))

    with sns.plotting_context(font_scale=5):
        ax = sns.heatmap(likes_matrix, annot=True, fmt='d', cmap="YlGnBu")
    #ax.set(xlabel='Likes Given', ylabel='Likes Recieved')
    ax.set_xlabel('Likes Given',fontsize=20);
    ax.set_ylabel('Likes Received',fontsize=20)
    #plt.show()
    #st = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


    dt = datetime.datetime.now()

    utc_time = dt.replace(tzinfo = timezone.utc)
    utc_timestamp = utc_time.timestamp()

    plot_url = 'static/images/'+str(group_id)+'_'+str(utc_timestamp)+'_plot.png'
    plt.savefig(plot_url)

    print(utc_timestamp)
    print(plot_url)

    #print(st)
    print(total_group_stats_dict)
    print(best_msg_dict)
    print(superlative_members)

    return render_template('analysis.html', group_name=group_name,
                                            best_msg=best_msg_dict,
                                            best_msg_attchmnt=best_msg_attchmnt,
                                            superlative_members=superlative_members,
                                            group_stats=total_group_stats_dict,
                                            plot_url=plot_url)


if __name__ == "__main__":
    plt.switch_backend('Agg')
    app.run(debug=True)
#
