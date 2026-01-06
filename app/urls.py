from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('home/', views.home, name='home'),

    path('sign_in/', views.sign_in, name='sign_in'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('logout/', views.logout, name='logout'),

    path('post/create/', views.create_post, name='create_post'),

    # ✅ DELETE FIRST (most specific)
    path('post/delete/<slug:slug>/', views.delete_post, name='delete_post'),

    # ✅ POST DETAIL
    path('post/<slug:post_slug>/', views.post_detail, name='post_detail'),

    # ✅ LIKE / DISLIKE LAST (most generic)
    path('post/<slug:slug>/<str:action>/', views.like_post, name='like_post'),

    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('myprofile/', views.my_profile, name='my_profile'),

    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('following/', views.following_feed, name='following_feed'),

    path('profile/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('profile/<str:username>/following/', views.following_list, name='following_list'),

    path('post/<slug:slug>/likes/', views.post_likes, name='post_likes'),

    path('search/', views.search_user, name='search_user'),
    path('ajax/search_users/', views.ajax_search_users, name='ajax_search_users'),

    path('delete_account/', views.delete_account, name='delete_account'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp1/', views.verify_otp1, name='verify_otp1'),
    path('reset-password/', views.reset_password, name='reset_password'),


]
