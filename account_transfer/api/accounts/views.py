import csv
from rest_framework.parsers import MultiPartParser, FormParser
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import Account
from .serializers import AccountSerializer
from django.db.models import Q


class AccountListView(APIView):
    def get(self, request):
        search_query = request.GET.get('search', '')
        if search_query:
            accounts = Account.objects.filter(Q(name__icontains=search_query))
        else:
            accounts = Account.objects.all()

        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)


class AccountDetailView(APIView):
    def get(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AccountSerializer(account)
        return Response(serializer.data)


class TransferFundsView(APIView):
    def post(self, request):
        from_account_id = request.data.get('from_account')
        to_account_id = request.data.get('to_account')
        amount = request.data.get('amount')

        try:
            from_account = Account.objects.get(id=from_account_id)
            to_account = Account.objects.get(id=to_account_id)
        except Account.DoesNotExist:
            return Response({"detail": "Account not found."}, status=status.HTTP_404_NOT_FOUND)

        if from_account_id == to_account_id:
            return Response({"detail": "You are trying to transfer money to the same account."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"detail": "Amount should be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure sufficient funds before transferring
        if from_account.withdraw(amount):
            to_account.deposit(amount)
            return Response({"detail": "Transfer successful."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)


class ImportAccountsView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Check if the 'file' key exists in the request data
        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        imported_accounts = 0
        skipped_accounts = 0

        for row in reader:
            if row[0] == 'ID':  # Skip the header row
                continue

            account_id = row[0]  # UUID
            account_name = row[1]  # Account name
            account_balance = row[2]  # Account balance

            # Check if the account already exists, and skip if it does
            if not Account.objects.filter(id=account_id).exists():
                Account.objects.create(
                    id=account_id,
                    name=account_name,
                    balance=account_balance
                )
                imported_accounts += 1
            else:
                skipped_accounts += 1

        return Response(
            {
                "message": f"Import completed. {imported_accounts} accounts imported, {skipped_accounts} accounts skipped.",
                "imported": imported_accounts,
                "skipped": skipped_accounts
            },
            status=status.HTTP_201_CREATED
        )
