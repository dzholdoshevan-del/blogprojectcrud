from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('items/', include('crud.urls')),   # CRUD-приложение
    path('reports/', include('reports.urls')),   # отчёт по тестам -> Word
    path('', include('blog.urls')),
]
