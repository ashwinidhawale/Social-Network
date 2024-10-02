from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSignupSerializer, UserLoginSerializer
from rest_framework.permissions import AllowAny
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from .permission import IsAdmin, IsWriter, IsReader
from django.contrib.postgres.search import SearchVector
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

class Signup(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'].lower(),
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({"message": "Admin Access"}, status=status.HTTP_200_OK)

class WriteView(APIView):
    permission_classes = [IsWriter]

    def post(self, request):
        return Response({"message": "Writer Access"}, status=status.HTTP_200_OK)

class ReadView(APIView):
    permission_classes = [IsReader]

    def get(self, request):
        return Response({"message": "Reader Access"}, status=status.HTTP_200_OK)
    
    
User = get_user_model()
class UserSearchView(APIView):
    def get(self, request):
        search_query = request.query_params.get('q', '').lower()
        page = request.query_params.get('page', 1)

        if not search_query:
            return Response({"error": "Search query is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Exact match on email
        user_by_email = User.objects.filter(email=search_query).first()
        if user_by_email:
            return Response({
                'results': [{
                    'username': user_by_email.username,
                    'email': user_by_email.email
                }]
            })

        # Full-text search on name
        users_by_name = User.objects.annotate(
            search=SearchVector('username', 'first_name', 'last_name')
        ).filter(search__icontains=search_query)

        # Pagination
        paginator = Paginator(users_by_name, 10)  # 10 results per page
        users_page = paginator.get_page(page)

        # Prepare response
        results = [
            {'username': user.username, 'email': user.email}
            for user in users_page
        ]
        return Response({
            'results': results,
            'page': users_page.number,
            'total_pages': paginator.num_pages
        })    
        
class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    # Rate limit to 3 friend requests per minute per user
    @method_decorator(ratelimit(key='user', rate='3/m', method='POST', block=True))
    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        to_user = CustomUser.objects.filter(id=to_user_id).first()

        if not to_user:
            return Response({"error": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a friend request already exists
        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response({"error": "Friend request already sent"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the friend request
        friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return Response({"message": "Friend request sent"}, status=status.HTTP_201_CREATED)

class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        friend_request = FriendRequest.objects.filter(id=request_id, to_user=request.user, status='pending').first()
        if not friend_request:
            return Response({"error": "Friend request not found"}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'accepted'
        friend_request.save()
        return Response({"message": "Friend request accepted"}, status=status.HTTP_200_OK)

class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        friend_request = FriendRequest.objects.filter(id=request_id, to_user=request.user, status='pending').first()
        if not friend_request:
            return Response({"error": "Friend request not found"}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'rejected'
        friend_request.save()
        return Response({"message": "Friend request rejected"}, status=status.HTTP_200_OK)        