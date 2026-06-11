from django.db.models import Q
from django.views.generic import DetailView, ListView

from core.models import Category, Project, Tag


class CategoryDetail(ListView):
    paginate_by = 6
    model = Project
    template_name = 'core/index.html'
    context_object_name = 'projects'
    allow_empty = True

    def create_store_data(self, **kwargs):
        context = kwargs
        if 'slug' in self.kwargs:
            context['core_title'] = str(
                Category.objects.get(slug=self.kwargs['slug']))
            context['project_count'] = Project.objects.filter(
                category__slug=self.kwargs['slug']).count()
            return context
        context['core_title'] = 'Welcome'
        return context

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.create_store_data()
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self, **kwargs):
        if 'slug' in self.kwargs:
            return Project.objects.filter(
                category__slug=self.kwargs['slug']
            ).select_related('category').order_by('ordering', '-created_at')
        return Project.objects.all().select_related(
            'category',
        ).order_by('ordering', '-created_at')


class ProjectDetail(DetailView):
    model = Project
    template_name = 'core/portfolio_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery_images'] = self.object.projectgallery.all()
        return context


class ProjectSearchListView(ListView):
    model = Project
    template_name = 'core/index.html'
    context_object_name = 'projects'
    paginate_by = 4

    def get_queryset(self):
        keywords = self.request.GET.get('keyword')
        queryset = super().get_queryset()

        if keywords:
            queryset = queryset.filter(
                Q(content__icontains=keywords) | Q(title__icontains=keywords))

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_count'] = self.get_queryset().count()
        context['core_title'] = 'Search Result'
        context['keyword'] = self.request.GET.get('keyword')
        return context


class ProjectsByTag(ListView):
    template_name = 'core/index.html'
    context_object_name = 'projects'
    paginate_by = 6
    allow_empty = False

    def get_queryset(self):
        return Project.objects.filter(tags__slug=self.kwargs['slug'])

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['core_title'] = str(Tag.objects.get(slug=self.kwargs['slug']))
        return context
