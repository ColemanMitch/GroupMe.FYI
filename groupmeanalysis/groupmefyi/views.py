from django.shortcuts import render
from django.http import HttpResponse
import requests
from groupy.client import Client
from groupy import attachments
import json
import pprint
import datetime
from dateutil import tz
from django.core import serializers
import pandas as pd
import numpy
import datetime as dt
from pandas import DataFrame

#import * from models


def replace_nans_with_dict(series):
    for idx in series[series.isnull()].index:
        series.at[idx] = {}
    return series


pp = pprint.PrettyPrinter(indent=5)


def login(t):
    token = t
    client = Client.from_token(token)
    return client

# Create your views here.

# def timectime(s):
 #   return time.strftime("%A, %B %-d, %Y %-I:%M %p", time.localtime(s))


def index(request):
    return render(request, 'index.html')


def groups(request):

    token = request.GET.get('access_token')
    # client = login(token)
    # print('client = ',client)
    # print('token = ', token)

    url = "https://api.groupme.com/v3/groups?token="+str(token)
    urlData = {'per_page': 500}
    response = requests.get(url, params=urlData)
    res_js = json.loads(response.text)
    group_details = res_js['response']

    try:
        for deserialized_object in serializers.deserialize("json", response.text):
            deserialized_object.save()
    except:
        print('fudge')

    # groups = client.groups.list_all()
    # group_times = [group_details.[]]

    # group_times = [datetime.datetime.fromtimestamp(float(g['messages']['last_message_created_at'])) for g in group_details]
    for g in range(0, len(group_details)):
        group_details[g]['messages']['last_message_created_at'] = datetime.datetime.fromtimestamp(
            float(group_details[g]['messages']['last_message_created_at']), tz=tz.tzlocal())

    # print(group_times)
    print(tz.tzlocal())
    pp.pprint(group_details[0])

    return render(request, 'groups.html', {'groups': groups, 'group_details': group_details, 'token': token})


def download_data(request, access_token, group_id, group_name):
    data = request.session.get('data')
    
    df = pd.DataFrame.from_dict(data)

    print(df)
    df.to_csv('test.csv', index=False)
    #print(group_data_df)
    
    return HttpResponse(data)

def analyze(request, access_token, group_id, group_name):
    any_mentions = False
    any_self_likes = False

    url = "https://api.groupme.com/v3/groups/" + \
        str(group_id)+"/messages?token=" + \
            str(access_token)  # 9429f5a055c30138f03c768570a6045f"
    urlData = {'limit': 100}
    print(url)
    response = requests.get(url, params=urlData)
    res_js = None
    messages = None

    print(group_name)

    df = pd.DataFrame([])

    try:
        while response.status_code != 304:
            response = requests.get(url, params=urlData)
            res_js = json.loads(response.text)
            messages = res_js['response']['messages']
            df = df.append(pd.DataFrame(res_js['response']['messages']), ignore_index=True)
            urlData['before_id'] = str(messages[-1]['id'])

    except:
        # json_formatted_str = json.dumps(res_js, indent=5)
        print("Done")
        
    """ for col in df.columns: 
       print(col) """

    # Some groups have negative created_at values which mess up errthing 
    df = df[df['created_at'] >= 0] 

    df_users = df.groupby(['user_id'], as_index=False).first()[['name','user_id', 'avatar_url']]

    df['num_likes'] = df['favorited_by'].apply(len)
    df['timestamp'] = df['created_at'].apply(dt.datetime.fromtimestamp)
    print(df)        



    df['self_like'] = df.apply(lambda x: 1 if x.user_id in x.favorited_by else 0, axis = 1)
    any_self_likes =  True if df['self_like'].sum() > 0 else False
    
    
    """print('Total Messages: ', len(df))
    print('User Messages: ', len(df[df['sender_type'] == 'user']))
    print('Total Likes: ', df['num_likes'].sum())
    print('Average Likes / User Message: ', df[df['sender_type'] == 'user']['num_likes'].sum()/(len(df[df['sender_type'] == 'user'])))
    print('Most Liked Message: ', df['num_likes'].max(), ' likes') 
    print('\n')"""
    

    
    
    ## build in logic abt no mentions/self likes etc.
    max_likes = int(df['num_likes'].max())


    if max_likes > 0:
        most_liked_msgs = df[df['num_likes'] == max_likes]
        most_liked_msgs.drop(most_liked_msgs.columns.difference(['name','text','attachments', 'timestamp']), 1, inplace=True)
        most_liked_msgs_array = most_liked_msgs.T.to_dict().values()
        print(most_liked_msgs)
        for index, row in most_liked_msgs.iterrows():
            print(index, row['text'], row['attachments'], row['name'], row['timestamp'])
    else: 
        most_liked_msgs_array = []

    
    df = df.explode('attachments')
    if df['attachments'].isna().any():
        df['attachements'] = replace_nans_with_dict(df['attachments'])
    
    df['mentioned'] = [val['user_ids'] if val and val['type'] == 'mentions' else [] for val in df['attachments']]
    df['num_mentions'] = df['mentioned'].apply(len)
    any_mentions =  True if df['num_mentions'].sum() > 0 else False


    df['url'] = [val['url'] if val and val['type'] in ('video', 'image') else '' for val in df['attachments']]

    if any_self_likes:
        print('Self Likes by User ID')
        print(df.groupby('user_id')['self_like'].sum(),'\n') # number of self likes by user_id
    print('Messages by User ID')
    print(df.groupby('user_id')['user_id'].count()[0], '\n') # number of messages by user_id
    if any_mentions:
        print('Times Mentioning Others by User ID')
        print(df.groupby('user_id')['num_mentions'].sum(),'\n') # number of times mentioning by user_id
        print('Times Mentioned')
        print(pd.DataFrame(df['mentioned'].values.tolist()).stack().value_counts(), '\n')    
    print('Likes Given')
    if max_likes > 0:
        print(pd.DataFrame(df['favorited_by'].values.tolist()).stack().value_counts(), '\n')
        print('Likes Received')
        print(df.groupby('user_id')['num_likes'].sum(),'\n') # number of likes received by user_id
        
    if any_mentions:
        df_mentioned = pd.DataFrame(df['mentioned'].values.tolist()).stack().value_counts()

    if max_likes > 0:
        df_likes_given = pd.DataFrame(df['favorited_by'].values.tolist()).stack().value_counts()
    else:
        df_likes_given = 0

    most_talkative = {'user_name': df_users.loc[df_users['user_id'] == df.groupby('user_id')['text'].count().nlargest(1).index[0]].name.iloc[0],
        'num_messages': df.groupby('user_id')['user_id'].count().nlargest(1).iloc[0],
        'avatar_url': df_users.loc[df_users['user_id'] == df.groupby('user_id')['text'].count().nlargest(1).index[0]].avatar_url.iloc[0]}

    if max_likes > 0:
        most_beloved = {'user_name': df_users.loc[df_users['user_id'] == df.groupby('user_id')['num_likes'].sum().nlargest(1).index[0]].name.iloc[0],
            'num_likes': df.groupby('user_id')['num_likes'].sum().nlargest(1).iloc[0],
            'avatar_url': df_users.loc[df_users['user_id'] == df.groupby('user_id')['num_likes'].sum().nlargest(1).index[0]].avatar_url.iloc[0]}
        
        best_ratio = {'user_name': df_users.loc[df_users['user_id'] == df.groupby('user_id')['num_likes'].mean().nlargest(1).index[0]].name.iloc[0],
            'ratio': df.groupby('user_id')['num_likes'].mean().nlargest(1).iloc[0],
            'avatar_url': df_users.loc[df_users['user_id'] == df.groupby('user_id')['num_likes'].mean().nlargest(1).index[0]].avatar_url.iloc[0]}
    else:
        most_beloved = {'user_name': 'No one', 'num_likes': 0, 'avatar_url': ''}
        best_ratio = {'user_name': 'No one', 'ratio': 0, 'avatar_url': ''}



    if any_self_likes:
        self_promoter = {'user_name': df_users.loc[df_users['user_id'] == df.groupby('user_id')['self_like'].sum().nlargest(1).index[0]].name.iloc[0],
        'self_likes': df.groupby('user_id')['self_like'].sum().nlargest(1).iloc[0],
        'avatar_url': df_users.loc[df_users['user_id'] == df.groupby('user_id')['self_like'].sum().nlargest(1).index[0]].avatar_url.iloc[0]}
    else:
        self_promoter = {'user_name': '', 'self_likes': 0, 'avatar_url': ''}

    if any_mentions:
        most_mentioned = {'user_name': df_users.loc[df_users['user_id'] == df_mentioned.nlargest(1).index[0]].name.iloc[0],
        'times_mentioned': df_mentioned.nlargest(1).iloc[0],
        'avatar_url': df_users.loc[df_users['user_id'] == df_mentioned.nlargest(1).index[0]].avatar_url.iloc[0]}
    else:
        most_mentioned = {'user_name': '', 'times_mentioned': 0, 'avatar_url': ''}

    if max_likes > 0:
        most_likes_given = {'user_name': df_users.loc[df_users['user_id'] == df_likes_given.nlargest(1).index[0]].name.iloc[0],
        'likes_given': df_likes_given.nlargest(1).iloc[0],
        'avatar_url': df_users.loc[df_users['user_id'] == df_likes_given.nlargest(1).index[0]].avatar_url.iloc[0]}
    else:
        print('max_likes', max_likes)
        most_likes_given = {'user_name': '', 'likes_given': 0, 'avatar_url': ''}
        
    
    date_created = df['timestamp'].min()
    
    del df['system']
    del df['timestamp']
   


    d = df.to_dict(orient='records')
    j = json.dumps(d, default=str)   
    
    print(df)

    

    request.session['data'] = d

    #if any_self_likes and any_mentions:
    return render(request, 'analyze.html', 
            {'group_name':group_name, 
            'total_messages': len(df),
            'total_user_messages': len(df[df['sender_type'] == 'user']),
            'total_likes': df['num_likes'].sum(),
            'avg_likes_user_comment': df[df['sender_type'] == 'user']['num_likes'].sum()/(len(df[df['sender_type'] == 'user'])),
            'date_created': date_created,
            'total_self_likes': df['self_like'].sum(),
            'total_mentions':df['num_mentions'].sum(),
            'most_likes_message_cnt': len(df[df['num_likes'] == df['num_likes'].max()]),
            'most_likes_message':df['num_likes'].max(),
            'most_talkative': most_talkative,
            'most_beloved': most_beloved,
            'best_ratio': best_ratio,
            'self_promoter': self_promoter,
            'most_likes_given':most_likes_given,
            'most_mentioned': most_mentioned,
            'most_liked_msgs_array': most_liked_msgs_array,
            'res_js': res_js,
            'j': j
            })


