from datetime import date
from unittest import TestCase

from sepacetamol.views.datev import (
    DatevBooking,
    DatevHeader,
    date_to_datev,
    float_to_german,
    get_datev_booking_from_personio,
    unquote_empty_csv_strings,
)


class TestDatev(TestCase):
    maxDiff = None

    def test_float_to_german(self):
        self.assertEqual("1234567,89", float_to_german(1234567.89))

    def test_csv_unquoting(self):
        self.assertEqual(";;;;;;;;;", unquote_empty_csv_strings(';;;"";"";;;;"";""'))

    def test_date_to_datev(self):
        self.assertEqual("20200101", date_to_datev(date(2020, 1, 1)))

    def test_header_serialization(self):
        output_csv = (
            """
            "EXTF";700;21;"Buchungsstapel";9;;;"RE";"MaxMuster";"";1001;99999;20200101;4;20200301;20200331;"Rechnungen März 2020";"";1;;0;"EUR";;;;;"03";;;"";""
            """  # noqa: E501
        ).strip()

        input_obj = DatevHeader(
            flag="EXTF",
            format_category=21,
            format_name="Buchungsstapel",
            format_version=9,
            reserved_08="RE",
            reserved_09="MaxMuster",
            consultant_number=1001,
            client_numer=99999,
            business_year_start="20200101",
            gl_account_length=4,
            date_from=20200301,
            date_till=20200331,
            designation="Rechnungen März 2020",
            record_type=1,
            currency_code="EUR",
            locking=0,
            gl_chart_of_accounts="03",
        )
        self.assertEqual(unquote_empty_csv_strings(output_csv.strip()), input_obj.model_dump_csv().strip())

    def test_booking_serialization(self):
        output_csv_header = """
            "Umsatz";"Soll-/Haben-Kennzeichen";"WKZ Umsatz";"Kurs";"Basisumsatz";"WKZ Basisumsatz";"Konto";"Gegenkonto (ohne BU-Schlüssel)";"BU-Schlüssel";"Belegdatum";"Belegfeld 1";"Belegfeld 2";"Skonto";"Buchungstext";"Postensperre"
        """  # noqa: E501
        output_csv_line = """
            "123,45";"H";"EUR";;;"";1755;4120;"";"0104";"202304";"";;"Festbezug Gehaelter";
        """

        input_obj = DatevBooking(
            umsatz="123,45",
            soll_haben_kz="H",
            wkz_umsatz="EUR",
            konto=1755,
            gegenkonto=4120,
            belegdatum="0104",
            belegfeld_1="202304",
            buchungstext="Festbezug Gehaelter",
        )

        self.assertEqual(output_csv_header.strip(), input_obj.model_dump_csv_header().strip())
        self.assertEqual(unquote_empty_csv_strings(output_csv_line.strip()), input_obj.model_dump_csv().strip())

    def test_personio_to_datev_booking(self):
        mock_row = (
            "01.06.2023",
            None,
            None,
            123456.78,
            "H",
            None,
            None,
            "4120",
            "1755",
            "202306",
            "Festbezug Gehaelter",
            None,
            None,
        )

        self.assertEqual(
            (
                date(2023, 6, 1),
                DatevBooking(
                    umsatz="123456,78",
                    soll_haben_kz="H",
                    konto=1755,
                    gegenkonto=4120,
                    belegdatum="0106",
                    belegfeld_1="202306",
                    buchungstext="Festbezug Gehaelter",
                ),
            ),
            get_datev_booking_from_personio(mock_row),
        )
