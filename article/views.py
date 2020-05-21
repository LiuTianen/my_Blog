from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
import markdown
from .forms import ArticlePosrForm
from .models import ArticlePost, ArticleColumn
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
# Create your views here.


def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    article_list = ArticlePost.objects.all()
    # 用户搜索逻辑
    if search:
        article_list = article_list.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            ).order_by('-total_views')
    else:
        search = ''

    if column is not  None and column.isdigit():
        article_list = article_list.filter(column=column)

    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    if order == 'total_views':
        article_list = article_list.all().order_by('-total_views')

    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    context = {'articles': articles, 'order': order, 'search': search, 'tag':tag}
    return render(request, 'article/list.html', context)

def article_detail(request, id):

    article = ArticlePost.objects.get(id = id)
    # 取出文章评论
    comments =Comment.objects.filter(article=id)
    comment_form = CommentForm()

    article.total_views += 1
    article.save(update_fields=['total_views'])
    # 将markdown语法渲染成html样式
    md = markdown.Markdown(
                                     extensions=[
                                         # 包含 缩写、表格等常用扩展
                                         'markdown.extensions.extra',
                                         # 语法高亮扩展
                                         'markdown.extensions.codehilite',
                                         # 目录扩展
                                         'markdown.extensions.toc',
                                     ])
    article.body = md.convert(article.body)
    context = { 'article': article, 'toc': md.toc, 'comments': comments, 'comment_form': comment_form}
    return render(request, 'article/detail.html', context)

# 写文章的视图
def article_create(request):
    # 判断用户是否提交数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePosrForm(request.POST, request.FILES)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            # 将新文章保存到数据库中
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            new_article.save()
            article_post_form.save_m2m()
            # 完成后返回到文章列表
            return redirect("article:article_list")
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    # 如果用户请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePosrForm()
        # 赋值上下文
        columns = ArticleColumn.objects.all()
        context = {'article_post_form':article_post_form, 'columns':columns}
        # 返回模板
        return render(request, 'article/create.html', context)

# 删文章
def article_delete(request, id):
    # 根据 id 获取需要删除的文章
    article = ArticlePost.objects.get(id=id)
    # 调用.delete()方法删除文章
    article.delete()
    # 完成删除后返回文章列表
    return redirect("article:article_list")

def article_safe_delete(request, id):
    if request.method =='POST':
        article = ArticlePost.objects.get(id=id)
        article.delete()
        return redirect("article:article_list")
    else:
        return HttpResponse("仅允许post请求")

@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    """
        更新文章的视图函数
        通过POST方法提交表单，更新titile、body字段
        GET方法进入初始表单页面
        id： 文章的 id
    """
    #获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章")
    # 判断用户是否为 POST 提交表单数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePosrForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存新写入的 title、body 数据并保存
            article.title = request.POST['title']
            article.body = request.POST['body']
            if request.POST['colum'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None

            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')
            article.tag.set(*request.POST.get('tags').split(','), clear=True)
            article.save()
            # 完成后返回到修改后的文章中。需传入文章的 id 值
            return redirect("article:article_detail", id=id)
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")

    # 如果用户 GET 请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePosrForm()
        columns = ArticleColumn.objects.all()
        # 赋值上下文，将 article 文章对象也传递进去，以便提取旧的内容
        context = {'article': article, 'article_post_form': article_post_form, 'columns': columns,
                   'tags': ','.join([x for x in article.tags.names()]),
                   }
        # 将响应返回到模板中
        return render(request,'article/update.html', context)



