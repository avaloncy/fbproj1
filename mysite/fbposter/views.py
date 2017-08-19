from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import generic
from django.utils import timezone

from . import models
from .forms import EntryForm
from social_django.models import UserSocialAuth

# Create your views here.

class BlogIndex(generic.ListView):
    queryset = models.Entry.objects.public()
    template_name="blog.html"
    paginate_by = 3


class BlogIndexPrivate(LoginRequiredMixin, generic.ListView):
    template_name="blog.html"
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
            post.save()
            form.save_m2m()
            return redirect('post', slug=post.slug)
    else:
        form = EntryForm()
    return render(request, 'post_edit.html', {'form':form})