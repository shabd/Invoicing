from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import *
from .models import *


from django.contrib.auth.models import User, auth
from random import randint
from uuid import uuid4

from django.http import HttpResponse

import pdfkit
from django.template.loader import get_template
import os


def index(request):
    context = {}
    return render(request, 'invoice/dashboard.html', context)


def dashboard(request):
    clients = Client.objects.all().count()
    invoices = Invoice.objects.all().count()
    paidInvoices = Invoice.objects.filter(status='PAID').count()

    context = {}
    context['clients'] = clients
    context['invoices'] = invoices
    context['paidInvoices'] = paidInvoices
    return render(request, 'invoice/dashboard.html', context)


def invoices(request):
    context = {}
    invoices = Invoice.objects.all()
    context['invoices'] = invoices

    return render(request, 'invoice/invoices.html', context)


def products(request):
    context = {}
    products = Product.objects.all()
    context['products'] = products

    return render(request, 'invoice/products.html', context)


def clients(request):
    context = {}
    clients = Client.objects.all()
    context['clients'] = clients

    if request.method == 'GET':
        form = ClientForm()
        context['form'] = form
        return render(request, 'invoice/clients.html', context)

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()

            messages.success(request, 'New Client Added')
            return redirect('clients')
        else:
            messages.error(request, 'Problem processing your request')
            return redirect('clients')

    return render(request, 'invoice/clients.html', context)


###--------------------------- Create Invoice Views Start here --------------------------------------------- ###

def createInvoice(request):
    #create a blank invoice ....
    number = 'INV-'+str(uuid4()).split('-')[1]
    newInvoice = Invoice.objects.create(number=number)
    newInvoice.save()

    inv = Invoice.objects.get(number=number)
    return redirect('create-build-invoice', slug=inv.slug)


def createBuildInvoice(request, slug):
    #fetch that invoice
    try:
        invoice = Invoice.objects.get(slug=slug)
        pass
    except:
        messages.error(request, 'Something went wrong')
        return redirect('invoices')

    #fetch all the products - related to this invoice
    products = Product.objects.filter(invoice=invoice)

    context = {}
    context['invoice'] = invoice
    context['products'] = products

    if request.method == 'GET':
        prod_form = ProductForm()
        inv_form = InvoiceForm(instance=invoice)
        client_form = ClientSelectForm(initial_client=invoice.client)
        context['prod_form'] = prod_form
        context['inv_form'] = inv_form
        context['client_form'] = client_form
        return render(request, 'invoice/create-invoice.html', context)

    if request.method == 'POST':
        prod_form = ProductForm(request.POST)
        inv_form = InvoiceForm(request.POST, instance=invoice)
        client_form = ClientSelectForm(
            request.POST, initial_client=invoice.client, instance=invoice)

        if prod_form.is_valid():
            obj = prod_form.save(commit=False)
            obj.invoice = invoice
            obj.save()

            messages.success(request, "Invoice product added succesfully")
            return redirect('create-build-invoice', slug=slug)
        elif inv_form.is_valid and 'paymentTerms' in request.POST:
            inv_form.save()

            messages.success(request, "Invoice updated succesfully")
            return redirect('create-build-invoice', slug=slug)
        elif client_form.is_valid() and 'client' in request.POST:

            client_form.save()
            messages.success(request, "Client added to invoice succesfully")
            return redirect('create-build-invoice', slug=slug)
        else:
            context['prod_form'] = prod_form
            context['inv_form'] = inv_form
            context['client_form'] = client_form
            messages.error(request, "Problem processing your request")
            return render(request, 'invoice/create-invoice.html', context)

    return render(request, 'invoice/create-invoice.html', context)


def deleteInvoice(request, slug):
    try:
        Invoice.objects.get(slug=slug).delete()
    except:
        messages.error(request, 'Something went wrong')
        return redirect('invoices')

    return redirect('invoices')


def viewPDFInvoice(request, slug):
    #fetch that invoice
    try:
        invoice = Invoice.objects.get(slug=slug)
        pass
    except:
        messages.error(request, 'Something went wrong')
        return redirect('invoices')

    #fetch all the products - related to this invoice
    products = Product.objects.filter(invoice=invoice)

    #Calculate the Invoice Total
    invoiceCurrency = ''
    invoiceTotal = 0.0
    if len(products) > 0:
        for x in products:
            y = float(x.quantity) * float(x.price)
            invoiceTotal += y
            invoiceCurrency = x.currency

    context = {}
    context['invoice'] = invoice
    context['products'] = products
    context['invoiceTotal'] = "{:.2f}".format(invoiceTotal)
    context['invoiceCurrency'] = invoiceCurrency

    return render(request, 'invoice/invoice-template.html', context)


def viewDocumentInvoice(request, slug):
    #fetch that invoice
    try:
        invoice = Invoice.objects.get(slug=slug)
        pass
    except:
        messages.error(request, 'Something went wrong')
        return redirect('invoices')

    #fetch all the products - related to this invoice
    products = Product.objects.filter(invoice=invoice)

    #Calculate the Invoice Total
    invoiceTotal = 0.0
    if len(products) > 0:
        for x in products:
            y = float(x.quantity) * float(x.price)
            invoiceTotal += y

    context = {}
    context['invoice'] = invoice
    context['products'] = products
    context['invoiceTotal'] = "{:.2f}".format(invoiceTotal)

    #The name of your PDF file
    filename = '{}.pdf'.format(invoice.uniqueId)

    #HTML FIle to be converted to PDF - inside your Django directory
    template = get_template('invoice/pdf-template.html')

    #Render the HTML
    html = template.render(context)

    options = {
        'encoding': 'UTF-8',
        'javascript-delay': '10',  # Optional
        'enable-local-file-access': None,  # To be able to access CSS
        'page-size': 'A4',
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
    }

    #Remember that location to wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

    #Create the file
    file_content = pdfkit.from_string(
        html, False, configuration=config, options=options)

    #Create the HTTP Response
    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename = {}'.format(filename)

    #Return
    return response
