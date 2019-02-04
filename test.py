import datetime
import unittest

from time_entry import TimeEntry

class TestTimeEntry(unittest.TestCase):
    def testCreateTimeEntry(self):
        entry = TimeEntry(1.0, datetime.datetime(2019,2,1), 'Made an entry')

        self.assertEqual(entry.hours, 1.0)
        self.assertEqual(entry.dt, datetime.datetime(2019,2,1))
        self.assertEqual(entry.message, 'Made an entry')

    def testAddEntries(self):
        entry1 = TimeEntry(1.0, datetime.datetime(2019,2,1), 'Made an entry')
        entry2 = TimeEntry(2.0, datetime.datetime(2019,2,2), 'Made another entry')
        entry3 = TimeEntry(2.5, datetime.datetime(2019,2,3), 'Made 3rd entry')
        entry4 = TimeEntry(3, datetime.datetime(2019,2,4), 'Made 4th entry')

        self.assertEqual(TimeEntry.add(entry1, entry2), 3.0)
        self.assertEqual(TimeEntry.add(entry1, entry2, entry3), 5.5)
        self.assertEqual(TimeEntry.add(entry1, entry2, entry3, entry4), 8.5)

    def testGettingUninvoicedEntries(self):
        entry1 = TimeEntry(1.0, datetime.datetime(2019,2,1), 'Made an entry', True)
        entry2 = TimeEntry(2.0, datetime.datetime(2019,2,2), 'Made another entry', True)
        entry3 = TimeEntry(2.5, datetime.datetime(2019,2,3), 'Made 3rd entry', False)

        uninvoiced_entries = TimeEntry.get_uninvoiced(entry1, entry2, entry3)
        self.assertEqual(uninvoiced_entries, [entry1, entry2])

        entry2.invoiced = True
        
        uninvoiced_entries = TimeEntry.get_uninvoiced(entry1, entry2, entry3)
        self.assertEqual(uninvoiced_entries, [entry1])
