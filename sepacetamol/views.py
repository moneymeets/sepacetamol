from dataclasses import dataclass

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import smart_str
from openpyxl import load_workbook
from schwifty import IBAN
from sepaxml import SepaTransfer


@dataclass
class Originator:
    name: str
    iban: str


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

            bic = str(iban.bic) if iban.country_code == "DE" else ""

            transactions.append(
                Transaction(
                    name=name,
                    iban=iban.formatted,
                    bic=bic,
                    amount=amount,
                    purpose=purpose,
                    reference=reference if reference is not None else "",
                ),
            )

    name, iban = map(lambda item: request.session.get(item), ("originator-name", "originator-iban"))
    originator = Originator(name=name, iban=IBAN(iban).formatted) if name and iban else None

    source_filename = transactions_file.name if transactions_file is not None else None
    target_filename = source_filename.replace(".xlsx", ".xml") if source_filename is not None else None

    return render(request, "index.html", {
        "source_filename": source_filename,
        "target_filename": target_filename,
        "originator": originator,
        "transactions": transactions,
        "grand_total": sum(transaction.amount for transaction in transactions),
    })


def generate(request):
    if request.method != "POST":
        return HttpResponseBadRequest

    target_filename = request.POST["target-filename"]
    batch_booking = request.POST.get("batch-booking", False)

    originator_name = request.session["originator-name"] = request.POST["originator-name"].strip()
    originator_iban = request.session["originator-iban"] = request.POST["originator-iban"].strip()

    originator_iban = IBAN(originator_iban)
    assert originator_iban.validate(), "invalid iban"
    assert originator_iban.country_code == "DE", "only German originator IBANs are supported"

    sepa = SepaTransfer({
        "name": originator_name,
        "IBAN": str(originator_iban),
        "BIC": str(originator_iban.bic),
        "batch": batch_booking,
        "currency": "EUR",
    }, clean=True)

    for name, iban, bic, amount, purpose, reference in zip(*map(lambda item: request.POST.getlist(item), (
            "transaction-name",
            "transaction-iban",
            "transaction-bic",
            "transaction-amount",
            "transaction-purpose",
            "transaction-reference",
    ))):
        name, bic, purpose, reference = map(lambda item: item.strip(), (name, bic, purpose, reference))
        sepa.add_payment({
            "name": name,
            "IBAN": str(IBAN(iban)),
            "BIC": bic,
            "amount": int(float(amount) * 100),  # cents
            "description": purpose,
            "execution_date": timezone.now().date(),
            "endtoend_id": reference if reference != "" else "NOTPROVIDED",
        })

    response = HttpResponse(content_type="application/xml")
    response["Content-Disposition"] = "attachment; filename=%s" % smart_str(target_filename)
    response.write(sepa.export(validate=True))

    return response
