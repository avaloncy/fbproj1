from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import generic
from django.utils import timezone
from django.urls import reverse

from . import models
from .forms import EntryForm
from social_django.models import UserSocialAuth
import facebook
import json
import copy


# Create your views here.

class BlogIndex(generic.ListView):
    queryset = models.Entry.objects.public()
    template_name="blog.html"
    paginate_by = 3

class BlogIndexPrivate(LoginRequiredMixin, generic.ListView):
    template_name="blog_private.html"
    paginate_by = 3
    def get_queryset(self):
        return models.Entry.objects.by_user(self.request.user)

def post_detail(request, slug):
    post = get_object_or_404(models.Entry, slug=slug)

    # Only the author can see the fb metric from the post detail
    if request.user.is_authenticated() and request.user == post.author:
        try:
            graph = get_fb_api( request.user )
            result = graph.get_object( post.post_to_fb_id + "/insights", metric='post_fan_reach,post_reactions_like_total')
            print(result)
            for metric in result['data']:
                if metric['name'] == 'post_fan_reach':
                    post.post_to_fb_reachs = get_metric_value( metric )
                elif metric['name'] == 'post_reactions_like_total':
                    post.post_to_fb_actions = get_metric_value( metric )
        except:
            post.post_to_fb_reachs = -1
            post.post_to_fb_actions = -1
    return render(request, 'post.html', {'object': post})


@login_required
def post_new(request):
    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()

            #Post to facebook if needed
            if post.post_to_fb == True:
                try:
                    graph = get_fb_api(request.user)
                    result = graph.put_object(get_page_id(), 'feed', message=post.title,
                                                                     link="http://www.fbposter.com:8000/" + reverse('post', kwargs={"slug": post.slug}), 
                                                                     published = post.post_to_fb_public )

                    post.post_to_fb_date = timezone.now()
                    post.post_to_fb_id = result['id']
                    post.save()
                except:
                    print("Failed to post to fb.")
                    post.post_to_fb = False
                    post.save()

            form.save_m2m()

            return redirect('post', slug=post.slug)
    else:
        form = EntryForm()
    return render(request, 'post_edit.html', {'form':form})


@login_required
def post_edit(request, slug):
    post = get_object_or_404(models.Entry, slug=slug)
    old_post = copy.deepcopy(post)
    if request.user != post.author:
        return redirect('myposts')

    if request.method == "POST":
        form = EntryForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()

            #Post to facebook if needed
            if old_post.post_to_fb == True:
                if post.post_to_fb == True:
                    try:
                        graph = get_fb_api( request.user )
                        graph.put_object(post.post_to_fb_id, "", message=post.title, is_published=post.post_to_fb_public )
                    except:
                        pass
                else:
                    try:
                        graph = get_fb_api( request.user )
                        graph.delete_object(id=post.post_to_fb_id)
                        post.post_to_fb_id = None
                    except:
                        post.post_to_fb = True
            else:
                if post.post_to_fb == True: 
                    try:
                        graph = get_fb_api( request.user )
                        result = graph.put_object(get_page_id(), 'feed', message=post.title,
                                                                         link="http://www.fbposter.com:8000/" + reverse('post', kwargs={"slug": post.slug}), 
                                                                         published = post.post_to_fb_public )
                        post.post_to_fb_date = timezone.now()
                        post.post_to_fb_id = result['id'];
                    except:
                        post.post_to_fb = False

            post.save()
            form.save_m2m()
            return redirect('post', slug=post.slug)
    else:
        form = EntryForm(instance=post)
    return render(request, 'post_edit.html', {'form': form})


@login_required
def post_delete(request, slug):
    post = get_object_or_404(models.Entry, slug=slug)
    if request.user != post.author:
        return redirect('myposts')

    if post.post_to_fb == True:
        try:
            graph = get_fb_api( request.user )
            graph.delete_object(id=post.post_to_fb_id)
        except:
            pass

    post.delete()
    return redirect('myposts')


@login_required
def change_post_to_fb(request, slug):
    post = get_object_or_404(models.Entry, slug=slug)
    if request.user != post.author:
        return redirect('post', slug=post.slug)

    graph = get_fb_api( request.user )
    if post.post_to_fb == True:
        try:
            graph.delete_object(id=post.post_to_fb_id)
            post.post_to_fb = False
            post.post_to_fb_id = None
        except:
            pass
    else:
        try:
            result = graph.put_object(get_page_id(), 'feed', message=post.title,
                                                             link="http://www.fbposter.com:8000/" + reverse('post', kwargs={"slug": post.slug}), 
                                                             published = post.post_to_fb_public )
            post.post_to_fb_date = timezone.now()
            post.post_to_fb_id = result['id']
            post.post_to_fb = True
        except:
            pass

    post.save()

    return redirect('post', slug=post.slug)

def get_fb_api( user ):
    social = user.social_auth.first()
    access_token = social.extra_data['access_token']

    graph = facebook.GraphAPI(access_token)
    # Get page token to post as the page. You can skip 
    # the following if you want to post as yourself. 
    resp = graph.get_object('me/accounts')
    page_access_token = None
    for page in resp['data']:
        if page['id'] == get_page_id():
            page_access_token = page['access_token']
    graph = facebook.GraphAPI(page_access_token)
    return graph

def get_page_id():
    return '323621744766235'

def get_metric_value( metric ):
    if not 'values' in metric:
        return -1
    values = metric['values']
    if values == None or len(values) == 0:
        return -1
    return values[0]['value']


@login_required
def post_insights(request):
    posts = models.Entry.objects.fb_posts_by_user(request.user)

    ids = [post.post_to_fb_id for post in posts if post.post_to_fb_id is not None]
    try:
        graph = get_fb_api( request.user )
        result = graph.get_object( "insights", ids=','.join(ids),
                                    metric='post_fan_reach,post_reactions_like_total')
    except:
        print("Failed to query insights from facebook")
        result = {}

    print(result)
    for post in posts:
        if post.post_to_fb_id in result:
            for metric in result[post.post_to_fb_id]['data']:
                if metric['name'] == 'post_fan_reach':
                    post.post_to_fb_reachs = get_metric_value( metric )
                elif metric['name'] == 'post_reactions_like_total':
                    post.post_to_fb_actions = get_metric_value( metric )
        else:
            post.post_to_fb_reachs = -1
            post.post_to_fb_actions = -1
        post.save()

    #insight on tags
    tags_of_interest = ['General','Tech']
    tag_results = []
    for tag in tags_of_interest:
        target_posts = posts.filter(tags__slug=tag)
        tag_result = {}
        tag_result['tag'] = tag
        tag_result['num_of_posts'] = len(target_posts)
        tag_result['data'] = target_posts
        tag_result['fb_reachs'] = sum([post.post_to_fb_reachs for post in target_posts if post.post_to_fb_reachs >= 0])
        tag_result['fb_actions'] = sum([post.post_to_fb_actions for post in target_posts if post.post_to_fb_actions >= 0])
        tag_results.append(tag_result)
    print(tag_results)
    return render(request, 'insights.html', {'allposts':posts, 'tag_results':tag_results})
