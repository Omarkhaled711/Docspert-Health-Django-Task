from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO
import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import Account
from django.urls import reverse


class AccountListViewTests(APITestCase):

    def setUp(self):
        # Create some accounts to test with, using UUIDs for ids
        self.account1 = Account.objects.create(
            id=uuid.uuid4(), name="Account 1", balance=1000)
        self.account2 = Account.objects.create(
            id=uuid.uuid4(), name="Account 2", balance=1500)
        self.account3 = Account.objects.create(
            id=uuid.uuid4(), name="Account 3", balance=2000)

    def test_get_accounts_without_search(self):
        url = reverse('account_list_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should return all accounts

    def test_get_accounts_with_search(self):
        url = reverse('account_list_api')
        response = self.client.get(url, {'search': 'Account 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should return only Account 1


class AccountDetailViewTests(APITestCase):

    def setUp(self):
        # Create an account with a UUID for testing
        self.account = Account.objects.create(
            id=uuid.uuid4(), name="Account 1", balance=1000)

    def test_get_account_detail(self):

        url = reverse('account_detail_api', kwargs={
                      'account_id': self.account.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # UUID should be serialized as string
        self.assertEqual(response.data['id'], str(self.account.id))
        self.assertEqual(response.data['name'], self.account.name)

    def test_get_account_detail_not_found(self):
        url = reverse('account_detail_api',
                      kwargs={'account_id': str(uuid.uuid4())})  # Random UUID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Not found.')


class TransferFundsViewTests(APITestCase):

    def setUp(self):
        # Create two accounts with UUIDs for transferring funds between them
        self.account1 = Account.objects.create(
            id=uuid.uuid4(), name="Account 1", balance=1000)
        self.account2 = Account.objects.create(
            id=uuid.uuid4(), name="Account 2", balance=500)

    def test_transfer_funds_successful(self):
        url = reverse('transfer_funds_api')
        data = {
            'from_account': str(self.account1.id),
            'to_account': str(self.account2.id),
            'amount': 200
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "Transfer successful.")

    def test_transfer_funds_same_account(self):
        url = reverse('transfer_funds_api')
        data = {
            'from_account': str(self.account1.id),
            'to_account': str(self.account1.id),
            'amount': 200
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'], "You are trying to transfer money to the same account.")

    def test_transfer_funds_insufficient_balance(self):
        url = reverse('transfer_funds_api')
        data = {
            'from_account': str(self.account1.id),
            'to_account': str(self.account2.id),
            'amount': 1200  # More than the balance of account1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Insufficient funds.")

    def test_transfer_funds_account_not_found(self):
        url = reverse('transfer_funds_api')
        data = {
            'from_account': str(uuid.uuid4()),  # Invalid UUID
            'to_account': str(self.account2.id),
            'amount': 200
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Account not found.")


class ImportAccountsViewTests(APITestCase):

    def setUp(self):
        # You can create some accounts if needed, but this test focuses on file upload
        pass

    def test_import_accounts_success(self):
        url = reverse('import_accounts_api')
        csv_data = f"ID,name,balance\n{uuid.uuid4()},Account 1,1000\n{uuid.uuid4()},Account 2,1500"
        csv_file = InMemoryUploadedFile(
            StringIO(csv_data), None, 'accounts.csv', 'text/csv', len(csv_data), None)
        data = {'file': csv_file}

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("imported", response.data)
        # Should import 2 accounts
        self.assertEqual(response.data['imported'], 2)

    def test_import_accounts_no_file(self):
        url = reverse('import_accounts_api')
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "No file provided.")
