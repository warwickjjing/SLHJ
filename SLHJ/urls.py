from argparse import Namespace
from unicodedata import name
from django.urls import path
from SLHJ import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('main/', views.main, name='main'),
    # path('list/', views.list),
    path('hotel_search/', views.hotel_search, name='hotel_search'),
    path('vacation_search/', views.vacation_search, name='vacation_search'),
    # path('login/', views.login),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('loginFail/', views.loginFail),
    path('user_create/', views.user_create),
    path('hotel_reserve/', views.hotel_reserve),
    path('vacation_reserve/', views.vacation_reserve),
    path('hotel_detail/<int:pk>/', views.hotel_detail, name='hotel_detail'),
    path('vacation_detail/<int:pk>/', views.vacation_detail, name='vacation_detail'),
    path('hotel_confirm/', views.hotel_confirm),
    path('vacation_confirm/', views.vacation_confirm),
    path('user_divide/', views.user_divide, name='user_divide'),
    path('user_create/', views.user_create, name='user_create'),

    # 마이페이지
    path('user_info/', views.user_info, name='user_info'),
    path('pw_change/', views.pw_change, name='pw_change'),
    path('pw_changeFail2/', views.pw_changeFail2, name='pw_changeFail2'),
    path('pw_changeOk/', views.pw_changeOk, name='pw_changeOk'),
    path('history_hotel/', views.history_hotel, name='history_hotel'),
    path('history_vacation/', views.history_vacation, name='history_vacation'),

    # 마이페이지 - admin
    path('admin_info/', views.admin_info, name='admin_info'),
    path('admin_pw_change/', views.admin_pw_change, name='admin_pw_change'),
    path('pw_changeFail/', views.pw_changeFail, name='pw_changeFail'),
    path('admin_hotel/', views.admin_hotel, name='admin_hotel'),
    path('admin_vacation/', views.admin_vacation, name='admin_vacation'),
    path('admin_manage/', views.admin_manage, name='admin_manage'),

    path('hotel_register/', views.hotel_register, name="hotel_register"),
    path('hotel_delete/', views.hotel_delete, name="hotel_delete"),
    path('hotel_delete2/', views.hotel_delete2, name="hotel_delete2"),
    path('hotel_deleteOk/', views.hotel_deleteOk, name="hotel_deleteOk"),
    path('hotel_deleteOk2/', views.hotel_deleteOk2, name="hotel_deleteOk2"),
    path('vacation_register/', views.vacation_register, name="vacation_register"),
    path('vacation_delete/', views.vacation_delete, name="vacation_delete"),
    path('vacation_delete2/', views.vacation_delete2, name="vacation_delete2"),
    path('vacation_deleteOk/', views.vacation_deleteOk, name="vacation_deleteOk"),
    path('vacation_deleteOk2/', views.vacation_deleteOk2, name="vacation_deleteOk2"),

    path('admin_hotel_detail/<int:hk>/', views.admin_hotel_detail, name="admin_hotel_detail"),
    path('admin_vacation_detail/<int:hk>/', views.admin_vacation_detail, name="admin_vacation_detail"),
    path('hotel_update/', views.hotel_update, name="hotel_update"),
    path('vacaion_update/', views.vacation_update, name="vacation_update"),



    #api data용
    # path('api/', views.api, name='api'),
    # path('api2/', views.api2, name='api2'),

    path('sample/', views.sample, name='sample'),       # vacation_reveiew 포맷입니다.
    path('sample2/', views.sample2, name='sample2'),    # vacation_reserve 포맷입니다.
    path('sample3/', views.sample3, name='sample3'),    # hotel_room 포맷입니다.
    path('sample4/', views.sample4, name='sample4'),    # hotel_reserve 포맷입니다.
    path('sample5/', views.sample5, name='sample5'),    # hotel_review 포맷입니다.
    path('sample6/', views.sample6, name='sample6'),    # hotel_imgage 포맷입니다.
    path('sample7/', views.sample7, name='sample7'),    # vacation_imgage 포맷입니다.

    # ajax 용
    path(r'option_change/<int:pk>/', views.option_change, name='option_change')
]

# hotel_image, vacation_image 경로
urlpatterns += static(
    settings.MEDIA_URL, 
    document_root = settings.MEDIA_ROOT


)