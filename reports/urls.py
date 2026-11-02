from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_page, name='report'),
    path('download.doc', views.download_doc, name='download_doc'),
    path('download.docx', views.download_docx, name='download_docx'),
]
