from django.views.generic import DetailView, ListView

from .models import Blog


class BlogListView(ListView):
    model = Blog
    template_name = 'blog/blog_list.html'
    context_object_name = 'blogs'


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'
    context_object_name = 'blog'

    # TODO: логика увеличения счётчика лайков ещё не написана.
