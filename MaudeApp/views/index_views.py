from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def get_index(request):
    return render(request, 'MaudeApp/index.html')

def get_login_form(request):
    return render(request, 'MaudeApp/login_form.html')