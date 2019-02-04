import datetime

from collections import defaultdict

from time_entry import TimeEntry

class Invoice(object):
    def __init__(self, entries, payment_date):
        for i in range(len(entries) - 1, -1, -1):
            if i > 0 and entries[i].company != entries[i - 1].company:
                raise ValueError('Found entries with different companies: %s and %s' % (entries[i].company, entries[i - 1].company))

            if not entries[i].can_be_invoiced():
                del(entries[i])

        self.entries = sorted(entries, key=lambda x: x.dt)
        self.jobs = defaultdict(list)
        for entry in self.entries:
            self.jobs[entry.job].append(entry)

        self.scheduled_payment_date = payment_date
        self.hours_total  = TimeEntry.get_hours_total(self.entries)
        self.company = self.entries[0].company
        self.datetime_invoiced = None
        self.datetime_paid = None
        self.sent = False

    def print_txt(self):
        print_str = self.company + '\n'
        for job in sorted(self.jobs.keys()):
            print_str += job + ':\n'
            for entry in self.jobs[job]:
                dt = entry.dt
                print_str += '%s: %d\n' % (dt.strftime('%a')[0] + ' ' + dt.strftime('%m/%d/%y'), entry.hours)
            print_str += '----\n'
            print_str += 'total: %d\n\n' % TimeEntry.get_hours_total(self.jobs[job])

        return print_str

    def send(self):
        now = datetime.datetime.now()
        for entry in self.entries:
            entry.invoiced = True
            entry.datetime_invoiced = now
        self.datetime_invoiced = now
        self.sent = True
