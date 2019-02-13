import datetime
import unittest
import StringIO

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry


class BaseClass(unittest.TestCase):
    def setUp(self):
        self.entry1 = TimeEntry(1.0, datetime.datetime(2019,2,1),
                                'Made an entry', 'Company1', 'job1')
        self.entry2 = TimeEntry(2.0, datetime.datetime(2019,2,2),
                                'Made another entry', 'Company1', 'job2')
        self.entry3 = TimeEntry(2.5, datetime.datetime(2019,2,3),
                                'Made 3rd entry', 'Company2', 'job2', billable=False)
        self.entry4 = TimeEntry(3, datetime.datetime(2019,2,4),
                                'Made 4th entry', 'Company2', 'job2')
        self.entries = [self.entry1, self.entry2, self.entry3, self.entry4]

        self.now = datetime.datetime.now()
        self.net_30 = self.now + datetime.timedelta(days=30)
        self.net_45 = self.now + datetime.timedelta(days=45)

        self.company1_jobs_dict = {'job1': 'Job One', 'job2': 'Job Two'}
        self.company1_jobs = CompanyJobs('Company1', self.company1_jobs_dict)

class TestTimeEntries(BaseClass):
    def testCreateTimeEntry(self):
        self.assertEqual(self.entry1.hours, 1.0)
        self.assertEqual(self.entry1.dt, datetime.datetime(2019,2,1))
        self.assertEqual(self.entry1.message, 'Made an entry')

    def testSumEntryHours(self):
        self.assertEqual(TimeEntry.get_hours_total([self.entry1, self.entry2]), 3.0)
        self.assertEqual(TimeEntry.get_hours_total([self.entry1, self.entry2, self.entry3]), 5.5)
        self.assertEqual(TimeEntry.get_hours_total(self.entries), 8.5)

    def testGettingUninvoicedEntries(self):
        uninvoiced_entries = TimeEntry.get_uninvoiced([self.entry1, self.entry2, self.entry3])
        self.assertEqual(uninvoiced_entries, [self.entry1, self.entry2])

        self.entry2.invoiced = True
        
        uninvoiced_entries = TimeEntry.get_uninvoiced([self.entry1, self.entry2, self.entry3])
        self.assertEqual(uninvoiced_entries, [self.entry1])

    def testFilterEntries(self):
        filtered_entries = TimeEntry.query(self.entries, company='Company1')
        self.assertEqual(filtered_entries, [self.entry1, self.entry2])

    def testParseEntryNotesSimple(self):
        note_txt = """1,02/01/19,"Made an entry",Company1,Job One
2,2/2/19,Made another entry,Company1,Job Two"""
        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt), self.company1_jobs)
        self.assertEqual(entries, [self.entry1, self.entry2])

    def testParseEntryNotesWithJobMappings(self):
        # Test job1 --> Job One, and Job two --> Job Two
        note_txt = """1,02/01/19,"Made an entry",Company1,job1
2,2/2/19,Made another entry,Company1,Job two"""

        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt), self.company1_jobs)
        self.assertEqual(entries, [self.entry1, self.entry2])


class TestInvoicing(BaseClass):
    def testCreateInvoice(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)
        self.assertEqual(invoice.hours_total, 3)

        filtered_entries = TimeEntry.query(self.entries, 'Company2')
        invoice = Invoice(filtered_entries, self.net_30)
        self.assertEqual(invoice.hours_total, 3)

    def testInvoicePayperiod(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, datetime.datetime(2019,2,18))

        self.assertEqual(invoice.payperiod_start, datetime.datetime(2019,2,4))
        self.assertEqual(invoice.payperiod_end, datetime.datetime(2019,2,17))
        
    def testSendInvoice(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)

        invoice.send()
        self.assertTrue(invoice.sent)
        invoiced_dt = invoice.datetime_invoiced
        for entry in invoice.entries:
            self.assertFalse(entry.can_be_invoiced())
            self.assertEqual(entry.datetime_invoiced, invoiced_dt)
        self.assertEqual(TimeEntry.get_uninvoiced(invoice.entries), [])

    def tesPrintInvoicedEntries(self):
        note_txt = """1,2/1/19,"Made an entry",Company1,job1
3.5,2/3/19,Last entry,Company1,Job One
2,2/2/19,Made another entry,Company1,Job two
"""
        invoiced_entries_txt = """| 1 | 02/01/19 | Made an entry | Company1 | job1 |
| 2 | 02/02/19 | Made another entry | Company1 | job2 |
| 3.5 | 02/03/19 | Last entry | Company1 | job1 |

Total: 6.5 | Invoiced: {} | Payment due: {}
----
"""

        entries = TimeEntry.parse_note(
            StringIO.StringIO(note_txt), self.company1_jobs
        )
        filtered_entries = TimeEntry.query(entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)
        invoice.send()

        invoiced_entries_txt = invoiced_entries_txt.format(
            invoice.datetime_invoiced,
            invoice.scheduled_payment_date
        )
        
        self.assertEqual(invoice.print_entries(), invoiced_entries_txt)

    def testPrintInvoice(self):
        printed_invoice = """Company1
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

        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)
        invoice.send()
        self.assertEqual(
            invoice.print_txt(self.company1_jobs),
            printed_invoice)

    def testWriteInvoice(self):
        import tempfile

        import file_util

        note_txt = """1,2/1/19,"Made an entry",Company1,job1
3.5,2/3/19,Last entry,Company1,Job One
2,2/2/19,Made another entry,Company1,Job two
"""

        printed_invoice = """Company1
Job One:
Fr 02/01/19: 1
Su 02/03/19: 3.5
----
total: 4.5

Job Two:
Sa 02/02/19: 2
----
total: 2

----
total: 6.5

"""


        invoiced_entries_txt = """| 1 | 02/01/19 | Made an entry | Company1 | job1 |
| 2 | 02/02/19 | Made another entry | Company1 | job2 |
| 3.5 | 02/03/19 | Last entry | Company1 | job1 |

Total: 6.5 | Invoiced: {} | Payment due: {}
----
"""
        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt),
                                                         self.company1_jobs)
        invoice = Invoice(entries, self.net_30, self.company1_jobs)
        invoice.send()
        
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        invoice.write_file(tmppath)

        written_txt = printed_invoice + invoiced_entries_txt.format(
            invoice.datetime_invoiced,
            invoice.scheduled_payment_date
        )


        with open(tmppath, 'r') as f:
            self.assertEqual(written_txt, f.read())
        file_util.del_path(tmppath)
        
class TestCompanyJobs(unittest.TestCase):
    def testCompanyJobs(self):
        company1_jobs_dict = {
            'job1': 'Job One',
            'job2': 'Job Two'
        }
        jobs = CompanyJobs('Company1', company1_jobs_dict)

        # Test simple id <--> name
        self.assertEqual(jobs.get_id_by_name('Job One'), 'job1')
        self.assertEqual(jobs.get_name_by_id('job1'), 'Job One')
        self.assertEqual(jobs.get_id_by_name('Job Two'), 'job2')
        self.assertEqual(jobs.get_name_by_id('job2'), 'Job Two')

        # Test normalization
        self.assertEqual(jobs.get_id_by_name('job one'), 'job1')
        self.assertEqual(jobs.get_id_by_name('JoB One'), 'job1')
        self.assertEqual(jobs.get_id_by_name('JOB ONE'), 'job1')

        # id is not normalized
        self.assertIsNone(jobs.get_name_by_id('JOB1'))

        # Check for bogus name
        self.assertIsNone(jobs.get_id_by_name('Job 1'))


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
            'Company1',
            company1_jobs_dict,
            StringIO.StringIO(note_txt)
        )
        self.assertEqual(invoice.print_txt(), invoice_txt)


class TestFileOperations(unittest.TestCase):
    def testAppendFile(self):
        import os
        import tempfile

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
        import tempfile

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
        
