from django.shortcuts import render
from django.http import HttpResponse

from .models import Article, War, Tactics, Era

import requests
import json

def homepage(request):
    articles = Article.objects.all()

    return render(request, 'content/homepage.html', {'articles': articles})

def article(request, id):
    article = Article.objects.get(pk=id)

    return render(request, 'content/article.html', {'article': article})

def context(request, id):
    context = War.objects.get(pk=id)

    return render(request, 'content/articleContext.html', {'context': context})

def article_tactics(request, tactics_link):
    tactics_articles = Article.objects.filter(tactics_link=tactics_link)

    return render(request, 'content/articleTactics.html', {'tactics_articles': tactics_articles, 'tactics': tactics_link})

def era(request, id):
    era = Era.objects.get(pk=id)

    return render(request, 'content/era.html', {'era': era})