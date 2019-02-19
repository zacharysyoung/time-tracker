import datetime
import os
import StringIO
import tempfile
import unittest

import file_util
import io_txt

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

_dt = datetime.datetime


class BaseClassIO(unittest.TestCase):
    def setUp(self):
        super(BaseClassIO, self).setUp()

        self.invoice = Invoice(
            [
                TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1'),
                TimeEntry(2.5, _dt(2010,1,2), '2nd entry', 'Company1', 'job1')
            ],
            _dt(2010,1,14),
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Company1', {'job1': 'Job One'}, 20)
            )


class TestIO(BaseClassIO):
    def testGetInvoiceName(self):
        invoice_name = io_txt.get_invoice_name(self.invoice)
        self.assertEqual(invoice_name, '20100101_20100113_Company1')

    def testGetFullInvoicePath(self):
        invoice_path = io_txt.get_full_invoice_path(self.invoice)
        self.assertEqual(invoice_path,
                         'invoices/20100101_20100113_Company1.pkl')

    def testWriteInovice(self):
        invoice_path = io_txt.get_full_invoice_path(self.invoice)

        if os.path.exists(invoice_path):
            file_util.del_path(invoice_path)
            
        io_txt.write_invoice(self.invoice)
        self.assertTrue(os.path.exists(invoice_path))

        file_util.del_path(invoice_path)

    def testWriteAlreadyExistingInvoiceError(self):
        invoice_p = io_txt.get_full_invoice_path(self.invoice)

        if os.path.exists(invoice_p):
            file_util.del_path(invoice_p)

        io_txt.write_invoice(self.invoice)
        self.assertTrue(os.path.exists(invoice_p))

        with self.assertRaises(IOError) as e:
            io_txt.write_invoice(self.invoice)
            self.assertEqual(e.errno, 1024)
            self.assertEqual(e.strerror, 'File already exists: %s' % invoice_p)

        file_util.del_path(invoice_p)

    def testWriteInvoiceReport(self):
        self.invoice.send()

        # open named-temp file to get its path
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name

        # close...
        tmpfile.close()

        # so other processes can open it
        io_txt.write_invoice_report(self.invoice, tmppath)

        # Assert file was written and contains some basic values
        with open(tmppath, 'r') as f:
            written_txt =  f.read()
            _entries = self.invoice.entries
            self.assertIn(_entries[0].message, written_txt)
            self.assertIn(
                str(TimeEntry.get_hours_total(_entries)), written_txt)

        file_util.del_path(tmppath)
        
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
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        io_txt.pickle(self.invoice, tmppath)
        read_invoice = io_txt.unpickle(tmppath)
        self.assertEqual(read_invoice, self.invoice)
        file_util.del_path(tmppath)

    def testReadWriteEntry(self):
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        io_txt.pickle(entry, tmppath)
        read_entry = io_txt.unpickle(tmppath)
        self.assertEqual(read_entry, entry)



class TestPrinting(BaseClassIO):
    def testPrintInvoicedEntries(self):
        self.invoice.send()

        printed_txt = """| 1 | 01/01/10 | 1st entry | Company1 | job1 |
| 2.5 | 01/02/10 | 2nd entry | Company1 | job1 |

Total: 3.5 | Invoiced: {} | Payment due: 2010-01-14 00:00:00 | Gross $: 70.0
----
""".format(self.invoice.invoiced_dt)
        
        self.assertEqual(
            io_txt.print_entries(self.invoice).splitlines(),
            printed_txt.strip().splitlines()
        )

    def testPrintInvoiceForTextingToKen(self):
        invoice = Invoice(
            [TimeEntry(1, _dt(2010,1,1), None, 'Company1', 'job1'),
             ],
            None,
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Company1', {'job1': 'Job One'}, None)
        )
        txt = io_txt.print_hours_for_ken(self.invoice)
        self.assertEqual(
            txt,
            """Company1
Job One:
Fr 01/01/10: 1
Sa 01/02/10: 2.5
----
total: 3.5

----
total: 3.5

"""
        )

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
