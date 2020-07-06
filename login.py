from groupy.client import Client
from groupy import attachments


def login(t):
    token = t
    client = Client.from_token(token)
    return client
