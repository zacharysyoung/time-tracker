import datetime
import unittest

from time_entry import TimeEntry


class TestTimeEntry(unittest.TestCase):
    def setUp(self):
        self.entry1 = TimeEntry(1.0, datetime.datetime(2019,2,1), 'Made an entry', 'Company1', 'Job1', True)
        self.entry2 = TimeEntry(2.0, datetime.datetime(2019,2,2), 'Made another entry', 'Company1', 'Job2', True)
        self.entry3 = TimeEntry(2.5, datetime.datetime(2019,2,3), 'Made 3rd entry', 'Company2', 'Job1', False)
        self.entry4 = TimeEntry(3, datetime.datetime(2019,2,4), 'Made 4th entry', 'Company2', 'Job2', True)
        
    def testCreateTimeEntry(self):
        self.assertEqual(self.entry1.hours, 1.0)
        self.assertEqual(self.entry1.dt, datetime.datetime(2019,2,1))
        self.assertEqual(self.entry1.message, 'Made an entry')

    def testAddEntries(self):
        self.assertEqual(TimeEntry.add(self.entry1, self.entry2), 3.0)
        self.assertEqual(TimeEntry.add(self.entry1, self.entry2, self.entry3), 5.5)
        self.assertEqual(TimeEntry.add(self.entry1, self.entry2, self.entry3, self.entry4), 8.5)

    def testGettingUninvoicedEntries(self):
        uninvoiced_entries = TimeEntry.get_uninvoiced(self.entry1, self.entry2, self.entry3)
        self.assertEqual(uninvoiced_entries, [self.entry1, self.entry2])

        self.entry2.invoiced = True
        
        uninvoiced_entries = TimeEntry.get_uninvoiced(self.entry1, self.entry2, self.entry3)
        self.assertEqual(uninvoiced_entries, [self.entry1])

    def testFilterEntries(self):
        entries = [self.entry1, self.entry2, self.entry3]
        filtered_entries = TimeEntry.query(entries, company='Company1')
        self.assertEqual(filtered_entries, [self.entry1, self.entry2])
        
