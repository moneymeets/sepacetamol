from dataclasses import dataclass

from django.shortcuts import render
from openpyxl import load_workbook
from schwifty import IBAN


@dataclass
class Transaction:
    name: str
    iban: str
    bic: str
    amount: float
    purpose: str
    reference: str


def index(request):
    transactions_file = request.FILES["transactions-file"] if request.method == "POST" else None
    transactions = []

    if request.method == "POST":
        workbook = load_workbook(transactions_file)
        worksheet = workbook.active
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            name, iban, amount, purpose, reference = (cell for cell in row)

            iban = IBAN(iban)
            assert iban.validate(), "invalid iban"

            bic = str(iban.bic)

            transactions.append(
                Transaction(
                    name=name,
                    iban=iban.formatted,
                    bic=bic,
                    amount=amount,
                    purpose=purpose,
                    reference=reference,
                ),
            )

    return render(request, "index.html", {
        "source_filename": transactions_file.name if transactions_file is not None else None,
        "transactions": transactions,
        "grand_total": sum(transaction.amount for transaction in transactions),
    })
