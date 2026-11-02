from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView,
                                  ListView, UpdateView)

from .forms import ItemForm
from .models import Item


class ItemListView(ListView):          # READ (список)
    model = Item
    template_name = 'crud/item_list.html'
    context_object_name = 'items'


class ItemDetailView(DetailView):      # READ (одна запись)
    model = Item
    template_name = 'crud/item_detail.html'
    context_object_name = 'item'


class ItemCreateView(CreateView):      # CREATE
    model = Item
    form_class = ItemForm
    template_name = 'crud/item_form.html'
    # после создания Django сам перейдёт на get_absolute_url() модели


class ItemUpdateView(UpdateView):      # UPDATE
    model = Item
    form_class = ItemForm
    template_name = 'crud/item_form.html'


class ItemDeleteView(DeleteView):      # DELETE
    model = Item
    template_name = 'crud/item_confirm_delete.html'
    context_object_name = 'item'
    success_url = reverse_lazy('crud:list')
