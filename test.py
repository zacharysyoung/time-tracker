import datetime
import unittest
import StringIO

from job_config import JobConfig
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

        config_txt = """[Company1]
job1: Job One
job2: Job Two
"""
        self.config_company1 = JobConfig(StringIO.StringIO(config_txt), 'Company1')

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
        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt), self.config_company1)
        self.assertEqual(entries, [self.entry1, self.entry2])

    def testParseEntryNotesWithJobMappings(self):
        # Test job1 --> Job One, and Job two --> Job Two
        note_txt = """1,02/01/19,"Made an entry",Company1,job1
2,2/2/19,Made another entry,Company1,Job two"""

        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt), self.config_company1)
        self.assertEqual(entries, [self.entry1, self.entry2])


class TestInvoicing(BaseClass):
    def testCreateInvoice(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)
        self.assertEqual(invoice.hours_total, 3)

        filtered_entries = TimeEntry.query(self.entries, 'Company2')
        invoice = Invoice(filtered_entries, self.net_30)
        self.assertEqual(invoice.hours_total, 3)

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
            invoice.print_txt(self.config_company1),
            printed_invoice)

class TestJobConfig(unittest.TestCase):
    def testCreateConfig(self):
        config_txt = """[Company1]
job1: Job One
job2: Job Two
"""

        config = JobConfig(StringIO.StringIO(config_txt), 'Company1')

        # Test simple id <--> name
        self.assertEqual(config.get_id_by_name('Job One'), 'job1')
        self.assertEqual(config.get_name_by_id('job1'), 'Job One')
        self.assertEqual(config.get_id_by_name('Job Two'), 'job2')
        self.assertEqual(config.get_name_by_id('job2'), 'Job Two')

        # Test normalization
        self.assertEqual(config.get_id_by_name('job one'), 'job1')
        self.assertEqual(config.get_id_by_name('JoB One'), 'job1')
        self.assertEqual(config.get_id_by_name('JOB ONE'), 'job1')

        # id is not normalized
        self.assertIsNone(config.get_name_by_id('JOB1'))

        # Check for bogus name
        self.assertIsNone(config.get_id_by_name('Job 1'))


class TestGenInvoiceTask(unittest.TestCase):
    def testTaskWithMockData(self):
        import gen_invoice_task

        config_txt = """[Company1]
job1: Job One
job2: Job Two
"""

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

        gen_invoice_txt = gen_invoice_task.gen_invoice_task(
            'Company1',
            StringIO.StringIO(config_txt),
            StringIO.StringIO(note_txt)
        )
        self.assertEqual(gen_invoice_txt, invoice_txt)

    def testTaskWithRealData(self):
        import gen_invoice_task
        gen_invoice_task.main(print_txt=False)
