# Create your views here.
import csv
import uuid
from django.shortcuts import render, redirect
from .models import Account
from django.http import HttpResponse
from django.db.models import Q


def import_accounts(request):
    if request.method == 'POST' and request.FILES['file']:
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        for row in reader:
            if row[0] == 'ID':  # skip the header row
                continue
            # CSV row is in format: [UUID, name, balance]
            account_id = row[0]  # UUID
            account_name = row[1]  # Account name
            account_balance = row[2]  # Account balance

            # Check if the UUID already exists, and skip if it does
            if not Account.objects.filter(id=account_id).exists():
                Account.objects.create(
                    id=account_id,
                    name=account_name,
                    balance=account_balance
                )

        return redirect('account_list')

    return render(request, 'accounts/import.html')


def account_list(request):
    # Get the search query from the navbar
    search_query = request.GET.get('search', '')
    if search_query:
        accounts = Account.objects.filter(
            Q(name__icontains=search_query))  # Search by user name
    else:
        accounts = Account.objects.all()

    return render(request, 'accounts/account_list.html', {'accounts': accounts, 'search_query': search_query})


def account_detail(request, account_id):
    account = Account.objects.get(id=account_id)
    return render(request, 'accounts/account_detail.html', {'account': account})


def transfer_funds(request):
    if request.method == 'POST':
        from_account_id = request.POST['from_account']
        to_account_id = request.POST['to_account']
        amount = float(request.POST['amount'])
        if from_account_id == to_account_id:
            return HttpResponse("You are trying to transfer money to the same account", status=400)

        from_account = Account.objects.get(id=from_account_id)
        to_account = Account.objects.get(id=to_account_id)

        if from_account.withdraw(amount):
            to_account.deposit(amount)
            return redirect('account_list')
        else:
            return HttpResponse("Insufficient funds", status=400)
    accounts = Account.objects.all()
    return render(request, 'accounts/transfer.html', {'accounts': accounts})
