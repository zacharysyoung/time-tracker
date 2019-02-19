import datetime
import tempfile
import StringIO
import unittest

import file_util
import io_txt

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry
from test import BaseClass

_dt = datetime.datetime

class TestIO(BaseClass):
    def testWriteInvoiceForTextingToKen(self):
        import io_txt
        invoice = Invoice(
            [TimeEntry(1, _dt(2010,1,1), None, 'Comp1', 'job1'),
             TimeEntry(2.5, _dt(2010,1,2), None, 'Comp1', 'job1')
             ],
            None,
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Comp1', {'job1': 'Job One'}, None)
        )
        txt = io_txt.print_hours_for_ken(invoice)
        self.assertEqual(
            txt,
            """Comp1
Job One:
Fr 01/01/10: 1
Sa 01/02/10: 2.5
----
total: 3.5

----
total: 3.5

"""
        )

    def testGetInvoiceName(self):
        comp1_entries = TimeEntry.query(self.entries, 'Company1')

        payperiod = (_dt(2010,1,1), _dt(2010,1,13))
        invoice = Invoice(comp1_entries, None, payperiod, self.company1_jobs)

        invoice_name = io_txt.get_invoice_name(invoice)
        self.assertEqual(invoice_name, '20100101_20100113_Company1')

    def testGetFullInvoicePath(self):
        comp1_entries = TimeEntry.query(self.entries, 'Company1')

        payperiod = (_dt(2010,1,1), _dt(2010,1,13))
        invoice = Invoice(comp1_entries, None, payperiod, self.company1_jobs)

        invoice_path = io_txt.get_full_invoice_path(invoice)
        self.assertEqual(invoice_path,
                         'invoices/20100101_20100113_Company1.pkl')

    def testWriteInovice(self):
        from os.path import exists, join
        comp1_entries = TimeEntry.query(self.entries, 'Company1')

        payperiod = (_dt(2010,1,1), _dt(2010,1,13))
        invoice = Invoice(comp1_entries, None, payperiod, self.company1_jobs)
        invoice_path = io_txt.get_full_invoice_path(invoice)

        if exists(invoice_path):
            file_util.del_path(invoice_path)
            
        io_txt.write_invoice(invoice)
        self.assertTrue(exists(invoice_path))

        file_util.del_path(invoice_path)

    def testWriteAlreadyExistingInvoiceError(self):
        from os.path import exists, join
        comp1_entries = TimeEntry.query(self.entries, 'Company1')

        payperiod = (_dt(2010,1,1), _dt(2010,1,13))
        invoice = Invoice(comp1_entries, None, payperiod, self.company1_jobs)

        invoice_p = io_txt.get_full_invoice_path(invoice)

        if exists(invoice_p):
            file_util.del_path(invoice_p)

        io_txt.write_invoice(invoice)
        self.assertTrue(exists(invoice_p))

        with self.assertRaises(IOError) as e:
            io_txt.write_invoice(invoice)
            self.assertEqual(e.errno, 1024)
            self.assertEqual(e.strerror, 'File already exists: %s' % invoice_p)

        file_util.del_path(invoice_p)

    def testWriteInvoiceReport(self):
        import file_util

        comp1_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(comp1_entries, None, (None, None), self.company1_jobs)
        invoice.send()

        # open named-temp file to get its path
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name

        # close...
        tmpfile.close()

        # so other processes can open it
        io_txt.write_invoice_report(invoice, tmppath)

        entries_str = ''
        for entry in comp1_entries:
            entries_str += str(entry) + '\n'

        # Assert file was written and contains some basic values
        with open(tmppath, 'r') as f:
            written_txt =  f.read()
            self.assertIn(comp1_entries[0].message, written_txt)
            self.assertIn(
                str(TimeEntry.get_hours_total(comp1_entries)), written_txt)

        file_util.del_path(tmppath)
        
    def testPrintInvoicedEntries(self):
        entries = [
            TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1'),
            TimeEntry(2, _dt(2010,1,2), '2nd entry', 'Company1', 'job1'),
            TimeEntry(3, _dt(2010,1,3), '3rd entry', 'Company1', 'job1')
            ]
        invoice = Invoice(entries, _dt(2010,1,5,17,0), (None, None), self.company1_jobs)
        invoice.send()

        printed_txt = """| 1 | 01/01/10 | 1st entry | Company1 | job1 |
| 2 | 01/02/10 | 2nd entry | Company1 | job1 |
| 3 | 01/03/10 | 3rd entry | Company1 | job1 |

Total: 6 | Invoiced: {} | Payment due: 2010-01-05 17:00:00 | Gross $: 120
----
""".format(invoice.invoiced_dt)
        
        self.assertEqual(
            io_txt.print_entries(invoice).splitlines(),
            printed_txt.strip().splitlines()
        )

    def testParseEntryNote(self):
        def _test_parse(txt):
            parsed_entries = io_txt.parse_entries_from_note(
                StringIO.StringIO(txt), jobs
            )
            self.assertEqual(parsed_entries[0], entry)

        jobs = CompanyJobs('Company1', {'job1': 'Job One', 'job2': 'Job Two'}, 20)
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')

        # test m/d/yy
        _test_parse('1,1/1/10,1st entry,Company1,Job One')

        # test mm/dd/yy
        _test_parse('1,01/01/10,1st entry,Company1,Job One')

        # test job1 <--> Job One
        _test_parse('1,1/1/10,1st entry,Company1,job1')

        # test quoted comment
        _test_parse('1,1/1/10,"1st entry",Company1,job1')

        # test float
        _test_parse('1.0,1/1/10,"1st entry",Company1,job1')

        # errors
        with self.assertRaises(IndexError):
            _test_parse('')

    def testReadWriteInvoice2(self):
        entries = [
            TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1'),
            TimeEntry(2, _dt(2010,1,2), '2nd entry', 'Company1', 'job1'),
            TimeEntry(3, _dt(2010,1,3), '3rd entry', 'Company1', 'job1')
            ]
        invoice = Invoice(entries, _dt(2010,1,5,17,0), (None, None), self.company1_jobs)
        invoice.send()
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        io_txt.pickle(invoice, tmppath)
        read_invoice = io_txt.unpickle(tmppath)
        self.assertEqual(read_invoice, invoice)
        file_util.del_path(tmppath)

    def testReadWriteEntry(self):
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        io_txt.pickle(entry, tmppath)
        read_entry = io_txt.unpickle(tmppath)
        self.assertEqual(read_entry, entry)


class TestGenInvoiceTask(unittest.TestCase):
    def testTaskWithMockData(self):
        import gen_invoice_task
        company1_jobs_dict = {'job1': 'Job One', 'job2': 'Job Two'}

        note_txt = """1,02/01/19,"Made an entry",Company1,Job One
2,2/2/19,Made another entry,Company1,Job Two"""

        invoice_txt = """Company1
Job One:
Fr 02/01/19: 1
----
total: 1

Job Two:
Sa 02/02/19: 2
----
total: 2

----
total: 3

"""

        invoice = gen_invoice_task.gen_invoice_task(
            ('Company1', _dt(2019,2,18,17,0),
             (_dt(2019,2,3), _dt(2019,2,17)), 20),
            company1_jobs_dict,
            StringIO.StringIO(note_txt)
        )
        self.assertEqual(io_txt.print_hours_for_ken(invoice), invoice_txt)


class TestFileOperations(unittest.TestCase):
    def testAppendFile(self):
        import os

        import file_util

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.close()

        tmpname = tmpfile.name

        with open(tmpname, 'w+b') as f:
            f.write('Old Line\n')

        file_util.append_file_with_data(tmpname, 'New Line\n')

        with open(tmpname, 'r+b') as f:
            self.assertEqual(f.read(), 'Old Line\nNew Line\n')

        file_util.del_path(tmpname)

    def testDeletePath(self):
        import os

        import file_util

        # Test invalid deletes after system deletes file on f.close()
        f = tempfile.NamedTemporaryFile(delete=True)
        f.close()
        invalid_path = f.name
        with self.assertRaises(OSError):
            file_util.del_path(invalid_path)

        self.assertIsNone(file_util.del_path(invalid_path, ignore_error=2))
        
        # Test real delete; system does not delete on close: delete=False
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        self.assertTrue(os.path.exists(f.name))
        file_util.del_path(f.name)
        self.assertFalse(os.path.exists(f.name))
