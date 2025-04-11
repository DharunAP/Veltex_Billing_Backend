from django.urls import path
from . import views

urlpatterns = [
    path('bill10/',views.rendertemp),
    path('buyers/', views.BuyerListCreateView.as_view(), name='buyer-list-create'),
    path('buyers/<int:id>/', views.BuyerRetrieveUpdateDestroyView.as_view(), name='buyer-detail'),

    path('bills/create/', views.BillCreateView.as_view(), name='create-bill'),
    path('bills/<int:pk>/', views.BillRetrieveUpdateDestroyView.as_view(), name='view-update-bill'),
    path('bills/', views.BillListView.as_view(), name='bill-list'),

    path('export/', views.ExportBillsView.as_view(), name='export-bills'),
    path('archives/', views.ArchiveListView.as_view(), name='list-archives'),
]
