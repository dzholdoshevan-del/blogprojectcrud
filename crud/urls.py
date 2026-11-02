from django.urls import path

from . import views

app_name = 'crud'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='list'),
    path('create/', views.ItemCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ItemUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ItemDeleteView.as_view(), name='delete'),
]
