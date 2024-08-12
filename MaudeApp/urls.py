from django.urls import path
from .views import acl_views, index_views

urlpatterns = [
    path("", index_views.index, name="index"),
    path("login", index_views.login_form, name="login_form"),
    path("acl/login", acl_views.post_login, name="post_login"),
    path("acl/logout", acl_views.get_logout, name="get_logout")
]