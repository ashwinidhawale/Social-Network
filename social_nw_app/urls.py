from django.urls import path
from .views import Signup, Login,UserSearchView, SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', Signup.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('search/', UserSearchView.as_view(), name='user_search'),
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend-request/accept/<int:request_id>/', AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', RejectFriendRequestView.as_view(), name='reject_friend_request'),
]
