from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
import markdown
from .models import ArticlePost
# Create your views here.


def article_list(request):
    article = ArticlePost.objects.all()
    context = {'articles':article}
    return render(request, 'article/list.html', context)

def article_detail(request, id):

    article = ArticlePost.objects.get(id = id)

    article.body = markdown.markdown(article.body,
                                     extensions=[
                                         'markdown.extensions.extra',
                                         'markdown.extensions.codehilite',
                                     ])

    context = { 'article': article}

    return render(request, 'article/detail.html', context)
