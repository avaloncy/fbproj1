from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import generic
from django.utils import timezone

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

class BlogDetail(generic.DetailView):
    model = models.Entry
    template_name = "post.html"

@login_required
def post_new(request):
    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            
            #Post to facebook if needed
            if post.post_to_fb == True:
                social = request.user.social_auth.first()
                access_token = social.extra_data['access_token']
                graph = facebook.GraphAPI(access_token)

                privacy = {
                    'value' : 'EVERYONE'
                };
                if not post.post_to_fb_public:
                    privacy['value'] = "SELF"

                #result = graph.put_object('', '323621744766235', message=post.title )                
                result = graph.put_object('me', 'feed', message=post.title, privacy=json.dumps(privacy) )

                post.post_to_fb_date = timezone.now()
                post.post_to_fb_id = result['id'];

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

            privacy = {
                'value' : 'EVERYONE'
            };
            if not post.post_to_fb_public:
                privacy['value'] = "SELF"

            #Post to facebook if needed
            if old_post.post_to_fb == True:
                social = request.user.social_auth.first()
                access_token = social.extra_data['access_token']
                graph = facebook.GraphAPI(access_token)

                if post.post_to_fb == True:
                    graph.put_object(post.post_to_fb_id, "", message=post.title, privacy=json.dumps(privacy) )
                else:
                    graph.delete_object(id=post.post_to_fb_id)
            else:
                if post.post_to_fb == True: 
                    social = request.user.social_auth.first()
                    access_token = social.extra_data['access_token']
                    graph = facebook.GraphAPI(access_token)

                    #result = graph.put_object('', '323621744766235', message=post.title )                
                    result = graph.put_object('me', 'feed', message=post.title, privacy=json.dumps(privacy) )

                    post.post_to_fb_date = timezone.now()
                    post.post_to_fb_id = result['id'];

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
        social = request.user.social_auth.first()
        access_token = social.extra_data['access_token']
        graph = facebook.GraphAPI(access_token)
        graph.delete_object(id=post.post_to_fb_id)

    post.delete()
    return redirect('myposts')


@login_required
def change_post_to_fb(request, slug):
    post = get_object_or_404(models.Entry, slug=slug)
    if request.user != post.author:
        return redirect('post', slug=post.slug)

    social = request.user.social_auth.first()
    access_token = social.extra_data['access_token']
    graph = facebook.GraphAPI(access_token)
    if post.post_to_fb == True:
        graph.delete_object(id=post.post_to_fb_id)
        post.post_to_fb = False;
        post.post_to_fb_id = None
    else:      
        privacy = {
            'value' : 'EVERYONE'
        };
        if not post.post_to_fb_public:
            privacy['value'] = "SELF"
        result = graph.put_object('me', 'feed', message=post.title, privacy=json.dumps(privacy) )
        post.post_to_fb_date = timezone.now()
        post.post_to_fb_id = result['id']
        post.post_to_fb = True

    post.save()
        
    return redirect('post', slug=post.slug)