from django.test import TestCase
from django.urls import reverse
from .models import Account
from decimal import Decimal
from django.http import HttpResponse
import uuid


class AccountModelTest(TestCase):
    def setUp(self):
        """Create a test account."""
        self.account = Account.objects.create(
            name="Test Account", balance=Decimal('1000.000'))

    def test_account_fields(self):
        """Test the fields of the Account model."""
        # Test the type of the `id` field
        self.assertIsInstance(self.account.id, uuid.UUID)

        # Test the type of the `name` field
        self.assertEqual(self.account.name, "Test Account")

        # Test the type and precision of the `balance` field
        self.assertEqual(self.account.balance, Decimal('1000.000'))
        self.assertEqual(self.account._meta.get_field(
            'balance').max_digits, 10)
        self.assertEqual(self.account._meta.get_field(
            'balance').decimal_places, 3)

    def test_deposit(self):
        """Test the deposit method."""
        initial_balance = self.account.balance
        deposit_amount = Decimal('200.500')

        self.account.deposit(deposit_amount)

        # After deposit, the balance should increase
        self.assertEqual(self.account.balance,
                         initial_balance + deposit_amount)

    def test_withdraw(self):
        """Test the withdraw method with sufficient balance."""
        initial_balance = self.account.balance
        withdraw_amount = Decimal('300.000')

        # Withdraw an amount less than the balance
        success = self.account.withdraw(withdraw_amount)

        self.assertTrue(success)
        self.assertEqual(self.account.balance,
                         initial_balance - withdraw_amount)

    def test_withdraw_insufficient_funds(self):
        """Test the withdraw method with insufficient funds."""
        initial_balance = self.account.balance
        withdraw_amount = Decimal('1200.000')  # More than the balance

        # Attempt to withdraw more than the balance
        success = self.account.withdraw(withdraw_amount)

        self.assertFalse(success)
        # Balance should remain unchanged
        self.assertEqual(self.account.balance, initial_balance)

    def test_account_str(self):
        """Test the string representation of the Account model."""
        expected_str = "Test Account has 1000.000$"
        self.assertEqual(str(self.account), expected_str)

    def test_balance_precision(self):
        """Test the precision of the balance field."""
        account = Account.objects.create(
            name="Precision Test", balance=Decimal('123.456'))
        self.assertEqual(account.balance, Decimal('123.456'))


class AccountViewsTest(TestCase):

    def setUp(self):
        """Create test accounts."""
        self.account1 = Account.objects.create(
            name="Account 1", balance=Decimal('1000.000'))
        self.account2 = Account.objects.create(
            name="Account 2", balance=Decimal('500.000'))
        self.account3 = Account.objects.create(
            name="Account 3", balance=Decimal('1500.000'))

    def test_import_accounts(self):
        """Test the import_accounts view with a CSV file."""
        # Simulate file upload
        with open('test_file.csv', 'w') as f:
            f.write("ID,name,balance\n")
            f.write(f"{uuid.uuid4()},New Account,2000.000\n")

        with open('test_file.csv', 'rb') as csv_file:
            response = self.client.post(
                reverse('import_accounts'), {'file': csv_file})

        # After import, the new account should exist in the database
        # 3 existing + 1 new account
        self.assertEqual(Account.objects.count(), 4)

    def test_account_list_without_search(self):
        """Test the account_list view without search query."""
        response = self.client.get(reverse('account_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account 1")
        self.assertContains(response, "Account 2")
        self.assertContains(response, "Account 3")
        # Since it's not searched for
        self.assertNotContains(response, "New Account")

    def test_account_list_with_search(self):
        """Test the account_list view with a search query."""
        response = self.client.get(reverse('account_list'), {
                                   'search': 'Account 1'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account 1")
        self.assertNotContains(response, "Account 2")
        self.assertNotContains(response, "Account 3")

    def test_account_detail(self):
        """Test the account_detail view."""
        response = self.client.get(
            reverse('account_detail', args=[self.account1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account 1")
        self.assertContains(response, "1000.000")

    def test_transfer_funds_valid(self):
        """Test the transfer_funds view with valid transfer."""
        # Ensure balances before transfer
        initial_balance1 = self.account1.balance
        initial_balance2 = self.account2.balance

        response = self.client.post(reverse('transfer_funds'), {
            'from_account': self.account1.id,
            'to_account': self.account2.id,
            'amount': 100.000,
        })

        # Ensure the transfer was successful and balances updated
        self.assertRedirects(response, reverse('account_list'))
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance,
                         initial_balance1 - Decimal('100.000'))
        self.assertEqual(self.account2.balance,
                         initial_balance2 + Decimal('100.000'))

    def test_transfer_funds_insufficient_balance(self):
        """Test the transfer_funds view with insufficient balance."""
        initial_balance1 = self.account1.balance
        initial_balance2 = self.account2.balance

        response = self.client.post(reverse('transfer_funds'), {
            'from_account': self.account1.id,
            'to_account': self.account2.id,
            'amount': 2000.000,
        })

        # Ensure the transfer failed and the balances didn't change
        self.assertEqual(response.status_code, 400)
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, initial_balance1)
        self.assertEqual(self.account2.balance, initial_balance2)

    def test_transfer_funds_same_account(self):
        """Test the transfer_funds view when transferring to the same account."""
        response = self.client.post(reverse('transfer_funds'), {
            'from_account': self.account1.id,
            'to_account': self.account1.id,
            'amount': 100.000,
        })

        # Ensure the transfer fails and returns a 400 Bad Request response (since we are transferring to the same account)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You are trying to transfer money to the same account", response.content.decode())
