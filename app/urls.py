from django.urls import path, re_path
from app import views


urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    # PARAM ADD/EDIT (DISPLAY OPTIONS)
    path('create_param/', views.CreateParam, name="create_param"),

    # PARAM STORE
    path('store_param/', views.StoreParam, name="store_param"),

    # PARAM SEARCH
    path('list/', views.ListParam, name="list_param"),

    # view stored datasets
    re_path(r'^transactions/(?:(?P<pk>\d+)/)?(?:(?P<action>\w+)/)?', views.TransactionView.as_view(),
            name='transactions'),


    # # add new datasets
    # re_path(r'^intake/(?:(?P<pk>\d+)/)?(?:(?P<action>\w+)/)?', views.IntakeView.as_view(),
    #         name='intake'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
