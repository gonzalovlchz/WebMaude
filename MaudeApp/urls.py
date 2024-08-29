from django.urls import path
from .views import acl_views, index_views, chat_views

urlpatterns = [
    path("", index_views.index, name="index"),
    path("login", index_views.login_form, name="login_form"),
    path("acl/login", acl_views.post_login, name="post_login"),
    path("acl/logout", acl_views.get_logout, name="get_logout"),
    path("chat/get_all_sessions", chat_views.get_all_sessions, name="get_all_sessions"),
    path("chat/get_chat_session", chat_views.get_chat_session, name="get_chat_session"),
    path("chat/start_new_session", chat_views.start_new_session, name="start_new_session"),
    path("chat/post_execute_new_command", chat_views.post_execute_new_command, name="post_execute_new_command"),
    path('chat/get_files_by_session_type/', chat_views.get_files_by_session_type, name='get_files_by_session_type')
]