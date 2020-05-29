# analyze_group.py
from groupy.client import Client
import pandas as pd
import requests
import json
import datetime as dt
from login import login


gm_msgs, gm_likes, gm_users, gm_users_id, gm_created_at, gm_favorited_by, gm_attachments = [], [], [], [], [], [], []


def get_group(group_id, client):
    group_to_analyze = client.groups.get(group_id)
    member_list = group_to_analyze.members

    user_ids = []
    nicknames = []

    for member in member_list:
        print(member)
        user_ids.append(member.user_id)
        nicknames.append(member.nickname)

def scrape_messages(group_id, token):

    gm_msgs, gm_likes, gm_users, gm_users_id, gm_created_at, gm_favorited_by, gm_attachments = [], [], [], [], [], [], []


    url = "https://api.groupme.com/v3/groups/"+str(group_id)+"/messages?token="+str(token)#9429f5a055c30138f03c768570a6045f"
    urlData = {'limit':100}
    print(url)
    response = requests.get(url, params=urlData)
    res_js = None
    messages = None

    client = login(token)
    group_members = client.groups.get(group_id).members
    print(group_members)


    try:
      while response.status_code != 304:
        response = requests.get(url, params=urlData)
        res_js = json.loads(response.text)
        messages = res_js['response']['messages']
        urlData['before_id'] = str(messages[-1]['id'])
        for i in range(len(messages)):
          gm_likes.append(len(messages[i]['favorited_by']))
          gm_msgs.append(messages[i]['text'])
          gm_users.append(messages[i]['name'])
          gm_users_id.append(messages[i]['user_id'])
          gm_created_at.append(messages[i]['created_at'])
          gm_favorited_by.append(messages[i]['favorited_by'])
          gm_attachments.append(messages[i]['attachments'])
        #print(json_formatted_str)
    except:
        json_formatted_str = json.dumps(res_js, indent=5)
        df = pd.DataFrame(columns=["User ID", "Nickname","Message", "Attachments","Time Stamp", "Number of Likes", "Liked By"])

        df["Message"]=gm_msgs
        df["Attachments"]= gm_attachments
        df["Number of Likes"]=gm_likes
        df["User ID"] = gm_users_id
        df["Time Stamp"] = gm_created_at
        df["Nickname"] = gm_users
        df["Liked By"] = gm_favorited_by

        for i in range(len(gm_created_at)):
            gm_created_at[i] = dt.datetime.fromtimestamp(gm_created_at[i]).strftime('%c')

        df["Datetime"] = gm_created_at
        print("Done")

        return df


def best_msg(df):
    idx = df.groupby(['User ID'])['Number of Likes'].transform(max) == df['Number of Likes']
    df = df[idx].sort_values(by=['Number of Likes'], ascending=False)

    best_msg = {
                'message' : df["Message"].iloc[0],
                'messager' : df["Nickname"].iloc[0],
                'likes' : df['Number of Likes'].iloc[0],
                'attachments': df['Attachments'].iloc[0],
                }
    print(best_msg)
    return best_msg

def total_group_stats(df):
    # TO DO, TOTAL COMMENTS, LIKES, MEMBERS
    idx = df.groupby(['User ID'])['Time Stamp'].transform(max) == df['Time Stamp']
    df[idx].sort_values(by=['Time Stamp'], ascending=False)

    df_likes_comments = df.groupby('User ID').agg({'Number of Likes': ['sum','count']})
    df_likes_comments.columns = df_likes_comments.columns.droplevel()
    df_likes_comments["Average Likes"] = df_likes_comments["sum"]/df_likes_comments["count"]
    df_likes_comments.sort_values(by=['Average Likes'], ascending=False)


    df_members = pd.DataFrame(columns = ["User ID", "Nickname"])
    df_members["User ID"] = df[idx]["User ID"]
    df_members["Nickname"] = df[idx]["Nickname"]
    df_members = df_members.drop_duplicates()





    df_avg_likes = pd.merge(df_likes_comments, df_members, on='User ID', how='left').sort_values(by=['Average Likes'], ascending=False)
    df_avg_likes.rename(columns={'sum': 'Total Likes', 'count':'Comments Count', 'Average Likes':'Average Likes/Comment'}, inplace=True)
    df_avg_likes = df_avg_likes.drop_duplicates()
    print(df_avg_likes)


    total_user_likes = df['Number of Likes'].sum()
    total_user_comments = df_avg_likes[~df_avg_likes['User ID'].isin(['calendar', 'system'])]['Comments Count'].sum()
    df_avg_likes = df_avg_likes[~df_avg_likes['User ID'].isin(['calendar', 'system'])]
    if df_avg_likes.empty: # off chance the group has no messages from the members
        total_stats  = {
                        'total_comments': 0,
                        'total_likes': total_user_likes,
                        'num_participants': len(df_members),
                        'avg_likes_per_msg': 0
                        }
        return total_stats


    num_participants = len((df_avg_likes))

    best_ratio_user = { 'nickname': df_avg_likes.iloc[0]['Nickname'], 'ratio': df_avg_likes.iloc[0]['Average Likes/Comment']}
    chattiest_user = { }

    # total_comments = df_avg_likes.query("User ID not in ['calendar', 'system']")['Comments count'].sum()
    #print(total_comments)
    #total_members = df['User ID'].value_counts()


    total_stats  = {
                    'total_comments': total_user_comments,
                    'total_likes': total_user_likes,
                    'num_participants': num_participants,
                    'avg_likes_per_msg': total_user_likes/total_user_comments
                    }
    superaltive_members = {}
    print('Number of total likes', total_user_likes)
    print('Number of total comments', total_user_comments)
    print('Member with the best comments on average is', best_ratio_user['nickname'] ,
                'with an average of', best_ratio_user['ratio'], 'likes for every comment')

    return total_stats
    #print("Number of members likes", total_members)
