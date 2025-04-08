from django.urls import path
from . import views

urlpatterns = [
    path('bill10/',views.rendertemp),
    path('buyers/', views.BuyerListCreateView.as_view(), name='buyer-list-create'),
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),

    path('bills/create/', views.BillCreateView.as_view(), name='create-bill'),
    path('bills/<int:pk>/', views.BillRetrieveUpdateView.as_view(), name='view-update-bill'),
    path('bills/', views.BillListView.as_view(), name='bill-list'),

    path('reset/', views.ResetBillsView.as_view(), name='reset-bills'),
    path('export/', views.ExportBillsView.as_view(), name='export-bills'),
    path('archives/', views.ArchiveListView.as_view(), name='list-archives'),
]
