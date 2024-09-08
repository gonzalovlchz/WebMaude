from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

def post_login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("get_index")
            else:
                messages.error(request, 'Your account is pending approval. Please contact support if you believe this is an error.')
        else:
            # Check if the user exists but failed authentication
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    messages.error(request, 'Your account is pending approval. Please contact support if you believe this is an error.')
                else:
                    messages.error(request, 'Incorrect password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
    
    return redirect('get_login_form')

def get_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('get_login_form')

def post_signup(request):
    if request.method == 'POST':
        # Extract data from POST request
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate input data
        if not username or not email or not password1 or not password2:
            messages.error(request, 'All fields are required.')
            return redirect('get_login_form')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('get_login_form')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return redirect('get_login_form')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
            return redirect('get_login_form')

        # Create new user but set is_active to False until admin approval
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password1),  # Hash the password manually
            is_active=False
        )

        messages.success(request, 'Your account has been created. Please wait for admin approval.')
        return redirect('get_login_form')
