from django.urls import path
from django.conf.urls import url
from django.urls import re_path


from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/access_token=<slug:access_token>/group_id=<slug:group_id>/group_name=<str:group_name>/', views.analyze, name='analyze'),
    path('groups/', views.groups, name='groups'),
    path('analyze/access_token=<slug:access_token>/group_id=<slug:group_id>/group_name=<str:group_name>/download_data/', views.download_data, name='download_data'),
]
