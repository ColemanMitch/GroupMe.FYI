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
import datetime as dt
from datetime import timezone
import time
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, url_for, copy_current_request_context,request
from login import login
from analyze_group import *
import seaborn as sns
from io import StringIO
import dateutil.parser
import base64
import babel
import os


#

app = Flask(__name__)



@app.route('/')
def base():
    return render_template('index.html')

@app.template_filter('ctime')
def timectime(s):
    return time.strftime("%A, %B %-d, %Y %-I:%M %p", time.localtime(s))

@app.template_filter()
def numberFormat(value):
    return format(int(value), ',d')

@app.route('/groups_list')
def list_groups():
    token = request.args.get('access_token')
    client = login(token)

    print('client = ',client)
    print('token = ', token)

    url = "https://api.groupme.com/v3/groups?token="+str(token)
    urlData = {'per_page':500}
    response = requests.get(url, params=urlData)
    res_js = json.loads(response.text)
    group_details = res_js['response']

    #print(group_details)

    groups = client.groups.list_all()
    group_id = ''
    return render_template('group_list.html', groups = groups,
                                        group_details = group_details,
                                        token = token)

@app.route('/analyze')
def analyze():
    token = request.args.get('token')
    client = login(token)
    group_id = request.args.get('group_id')
    group_name = request.args.get('group_name')

    #df_group = pd.DataFrame()
    df_group, all_users_df = scrape_messages(group_id, token)

    print(df_group)
    #<center><img src={{ best_msg.attachments[0].url }}><center>
    print(all_users_df)
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




    total_group_stats_dict, superlative_members, likes_matrix = total_group_stats(df_group, all_users_df)

    #img = io.BytesIO()
    #sns.set_style(xlabel='Likes Given', ylabel='Likes Recieved')
    plt.figure(figsize=(25, 25))

    with sns.plotting_context(font_scale=5):
        ax = sns.heatmap(likes_matrix, annot=True, fmt='d', cmap="YlGnBu")
    #ax.set(xlabel='Likes Given', ylabel='Likes Recieved')
    ax.set_xlabel('Likes Given',fontsize=20);
    ax.set_ylabel('Likes Received',fontsize=20)
    #plt.show()
    #st = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


    ts = dt.datetime.now()

    utc_time = ts.replace(tzinfo = timezone.utc)
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



#
