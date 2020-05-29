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
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, url_for, copy_current_request_context,request
from login import login
from analyze_group import *

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
    return render_template('base.html', groups = groups, token = token)

@app.route('/analyze')
def analyze():
    token = request.args.get('token')
    client = login(token)
    group_id = request.args.get('group_id')
    group_name = request.args.get('group_name')

    

    #df_group = pd.DataFrame()
    df_group = scrape_messages(group_id, token)

    print(df_group)
    #<center><img src={{ best_msg.attachments[0].url }}><center>


    # best comment
    best_msg_dict = best_msg(df_group)
    best_msg_attchmnt = False
    if best_msg_dict['attachments']:
        print('there is an attachment')
        best_msg_attchmnt = True



    total_group_stats_dict = total_group_stats(df_group)
    print(total_group_stats_dict)

    return render_template('analysis.html', group_name=group_name,
                                            best_msg=best_msg_dict,
                                            best_msg_attchmnt=best_msg_attchmnt,
                                            group_stats=total_group_stats_dict)


if __name__ == "__main__":
    app.run(debug=True)
#
