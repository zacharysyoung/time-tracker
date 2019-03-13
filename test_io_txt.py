import datetime
import os
import StringIO
import tempfile
import unittest

from file_util import del_path
import io_txt

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

_dt = datetime.datetime


class TestInvoiceParsing(unittest.TestCase):
    def testParseEntryNote(self):
        def _test_parse(txt):
            parsed_entries = io_txt.parse_entries_from_note(
                StringIO.StringIO(txt), jobs
            )
            parsed_entry = parsed_entries[0]
            self.assertEqual(parsed_entry.hours, 1)
            self.assertEqual(parsed_entry.dt, _dt(2010,1,1))
            self.assertEqual(parsed_entry.message, '1st entry')
            self.assertEqual(parsed_entry.company, 'Company1')
            self.assertEqual(parsed_entry.job, 'job1')

        jobs = CompanyJobs('Company1', {'job1': 'Job One'}, 20)

        # test m/d/yy
        _test_parse('1,1/1/10,1st entry,Company1,Job One')

        # test mm/dd/yy
        _test_parse('1,01/01/10,1st entry,Company1,Job One')

        # test job1 <--> Job One
        _test_parse('1,1/1/10,1st entry,Company1,job1')

        # test quoted comment
        _test_parse('1,1/1/10,"1st entry",Company1,job1')

        # test float
        _test_parse('1.0,1/1/10,1st entry,Company1,job1')

        # test empty row
        _test_parse('1,1/1/10,1st entry,Company1,job1\n,,,,')

        # test non-row
        _test_parse('1,1/1/10,1st entry,Company1,job1\n\n')

        # errors
        self.assertRaisesRegexp(ValueError, 'no data', _test_parse, '')
        self.assertRaisesRegexp(AssertionError,
                                'Expected \d+ field\(s\) in row, got 1',
                                _test_parse,
                                'a'
                                )
        self.assertRaisesRegexp(AssertionError,
                                'Expected \d+ field\(s\) in row, got 2',
                                _test_parse,
                                'a,b'
                                )


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

class TestPathsAndNames(BaseClassIO):
    def testGetReportName(self):
        # Interesting, not sure if I should ever assert what the name
        # is, but it's at least documentation of what the name can
        # look like, if that's even necessary. Hmm, weird.  Maybe the
        # function could be used by the UI to inform the user of the
        # name of a given report, kinda like an export in Harvest
        # resulting in an e-mail to the user with a link to download
        # the PDF.  But, I cannot see the format or appearance of the
        # name having any value... expect to maybe assert the name
        # itself didn't sensitive information in it... so assert its
        # text is a certain, neutral, way... curious, obviously
        invoice_name = io_txt.get_report_name(self.invoice)
        self.assertEqual(invoice_name, '20100101_20100113_Company1')
    
    def testGetReportPath(self):
        report_path = io_txt.get_report_path(self.invoice)
        self.assertEqual(report_path,
                         'io/fs/reports/20100101_20100113_Company1.txt')

    def testGetInvoicePath(self):
        invoice_path = io_txt.get_invoice_path(self.invoice)
        self.assertEqual(invoice_path,
                         'io/fs/invoices/{}.pkl'.format(self.invoice.id) )


class TestInvoiceOpenWrite(BaseClassIO):
    def setUp(self):
        super(TestInvoiceOpenWrite, self).setUp()

        self.invoice_path = io_txt.get_invoice_path(self.invoice)
        if os.path.exists(self.invoice_path):
            del_path(self.invoice_path)

    def tearDown(self):
        super(TestInvoiceOpenWrite, self).tearDown()

        del_path(self.invoice_path)

    def testWriteInvoice(self):            
        io_txt.write_invoice(self.invoice)
        self.assertTrue(os.path.exists(self.invoice_path))

    def testOpenInvoice(self):
        io_txt.write_invoice(self.invoice)
        self.assertTrue(os.path.exists(self.invoice_path))

        gotten_invoice = io_txt.open_invoice(self.invoice_path)
        self.assertEqual(gotten_invoice.id, self.invoice.id)

        for x, y in zip(gotten_invoice.entries, self.invoice.entries):
            self.assertEqual(x.id, y.id)

    def testWriteAlreadyExistingInvoiceError(self):
        io_txt.write_invoice(self.invoice)
        self.assertTrue(os.path.exists(self.invoice_path))

        with self.assertRaises(IOError) as e:
            io_txt.write_invoice(self.invoice)
            self.assertEqual(e.errno, 1024)
            self.assertEqual(e.strerror, 'File already exists: %s' % invoice_p)


class TestReportOpenWrite(BaseClassIO):
    def testWriteReport(self):
        self.invoice.send()

        report_path = io_txt.get_report_path(self.invoice)
        io_txt.write_report(self.invoice)

        with open(report_path, 'r') as f:
            written_txt =  f.read()
            _entries = self.invoice.entries
            self.assertIn(_entries[0].message, written_txt)
            self.assertIn(
                str(TimeEntry.get_hours_total(_entries)), written_txt)

        del_path(report_path)
        
class TestEntryOpenWrite(BaseClassIO):
    def testOpenEntry(self):
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')
        entry_path = io_txt.get_entry_path(entry)
        io_txt.write_entry(entry)
        read_entry = io_txt.open_entry(entry_path)
        self.assertEqual(read_entry.id, entry.id)

        del_path(entry_path)


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


class TestGenInvoice(unittest.TestCase):
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

        del_path(tmpname)

    def testDeletePath(self):
        import os

        import file_util

        # Test invalid deletes after system deletes file on f.close()
        f = tempfile.NamedTemporaryFile(delete=True)
        f.close()
        invalid_path = f.name
        with self.assertRaises(OSError):
            del_path(invalid_path)

        self.assertIsNone(del_path(invalid_path, ignore_error=2))
        
        # Test real delete; system does not delete on close: delete=False
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        self.assertTrue(os.path.exists(f.name))
        del_path(f.name)
        self.assertFalse(os.path.exists(f.name))
