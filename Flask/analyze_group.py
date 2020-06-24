# analyze_group.py
from groupy.client import Client
import pandas as pd
import requests
import json
import datetime as dt
from login import login
import seaborn as sns
import matplotlib.pyplot as plt
import pprint as pp


members_df = pd.DataFrame(columns = ["User ID", "Nickname"])

gm_msgs, gm_likes, gm_users, gm_users_id, gm_created_at, gm_favorited_by, gm_attachments, gm_user_pic = [], [], [], [], [], [], [], []

def scrape_messages(group_id, token):

    gm_msgs, gm_likes, gm_users, gm_users_id, gm_created_at, gm_favorited_by, gm_attachments, gm_user_pic = [], [], [], [], [], [], [], []

    all_users_dict = {}


    url = "https://api.groupme.com/v3/groups/"+str(group_id)+"/messages?token="+str(token)#9429f5a055c30138f03c768570a6045f"
    urlData = {'limit':100}
    print(url)
    response = requests.get(url, params=urlData)
    res_js = None
    messages = None

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
          gm_user_pic.append(messages[i]['avatar_url'])
          gm_favorited_by.append(messages[i]['favorited_by'])
          gm_attachments.append(messages[i]['attachments'])
          if 'event' in messages[i]:
              if messages[i]['event']['type'] == 'membership.announce.added':
                if 'adder_user' in messages[i]['event']['data']:
                    pp.pprint(messages[i]['event']['data'])
                    all_users_dict[messages[i]['event']['data']['adder_user']['id']] = messages[i]['event']['data']['adder_user']['nickname']
                for i in messages[i]['event']['data']['added_users']:
                    all_users_dict[i['id']] = i['nickname']#print(json_formatted_str)
    except:
        json_formatted_str = json.dumps(res_js, indent=5)
        df = pd.DataFrame(columns=["User ID", "Nickname","Message", "Attachments","Time Stamp", "Number of Likes", "Liked By", "User Avatar"])

        df["Message"]=gm_msgs
        df["Attachments"]= gm_attachments
        df["Number of Likes"]=gm_likes
        df["User ID"] = gm_users_id
        df["Time Stamp"] = gm_created_at
        df["Nickname"] = gm_users
        df["Liked By"] = gm_favorited_by
        df["User Avatar"] = gm_user_pic

        client = Client.from_token(token)
        group_to_analyze = client.groups.get(group_id)
        member_list = group_to_analyze.members

        user_ids = []
        nicknames = []

        for member in member_list:
            print(member)
            user_ids.append(member.user_id)
            nicknames.append(member.nickname)

        df_members = pd.DataFrame(columns = ["User ID", "Nickname"])
        df_members["User ID"] = user_ids
        df_members["Nickname"] = nicknames

        all_users_df = pd.DataFrame(all_users_dict.items(), columns=['User ID', 'Nickname'])

        all_users_df['User ID'] = all_users_df['User ID'].apply(str)
        #ids = df_members['User ID'].to_list()

        result = df_members.append([all_users_df])
        result = result.drop_duplicates(subset='User ID', keep="first")

        print(result)
        print('result^')
        print(all_users_df)
        print("Done")

        return df, result


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

def total_group_stats(df, df_members):
    # TO DO, TOTAL COMMENTS, LIKES, MEMBERS
    all_users_df = df_members.copy()
    print(df_members)

    user_ids = df['User ID'].unique().tolist()
    print(user_ids)

    for i in user_ids:
        if i not in df_members['User ID'].values:
            df_members.append({'user ID' : i } , ignore_index=True)

    print(df_members)

    idx = df.groupby(['User ID'])['Time Stamp'].transform(max) == df['Time Stamp']
    df[idx].sort_values(by=['Time Stamp'], ascending=False)

    df_likes_comments = df.groupby(['User ID']).agg({'Number of Likes': ['sum','count']})
    df_likes_comments.columns = df_likes_comments.columns.droplevel()
    df_likes_comments["Average Likes"] = df_likes_comments["sum"]/df_likes_comments["count"]
    df_likes_comments.sort_values(by=['Average Likes'], ascending=False)

    idx2 = df.groupby(['User Avatar'])['Time Stamp'].transform(max) == df['Time Stamp']
    df[idx].sort_values(by=['Time Stamp'], ascending=False)
    print('idx2', idx2)
    df_user_avatars = df[idx2]
    df_user_avatars = df_user_avatars.drop_duplicates(subset='User ID', keep="first")
    df_user_avatars_merge = df_user_avatars[['User ID', 'User Avatar']]
    print(df_user_avatars_merge)

    print('df_likes_comments', df_likes_comments)
    #df_members = pd.DataFrame(columns = ["User ID", "Nickname"])
    #df_members["User ID"] = df[idx]["User ID"]
    #df_members["Nickname"] = df[idx]["Nickname"]

    #df_members = df_members.drop_duplicates()
    print('df_members')
    print(df_members)


    df_avg_likes = pd.merge(df_likes_comments, df_members, on='User ID', how='left').sort_values(by=['Average Likes'], ascending=False)
    df_avg_likes.rename(columns={'sum': 'Total Likes', 'count':'Comments Count', 'Average Likes':'Average Likes/Comment'}, inplace=True)
    df_avg_likes = df_avg_likes.drop_duplicates()
    df_avg_likes_merge = pd.merge(df_avg_likes, df_user_avatars_merge, on='User ID', how='left').sort_values(by=['Average Likes/Comment'], ascending=False)


    print('\n')
    print(df_avg_likes_merge)
    print('\n')


    total_user_likes = df['Number of Likes'].sum()
    total_user_comments = df_avg_likes[~df_avg_likes['User ID'].isin(['calendar', 'system'])]['Comments Count'].sum()
    df_avg_likes = df_avg_likes[~df_avg_likes['User ID'].isin(['calendar', 'system'])]
    if df_avg_likes.empty: # off chance the group has no messages from the members
        total_stats  = {
                        'total_comments': 0,
                        'total_likes': total_user_likes,
                        'num_participants': len(all_users_df),
                        'avg_likes_per_msg': 0
                        }
        return total_stats


    num_participants = len((all_users_df))

    best_ratio_user = {'nickname': df_avg_likes_merge.iloc[0]['Nickname'], 'ratio': df_avg_likes_merge.iloc[0]['Average Likes/Comment'], 'url': df_avg_likes_merge.iloc[0]['User Avatar']}
    df_avg_likes_merge.sort_values(by=['Comments Count'], ascending=False, inplace=True)
    #print(df_avg_likes)
    chattiest_user = {'nickname': df_avg_likes_merge.iloc[0]['Nickname'], 'num_comments': df_avg_likes_merge.iloc[0]['Comments Count'], 'url': df_avg_likes_merge.iloc[0]['User Avatar']}
    df_avg_likes_merge.sort_values(by=['Total Likes'], ascending=False, inplace=True)
    most_liked_user = {'nickname': df_avg_likes_merge.iloc[0]['Nickname'], 'num_likes': df_avg_likes_merge.iloc[0]['Total Likes'], 'url': df_avg_likes_merge.iloc[0]['User Avatar']}



    #df_likes_given = df_members.copy()
    df_likes_given = pd.merge(df_members, df_user_avatars_merge, on='User ID', how='left')
    df_likes_given['Likes Given'] = 0
    df_likes_given['Self Likes'] = 0
    gm_favorited_by = df['Liked By'].tolist()
    gm_users_id = df['User ID'].tolist()

    for j, k in  zip(gm_favorited_by, gm_users_id):
      for i in j:
        df_likes_given.loc[df_likes_given["User ID"] == i, 'Likes Given']+=1
        if (k == i):
          df_likes_given.loc[df_likes_given["User ID"] == i, 'Self Likes']+=1



    df_likes_given.sort_values(by=['Likes Given'], ascending=False, inplace=True)
    most_likes_given_user = {'nickname': df_likes_given.iloc[0]['Nickname'], 'likes_given': df_likes_given.iloc[0]['Likes Given'], 'url': df_likes_given.iloc[0]['User Avatar']}
    df_likes_given.sort_values(by=['Self Likes'], ascending=False, inplace=True)

    most_self_likes_user = {'nickname': df_likes_given.iloc[0]['Nickname'], 'self_likes': df_likes_given.iloc[0]['Self Likes'], 'url': df_likes_given.iloc[0]['User Avatar']}
    print(df_likes_given)


    ## Mentions

    df_mentions = pd.merge(df_members, df_user_avatars_merge, on='User ID', how='left')#= df_members.copy()
    df_mentions['Times Mentioned'] = 0
    df_mentions['Times Mentioning Others'] = 0
    mentions = []

    for a in df['Attachments'].tolist():
      if len(a) >=1 and a[0]['type'] == 'mentions' :
        mentions.append(a[0]['user_ids'])


    for m in mentions:
      for n in m:
          df_mentions.loc[df_mentions["User ID"] == n, 'Times Mentioned']+=1

    print(df_mentions)
    df_mentions.sort_values(by=['Times Mentioned'], ascending=False, inplace=True)
    most_mentioned_user = {'nickname': df_mentions.iloc[0]['Nickname'], 'times_mentioned': df_mentions.iloc[0]['Times Mentioned'], 'url': df_mentions.iloc[0]['User Avatar']}


    ## Likes Matrix

    likes_matrix = all_users_df.copy()
    ids = all_users_df['User ID'].to_list()
    names = all_users_df['Nickname'].to_list()
    ids_names_dict = {str(ids[i]): names[i] for i in range(len(names))}


    for i in ids: #likes_matrix['User ID'].tolist():
      likes_matrix[i] = 0

    print(likes_matrix)
    #print(gm_favorited_by, gm_users_id)
    try:
        for fb, i in  zip(gm_favorited_by, gm_users_id):
          for f in fb:
            if i in likes_matrix['User ID'].tolist():
                likes_matrix.loc[likes_matrix['User ID'] == str(i), f]+=1
    except KeyError:
        print("Key is unknown.")


    if 'system' in likes_matrix.columns:
      likes_matrix.drop(['system'], axis=1, inplace=True)
    if 'calendar' in likes_matrix.columns:
      likes_matrix.drop(['calendar'], axis=1, inplace=True)

    print(likes_matrix)

    for column in likes_matrix[ids]:
      likes_matrix.rename(columns={column: ids_names_dict[column]}, inplace=True)

#likes_matrix.drop(likes_matrix[likes_matrix['Nickname'] == 'GroupMe'].index, axis=0, inplace=True)
#likes_matrix.drop(likes_matrix[likes_matrix['Nickname'] == 'GroupMe Calendar'].index, axis=0, inplace=True)

    likes_matrix.drop(['User ID'], axis=1, inplace=True)


    likes_matrix.set_index('Nickname', inplace=True)

## Drops people that haven't receieved or given a like
    # for cols in likes_matrix:
    #   if not likes_matrix[cols].any():
    #     likes_matrix.drop(columns = [cols], inplace=True)
    #
    # for index, row in likes_matrix.iterrows():
    #   if sum(row) == 0:
    #     likes_matrix.drop(index, inplace=True)


    #ids = df_members['User ID'].to_list()
    #if 'calendar' in ids:
     # ids.remove('calendar')
    #if 'system' in ids:
    #    ids.remove('system')

    # ## ------
    # names = df_members['Nickname'].to_list()
    # if 'GroupMe' in names:
    #     names.remove('GroupMe')
    # if 'GroupMe Calendar' in names:
    #   names.remove('GroupMe Calendar')
    #
    # ids_names_dict = {ids[i]: names[i] for i in range(len(names))}
    # print(ids_names_dict)
    #
    #
    # likes_matrix = df_members.copy()
    # for i in likes_matrix['User ID'].tolist():
    #     likes_matrix[i] = 0
    #
    # gm_users_id = df["User ID"].tolist()
    # gm_favorited_by = df["Liked By"].tolist()
    #
    # for fb, i in  zip(gm_favorited_by, gm_users_id):
    #     for f in fb:
    #         likes_matrix.loc[likes_matrix['User ID'] == i, f]+=1
    # if 'system' in likes_matrix.columns:
    #     likes_matrix.drop(['system'], axis=1, inplace=True)
    # if 'calendar' in likes_matrix.columns:
    #     likes_matrix.drop(['calendar'], axis=1, inplace=True)
    #
    # for column in likes_matrix[ids]:
    #     likes_matrix.rename(columns={column: ids_names_dict[column]}, inplace=True)
    #
    # likes_matrix.drop(likes_matrix[likes_matrix['Nickname'] == 'GroupMe'].index, axis=0, inplace=True)
    # likes_matrix.drop(likes_matrix[likes_matrix['Nickname'] == 'GroupMe Calendar'].index, axis=0, inplace=True)
    #
    # likes_matrix.drop(['User ID'], axis=1, inplace=True)
    # likes_matrix.set_index('Nickname', inplace=True)

###------
    #plt.figure(figsize=(10, 10))
    #plt.savefig(img, format='png')

    #ax = sns.heatmap(likes_matrix, annot=True, fmt='d', cmap="YlGnBu")
    #ax.set(xlabel='Likes Given', ylabel='Likes Recieved')
    #plt.savefig('/static/images/new_plot.png')

    print(likes_matrix)


    total_stats  = {
                    'total_comments' : total_user_comments,
                    'total_likes' : total_user_likes,
                    'num_participants' : num_participants,
                    'avg_likes_per_msg' : total_user_likes/total_user_comments
                    }
    superaltive_members = {
                    'chattiest_user' : chattiest_user,
                    'best_ratio_user' : best_ratio_user,
                    'most_liked_user' : most_liked_user,
                    'most_likes_given_user' : most_likes_given_user,
                    'most_mentioned_user' : most_mentioned_user,
                    'most_self_likes_user': most_self_likes_user
                    }



    print('Number of total likes', total_user_likes)
    print('Number of total comments', total_user_comments)
    print('Member with the best comments on average is', best_ratio_user['nickname'] ,
                'with an average of', best_ratio_user['ratio'], 'likes for every comment')

    print('Member with the most comments on average is', chattiest_user['nickname'] ,
                'with total of ', chattiest_user['num_comments'], ' comments')
    return total_stats, superaltive_members, likes_matrix
    #print("Number of members likes", total_members)
