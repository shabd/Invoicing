from django.urls import path
from . import views

urlpatterns = [

    path('dashboard', views.dashboard, name='dashboard'),
    path('invoices', views.invoices, name='invoices'),
    path('products', views.products, name='products'),
    path('clients', views.clients, name='clients'),

    #Create URL Paths
    path('invoices/create', views.createInvoice, name='create-invoice'),
    path('invoices/create-build/<slug:slug>',
         views.createBuildInvoice, name='create-build-invoice'),

    #Delete an invoice
    path('invoices/delete/<slug:slug>',
         views.deleteInvoice, name='delete-invoice'),

    #PDF and EMAIL Paths
    path('invoices/view-pdf/<slug:slug>',
         views.viewPDFInvoice, name='view-pdf-invoice'),
    path('invoices/view-document/<slug:slug>',
         views.viewDocumentInvoice, name='view-document-invoice'),

]