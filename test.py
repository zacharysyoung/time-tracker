import datetime
import unittest
import StringIO

from invoice import Invoice
from time_entry import TimeEntry


class BaseClass(unittest.TestCase):
    def setUp(self):
        self.entry1 = TimeEntry(1.0, datetime.datetime(2019,2,1),
                                'Made an entry', 'Company1', 'Job1')
        self.entry2 = TimeEntry(2.0, datetime.datetime(2019,2,2),
                                'Made another entry', 'Company1', 'Job2')
        self.entry3 = TimeEntry(2.5, datetime.datetime(2019,2,3),
                                'Made 3rd entry', 'Company2', 'Job1', billable=False)
        self.entry4 = TimeEntry(3, datetime.datetime(2019,2,4),
                                'Made 4th entry', 'Company2', 'Job2')
        self.entries = [self.entry1, self.entry2, self.entry3, self.entry4]

        self.now = datetime.datetime.now()
        self.net_30 = self.now + datetime.timedelta(days=30)
        self.net_45 = self.now + datetime.timedelta(days=45)

class TestTimeEntries(BaseClass):
    def testCreateTimeEntry(self):
        self.assertEqual(self.entry1.hours, 1.0)
        self.assertEqual(self.entry1.dt, datetime.datetime(2019,2,1))
        self.assertEqual(self.entry1.message, 'Made an entry')

    def testAddEntries(self):
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

    def testParseEntryNotes(self):
        note_txt = """1,02/01/19,"Made an entry",Company1,Job1
2,2/2/19,Made another entry,Company1,Job2"""
        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt))
        self.assertEqual(entries, [self.entry1, self.entry2])

        # Test with extra newlines
        note_txt = """7,1/31/19,shingled;trimmed custom flashing,cch,lasor
6,2/1/19,shingled,cch,lasor
5,2/2/19,shingled,cch,lasor
.5,2/5/19,delivered flashing,cch,LaSorella
3.5,2/5/19,installed floor sheathing in loft; tidied,cch,McElhose


"""
        entries = TimeEntry.parse_note(StringIO.StringIO(note_txt))

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
Job1:
Fr 02/01/19: 1
----
total: 1

Job2:
Sa 02/02/19: 2
----
total: 2

"""

        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, self.net_30)
        invoice.send()
        self.assertEqual(invoice.print_txt(), printed_invoice)

